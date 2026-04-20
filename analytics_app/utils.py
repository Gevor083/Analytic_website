"""
Shared utility functions for the analytics app.

Centralised here to avoid duplication between views.py and tasks.py.
"""

import datetime
import json
import logging
import uuid
import os

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# File upload helpers
# ---------------------------------------------------------------------------

def get_upload_path(instance, filename):
    """
    Generate a unique upload path per user to avoid filename collisions.
    Files are stored under  uploads/<user_id|anon>/<uuid>.<ext>
    """
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'bin'
    uid = uuid.uuid4().hex
    user_dir = str(instance.user_id) if instance.user_id else 'anon'
    return os.path.join(user_dir, f"{uid}.{ext}")


# ---------------------------------------------------------------------------
# JSON serialisation helpers
# ---------------------------------------------------------------------------

def make_json_serializable(o):
    """Recursively convert a value to a JSON-safe Python primitive."""
    if isinstance(o, float) and (np.isnan(o) or o == float('inf') or o == float('-inf')):
        return None
    if o is None:
        return None
    if isinstance(o, (str, bool, int, float)):
        return o
    if isinstance(o, (np.integer, np.int64, np.int32)):
        return int(o)
    if isinstance(o, (np.floating, np.float64, np.float32)):
        val = float(o)
        return None if (np.isnan(val) or val in (float('inf'), float('-inf'))) else val
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, (datetime.datetime, datetime.date)):
        return o.isoformat()
    if isinstance(o, (list, tuple)):
        return [make_json_serializable(x) for x in o]
    if isinstance(o, np.ndarray):
        return [make_json_serializable(x) for x in o.tolist()]
    if isinstance(o, dict):
        return {str(k): make_json_serializable(v) for k, v in o.items()}
    try:
        import pandas as _pd
        if isinstance(o, (_pd.Timestamp, _pd.Timedelta)):
            return str(o)
        if isinstance(o, _pd.Series):
            return [make_json_serializable(x) for x in o.tolist()]
        if isinstance(o, _pd.DataFrame):
            return [make_json_serializable(x) for x in o.values.tolist()]
    except Exception:
        pass
    try:
        return json.dumps(o, default=str)
    except Exception:
        return str(o)


# ---------------------------------------------------------------------------
# Data analysis helpers
# ---------------------------------------------------------------------------

def get_numeric_fields(df):
    """Return column names that can be treated as numeric."""
    numeric_fields = []
    for col in df.columns:
        try:
            numeric_series = pd.to_numeric(df[col], errors='coerce')
            if numeric_series.notna().sum() > 0:
                numeric_fields.append(col)
        except Exception:
            continue
    return numeric_fields


def get_categorical_fields(df, max_unique=20):
    """Return column names suitable for categorical/pie-chart analysis."""
    return [
        col for col in df.columns
        if df[col].dtype == 'object' or df[col].nunique() <= max_unique
    ]


def detect_outliers_iqr(series):
    """
    Detect outliers in a numeric Series using the IQR method.
    Returns {'count': int, 'values': list}.
    """
    if not pd.api.types.is_numeric_dtype(series):
        return {'count': 0, 'values': []}

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    outliers = series[(series < lower) | (series > upper)]
    return {'count': len(outliers), 'values': outliers.tolist()[:20]}


def group_and_calculate_stats(df, x_field, y_field):
    """
    Group *df* by *x_field* and compute summary statistics for *y_field*.
    Returns a list of dicts with keys: x, y (mean), stats.
    """
    if x_field not in df.columns or y_field not in df.columns:
        return []

    grouped = (
        df.groupby(x_field)[y_field]
        .agg(['mean', 'median', 'min', 'max', 'std', 'count'])
        .reset_index()
    )

    try:
        grouped = grouped.sort_values(by=x_field)
    except Exception:
        pass

    def _san(val):
        if pd.isna(val) or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
            return None
        return val

    result = []
    for _, row in grouped.iterrows():
        result.append({
            'x': _san(row[x_field]),
            'y': _san(row['mean']),
            'stats': {
                'mean':   _san(row['mean']),
                'median': _san(row['median']),
                'min':    _san(row['min']),
                'max':    _san(row['max']),
                'std':    _san(row['std']),
                'count':  _san(row['count']),
            },
        })
    return result


def apply_filter(df, filter_column, filter_operator, filter_value):
    """Apply a column/operator/value filter to *df*."""
    if not filter_column or not filter_operator or not filter_value:
        return df
    if filter_column not in df.columns:
        return df

    try:
        if pd.api.types.is_numeric_dtype(df[filter_column]):
            filter_value = pd.to_numeric(filter_value)
        elif pd.api.types.is_datetime64_any_dtype(df[filter_column]):
            filter_value = pd.to_datetime(filter_value)
    except ValueError:
        pass

    ops = {
        'eq': lambda s, v: s == v,
        'ne': lambda s, v: s != v,
        'gt': lambda s, v: s > v,
        'lt': lambda s, v: s < v,
        'ge': lambda s, v: s >= v,
        'le': lambda s, v: s <= v,
    }
    if filter_operator in ops:
        df = df[ops[filter_operator](df[filter_column], filter_value)]
    return df


def apply_sort(df, sort_column, sort_order):
    """Sort *df* by *sort_column* in *sort_order* ('asc'/'desc')."""
    if not sort_column or sort_column not in df.columns:
        return df
    return df.sort_values(by=sort_column, ascending=(sort_order == 'asc'))


def get_series_data_type(series):
    """Classify a pandas Series as 'numeric', 'datetime', or 'categorical'."""
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


def generate_text_insights(df, column_stats):
    """
    Generate human-readable insight strings from computed column statistics.
    Returns a list of insight strings.
    """
    insights = []
    total_rows = len(df)

    for col, stats in column_stats.items():
        missing = stats.get('missing', 0)
        if missing > 0 and total_rows > 0:
            pct = missing / total_rows * 100
            insights.append(
                f"⚠️ Column '{col}' has {missing} missing values ({pct:.1f}%). "
                f"Consider imputation or dropping the column."
            )

        outliers = stats.get('outliers', {})
        outlier_count = outliers.get('count', 0) if isinstance(outliers, dict) else 0
        if outlier_count > 0:
            insights.append(
                f"📊 Column '{col}' contains {outlier_count} outlier(s) detected via IQR. "
                f"Review or winsorise before modelling."
            )

    # Correlation insights
    numeric_cols = get_numeric_fields(df)
    if len(numeric_cols) >= 2:
        try:
            corr = df[numeric_cols].corr()
            for i, col_a in enumerate(numeric_cols):
                for col_b in numeric_cols[i + 1:]:
                    r = corr.loc[col_a, col_b]
                    if pd.isna(r):
                        continue
                    if abs(r) >= 0.8:
                        direction = "positively" if r > 0 else "negatively"
                        insights.append(
                            f"🔗 '{col_a}' and '{col_b}' are strongly {direction} correlated "
                            f"(r = {r:.2f})."
                        )
        except Exception:
            pass

    if not insights:
        insights.append("✅ No major data quality issues detected.")

    return insights
