from celery import shared_task
import logging
import pandas as pd
import numpy as np
import os
from .models import UploadedFile, ProcessedData
from .utils import get_series_data_type, detect_outliers_iqr, group_and_calculate_stats

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_uploaded_file(self, file_id):
    """
    Process an uploaded file: compute column statistics and persist them.

    - Reads CSV/JSON in chunks for memory efficiency on large files.
    - Uses update_or_create to safely handle re-runs.
    - Retries up to 3 times on transient failures (Celery bind=True).
    """
    file_obj = None
    try:
        file_obj = UploadedFile.objects.get(id=file_id)
        file_type = file_obj.file_type
        chunk_size = 10_000

        use_path = (
            hasattr(file_obj.file, 'path')
            and os.path.exists(getattr(file_obj.file, 'path', ''))
        )

        # ── Read full DataFrame first (needed for dtype inference) ─────────
        full_df = _read_full_df(file_obj, file_type, use_path)

        if full_df is None or full_df.empty:
            _mark_done(file_obj, {}, [], 0)
            return

        column_data_types = {col: get_series_data_type(full_df[col]) for col in full_df.columns}

        # ── Chunked accumulation of stats ──────────────────────────────────
        column_stats = {}
        df_iterator = _make_iterator(file_obj, file_type, use_path, full_df, chunk_size)

        for chunk in df_iterator:
            if not hasattr(chunk, 'select_dtypes'):
                continue
            for column in chunk.columns:
                if column_data_types.get(column) != 'numeric':
                    continue

                series = pd.to_numeric(chunk[column], errors='coerce')
                if series.isna().all():
                    continue

                if column not in column_stats:
                    column_stats[column] = {
                        'sum': 0, 'count': 0, 'sum_sq': 0,
                        'min': float('inf'), 'max': float('-inf'),
                        'missing': 0, 'values': [],
                    }

                stats = column_stats[column]
                non_null = series.dropna()
                stats['sum'] += float(non_null.astype(float).sum()) if len(non_null) else 0
                stats['count'] += int(len(non_null))
                stats['sum_sq'] += float((non_null.astype(float) ** 2).sum()) if len(non_null) else 0
                if len(non_null):
                    stats['min'] = min(stats['min'], float(non_null.min()))
                    stats['max'] = max(stats['max'], float(non_null.max()))
                stats['missing'] += int(series.isna().sum())
                if len(stats['values']) < 1000 and len(non_null):
                    sample = non_null.sample(min(len(non_null), 1000 - len(stats['values']))).tolist()
                    stats['values'].extend(sample)

        # ── Persist column-level statistics ───────────────────────────────
        for column, stats in column_stats.items():
            if stats['count'] > 0:
                mean = stats['sum'] / stats['count']
                variance = (stats['sum_sq'] / stats['count']) - (mean ** 2)
                std = float(np.sqrt(max(variance, 0)))
                median = float(np.median(stats['values'])) if stats['values'] else 0.0
                outlier_data = detect_outliers_iqr(pd.Series(stats['values']))

                hist_data = {'bins': [], 'counts': []}
                if stats['values']:
                    hist, bins = np.histogram(stats['values'], bins=10)
                    hist_data = {
                        'bins': [float(b) for b in bins if not np.isnan(b)],
                        'counts': [int(h) for h in hist],
                    }

                sanitized = {
                    'mean':    float(mean) if not np.isnan(mean) else 0.0,
                    'median':  float(median) if not np.isnan(median) else 0.0,
                    'std':     std,
                    'min':     float(stats['min']) if stats['min'] != float('inf') else 0.0,
                    'max':     float(stats['max']) if stats['max'] != float('-inf') else 0.0,
                    'count':   int(stats['count']),
                    'missing': int(stats['missing']),
                    'outliers': outlier_data,
                    'histogram': hist_data,
                    'sample_values': [
                        float(v) for v in (stats.get('values') or [])[:1000]
                        if not np.isnan(v)
                    ],
                }

                ProcessedData.objects.update_or_create(
                    uploaded_file=file_obj,
                    column_name=column,
                    defaults={
                        'value': float(mean),
                        'stats': sanitized,
                        'data_type': column_data_types.get(column, 'unknown'),
                    },
                )
            else:
                ProcessedData.objects.update_or_create(
                    uploaded_file=file_obj,
                    column_name=column,
                    defaults={
                        'value': 0.0,
                        'stats': {'missing': int(full_df[column].isna().sum())},
                        'data_type': column_data_types.get(column, 'unknown'),
                    },
                )

        # ── Pre-compute chart data for numeric pairs ───────────────────────
        numeric_fields = list(column_stats.keys())[:10]
        estimated_rows = sum(
            s['count'] + s['missing'] for s in column_stats.values()
        ) if column_stats else 0
        MAX_ROWS = 50_000

        processed_chart_data = {}
        if column_stats and estimated_rows <= MAX_ROWS:
            try:
                df = _read_full_df(file_obj, file_type, use_path)
                if df is not None and not df.empty and numeric_fields:
                    for x_field in numeric_fields:
                        for y_field in numeric_fields:
                            if x_field != y_field:
                                key = f"{x_field}_{y_field}"
                                processed_chart_data[key] = group_and_calculate_stats(df, x_field, y_field)
            except Exception as e:
                logger.warning("Failed to compute processed_chart_data: %s", e)

        if estimated_rows > MAX_ROWS:
            logger.info("Skipping chart data for large file (%d rows).", estimated_rows)
            processed_chart_data = {}

        _mark_done(file_obj, processed_chart_data, numeric_fields, full_df.shape[0])

    except Exception as exc:
        logger.exception("Error processing uploaded file %s", file_id)
        if file_obj is not None:
            try:
                file_obj.error_message = str(exc)
                file_obj.save()
            except Exception:
                pass
        raise self.retry(exc=exc)


# ── Private helpers ────────────────────────────────────────────────────────

def _read_full_df(file_obj, file_type=None, use_path=None):
    """Read the entire file into a DataFrame."""
    if file_type is None:
        file_type = file_obj.file_type
    if use_path is None:
        use_path = (
            hasattr(file_obj.file, 'path')
            and os.path.exists(getattr(file_obj.file, 'path', ''))
        )

    if file_type == 'csv':
        if use_path:
            return pd.read_csv(file_obj.file.path)
        file_obj.file.open('rb')
        file_obj.file.seek(0)
        return pd.read_csv(file_obj.file)

    if file_type == 'json':
        if use_path:
            try:
                df = pd.read_json(file_obj.file.path, lines=True)
            except ValueError:
                df = pd.read_json(file_obj.file.path)
            return df.to_frame().T if isinstance(df, pd.Series) else df
        file_obj.file.open('rb')
        file_obj.file.seek(0)
        try:
            df = pd.read_json(file_obj.file, lines=True)
        except ValueError:
            file_obj.file.seek(0)
            df = pd.read_json(file_obj.file)
        return df.to_frame().T if isinstance(df, pd.Series) else df

    raise ValueError(f"Unsupported file type: {file_type}")


def _make_iterator(file_obj, file_type, use_path, full_df, chunk_size):
    """Return a chunk iterator (or single-element list for JSON)."""
    if file_type == 'csv':
        if use_path:
            return pd.read_csv(file_obj.file.path, chunksize=chunk_size)
        file_obj.file.open('rb')
        file_obj.file.seek(0)
        return pd.read_csv(file_obj.file, chunksize=chunk_size)
    # JSON: already fully loaded, treat as single chunk
    return [full_df]


def _mark_done(file_obj, chart_data, numeric_fields, num_rows):
    file_obj.processed_chart_data = chart_data
    file_obj.numeric_fields = numeric_fields
    file_obj.num_rows = num_rows
    file_obj.processed = True
    file_obj.save()