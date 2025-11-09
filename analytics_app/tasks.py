from celery import shared_task
import logging
import pandas as pd
import numpy as np
import os
from .models import UploadedFile, ProcessedData

logger = logging.getLogger(__name__)


def group_and_calculate_stats(df, x_field, y_field):
    """
    Group data by x_field and calculate statistics for y_field.
    Returns a list of dicts with x, y (mean), and stats.
    """
    if x_field not in df.columns or y_field not in df.columns:
        return []

    # Group by x_field and calculate stats for y_field
    grouped = df.groupby(x_field)[y_field].agg(['mean', 'median', 'min', 'max', 'std', 'count']).reset_index()

    # Sort by x_field (assuming it's numeric or sortable)
    try:
        grouped = grouped.sort_values(by=x_field)
    except Exception:
        pass  # If not sortable, keep as is

    result = []
    for _, row in grouped.iterrows():
        x_val = row[x_field]
        mean_val = row['mean']
        median_val = row['median']
        min_val = row['min']
        max_val = row['max']
        std_val = row['std'] if not pd.isna(row['std']) else 0.0  # Handle NaN std
        count_val = row['count']

        # Sanitize values to handle NaN and ensure JSON serializable
        def sanitize_val(val):
            if pd.isna(val) or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
                return None
            return val

        result.append({
            'x': sanitize_val(x_val),
            'y': sanitize_val(mean_val),  # For line chart, y is the mean
            'stats': {
                'mean': sanitize_val(mean_val),
                'median': sanitize_val(median_val),
                'min': sanitize_val(min_val),
                'max': sanitize_val(max_val),
                'std': sanitize_val(std_val),
                'count': sanitize_val(count_val)
            }
        })

    return result


def get_series_data_type(series):
    """
    Determine the data type of a pandas Series.
    """
    try:
        pd.to_numeric(series, errors='raise')
        return 'numeric'
    except (ValueError, TypeError):
        pass

    try:
        pd.to_datetime(series, errors='raise')
        return 'datetime'
    except (ValueError, TypeError):
        pass

    return 'categorical'


def detect_outliers_iqr(series):
    """
    Detect outliers in a numeric series using the IQR method.
    """
    if not pd.api.types.is_numeric_dtype(series):
        return {'count': 0, 'values': []}

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outliers = series[(series < lower_bound) | (series > upper_bound)]
    return {
        'count': len(outliers),
        'values': outliers.tolist()[:20]  # Limit to 20 sample outlier values
    }


@shared_task
def process_uploaded_file(file_id):
    """Process an uploaded file in chunks, compute basic numeric statistics and save them.

    This function is defensive about file availability (storage backends without .path)
    and about pandas read failures. It also uses update_or_create to avoid unique
    constraint failures if the task is re-run.
    """
    file_obj = None
    try:
        file_obj = UploadedFile.objects.get(id=file_id)
        file_type = file_obj.file_type

        # Read file in chunks for large files
        chunk_size = 10000  # Adjust based on memory constraints

        # Prefer filesystem path when available, otherwise use file-like object
        use_path = hasattr(file_obj.file, 'path') and os.path.exists(getattr(file_obj.file, 'path', ''))

        # Read the entire file first to infer data types and get all columns
        full_df = None
        if file_type == 'csv':
            if use_path:
                full_df = pd.read_csv(file_obj.file.path)
            else:
                file_obj.file.open('rb')
                file_obj.file.seek(0)
                full_df = pd.read_csv(file_obj.file)
        elif file_type == 'json':
            if use_path:
                full_df = pd.read_json(file_obj.file.path, lines=True)
            else:
                file_obj.file.open('rb')
                file_obj.file.seek(0)
                full_df = pd.read_json(file_obj.file, lines=True)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        if full_df is None or full_df.empty:
            raise ValueError("Could not read file or file is empty.")

        column_data_types = {col: get_series_data_type(full_df[col]) for col in full_df.columns}

        # Reset file pointer for chunked reading if not using path
        if not use_path:
            file_obj.file.seek(0)

        if file_type == 'csv':
            if use_path:
                df_iterator = pd.read_csv(file_obj.file.path, chunksize=chunk_size)
            else:
                df_iterator = pd.read_csv(file_obj.file, chunksize=chunk_size)
        elif file_type == 'json':
            try:
                if use_path:
                    df_iterator = pd.read_json(file_obj.file.path, lines=True, chunksize=chunk_size)
                else:
                    df_iterator = pd.read_json(file_obj.file, lines=True, chunksize=chunk_size)
            except TypeError:
                df_iterator = [full_df] # Fallback to full_df if chunking not supported
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Initialize accumulators
        column_stats = {}

        # Process chunks
        for chunk_num, chunk in enumerate(df_iterator):
            # Ensure chunk is a DataFrame (pandas may return list-like fallback)
            if not hasattr(chunk, 'select_dtypes'):
                continue
            for column in chunk.columns:
                # Only process numeric columns for stats calculation
                if column_data_types.get(column) != 'numeric':
                    continue

                series = pd.to_numeric(chunk[column], errors='coerce')
                if series.isna().all():
                    continue

                if column not in column_stats:
                    column_stats[column] = {
                        'sum': 0,
                        'count': 0,
                        'sum_sq': 0,  # For calculating std dev
                        'min': float('inf'),
                        'max': float('-inf'),
                        'missing': 0,
                        'values': []  # Keep limited sample for histogram
                    }

                stats = column_stats[column]
                non_null = series.dropna()

                # Use numpy-safe operations
                try:
                    stats['sum'] += non_null.sum()
                except Exception:
                    stats['sum'] += float(non_null.astype(float).sum()) if len(non_null) > 0 else 0
                stats['count'] += int(len(non_null))
                try:
                    stats['sum_sq'] += (non_null ** 2).sum()
                except Exception:
                    stats['sum_sq'] += float((non_null.astype(float) ** 2).sum()) if len(non_null) > 0 else 0

                try:
                    stats['min'] = min(stats['min'], non_null.min() if len(non_null) > 0 else stats['min'])
                    stats['max'] = max(stats['max'], non_null.max() if len(non_null) > 0 else stats['max'])
                except Exception:
                    pass

                stats['missing'] += int(series.isna().sum())

                # Keep a sample of values for histogram (limit to 1000 values)
                if len(stats['values']) < 1000 and len(non_null) > 0:
                    try:
                        sample = non_null.sample(min(len(non_null), 1000 - len(stats['values']))).tolist()
                        stats['values'].extend(sample)
                    except Exception:
                        stats['values'].extend(non_null.tolist()[: max(0, 1000 - len(stats['values']))])

        # Calculate final statistics and save
        for column, stats in column_stats.items():
            if stats['count'] > 0:
                mean = stats['sum'] / stats['count']
                variance = (stats['sum_sq'] / stats['count']) - (mean ** 2)
                std = np.sqrt(variance) if variance > 0 else 0

                # Calculate median from sample values
                median = np.median(stats['values']) if len(stats['values']) > 0 else 0

                # Detect outliers from sample values
                outlier_data = detect_outliers_iqr(pd.Series(stats['values']))

                # Calculate histogram only if we have sample values
                if len(stats['values']) > 0:
                    hist, bins = np.histogram(stats['values'], bins=10)
                    hist_data = {
                        'bins': bins.tolist(),
                        'counts': hist.tolist()
                    }
                else:
                    hist_data = {'bins': [], 'counts': []}

                # Sanitize numeric types to native Python types before saving
                sanitized_stats = {
                    'mean': float(mean) if not np.isnan(mean) else 0.0,
                    'median': float(median) if not np.isnan(median) else 0.0,
                    'std': float(std) if not np.isnan(std) else 0.0,
                    'min': float(stats['min']) if not np.isnan(stats['min']) else 0.0,
                    'max': float(stats['max']) if not np.isnan(stats['max']) else 0.0,
                    'count': int(stats['count']),
                    'missing': int(stats['missing']),
                    'outliers': outlier_data,
                    'histogram': {
                        'bins': [float(b) for b in hist_data.get('bins', []) if not np.isnan(b)],
                        'counts': [int(h) for h in hist_data.get('counts', [])]
                    },
                    # Include a limited sample of numeric values for line/box charts
                    'sample_values': [float(v) for v in (stats.get('values') or [])[:1000] if not np.isnan(v)]
                }

                # Use update_or_create to avoid unique_together integrity errors on reruns
                ProcessedData.objects.update_or_create(
                    uploaded_file=file_obj,
                    column_name=column,
                    defaults={
                        'value': float(mean),
                        'stats': sanitized_stats,
                        'data_type': column_data_types.get(column, 'unknown'),
                    }
                )
            else:
                # For non-numeric columns, just save the data type and missing count
                ProcessedData.objects.update_or_create(
                    uploaded_file=file_obj,
                    column_name=column,
                    defaults={
                        'value': 0.0, # Default value for non-numeric
                        'stats': {'missing': int(full_df[column].isna().sum())},
                        'data_type': column_data_types.get(column, 'unknown'),
                    }
                )

        # Compute processed_chart_data for all numeric pairs
        processed_chart_data = {}
        numeric_fields = list(column_stats.keys())[:10]  # Use the columns we already processed, limit to 10

        if column_stats:
            # For large files, skip chart data computation to avoid memory and DB issues
            # Estimate file size based on chunk processing
            estimated_rows = sum(stats['count'] + stats['missing'] for stats in column_stats.values())
            max_rows_for_chart = 50000  # Limit chart computation to files with <= 50k rows

            if estimated_rows <= max_rows_for_chart:
                try:
                    if file_type == 'csv':
                        if use_path:
                            df = pd.read_csv(file_obj.file.path)
                        else:
                            file_obj.file.open('rb')
                            file_obj.file.seek(0)
                            df = pd.read_csv(file_obj.file)
                    elif file_type == 'json':
                        if use_path:
                            df = pd.read_json(file_obj.file.path, lines=True)
                        else:
                            file_obj.file.open('rb')
                            file_obj.file.seek(0)
                            df = pd.read_json(file_obj.file, lines=True)
                    else:
                        df = pd.DataFrame()

                    if not df.empty and numeric_fields:
                        # Pre-compute grouped stats for numeric pairs (limited to prevent exponential growth)
                        for x_field in numeric_fields:
                            for y_field in numeric_fields:
                                if x_field != y_field:
                                    key = f"{x_field}_{y_field}"
                                    processed_chart_data[key] = group_and_calculate_stats(df, x_field, y_field)

                except Exception as e:
                    logger.warning(f"Failed to compute processed_chart_data: {e}")
            else:
                logger.info(f"Skipping chart data computation for large file ({estimated_rows} rows)")

        # For large files, don't save processed_chart_data to avoid DB memory errors
        if estimated_rows > max_rows_for_chart:
            processed_chart_data = {}

        file_obj.processed_chart_data = processed_chart_data
        file_obj.numeric_fields = numeric_fields
        file_obj.num_rows = full_df.shape[0] # Save the number of rows
        file_obj.processed = True
        file_obj.save()

    except Exception as e:
        logger.exception("Error processing uploaded file %s", file_id)
        # Only set error_message if file_obj was successfully retrieved/created
        if file_obj is not None:
            try:
                file_obj.error_message = str(e)
                file_obj.save()
            except Exception:
                # If saving the error message fails, just continue to raise
                pass
        # Re-raise so Celery/other callers can see failure if needed
        raise