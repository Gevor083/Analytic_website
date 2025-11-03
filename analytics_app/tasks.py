from celery import shared_task
import logging
import pandas as pd
import numpy as np
import os
from .models import UploadedFile, ProcessedData

logger = logging.getLogger(__name__)


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

        if file_type == 'csv':
            if use_path:
                df_iterator = pd.read_csv(file_obj.file.path, chunksize=chunk_size)
            else:
                # file_obj.file is a file-like object; ensure we're at start
                file_obj.file.open('rb')
                file_obj.file.seek(0)
                df_iterator = pd.read_csv(file_obj.file, chunksize=chunk_size)
        elif file_type == 'json':
            # Some pandas versions don't accept chunksize for read_json unless lines=True
            try:
                if use_path:
                    df_iterator = pd.read_json(file_obj.file.path, lines=True, chunksize=chunk_size)
                else:
                    file_obj.file.open('rb')
                    file_obj.file.seek(0)
                    df_iterator = pd.read_json(file_obj.file, lines=True, chunksize=chunk_size)
            except TypeError:
                # Fallback: read whole file into DataFrame if chunksize unsupported
                if use_path:
                    df = pd.read_json(file_obj.file.path, lines=True)
                else:
                    file_obj.file.open('rb')
                    file_obj.file.seek(0)
                    df = pd.read_json(file_obj.file, lines=True)
                df_iterator = [df]
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Initialize accumulators
        column_stats = {}

        # Process chunks
        for chunk_num, chunk in enumerate(df_iterator):
            # Ensure chunk is a DataFrame (pandas may return list-like fallback)
            if not hasattr(chunk, 'select_dtypes'):
                continue
            for column in chunk.select_dtypes(include=[np.number]).columns:
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
                series = chunk[column]
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
                    'mean': float(mean),
                    'median': float(median),
                    'std': float(std),
                    'min': float(stats['min']),
                    'max': float(stats['max']),
                    'count': int(stats['count']),
                    'missing': int(stats['missing']),
                    'histogram': {
                        'bins': [float(b) for b in hist_data.get('bins', [])],
                        'counts': [int(h) for h in hist_data.get('counts', [])]
                    },
                    # Include a limited sample of numeric values for line/box charts
                    'sample_values': [float(v) for v in (stats.get('values') or [])[:1000]]
                }

                # Use update_or_create to avoid unique_together integrity errors on reruns
                ProcessedData.objects.update_or_create(
                    uploaded_file=file_obj,
                    column_name=column,
                    defaults={
                        'value': float(mean),
                        'stats': sanitized_stats,
                    }
                )

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