"""
Result, chart, full-data views.
"""

import io
import json
import logging

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render

from ..models import ProcessedData, UploadedFile
from ..utils import (
    apply_filter,
    apply_sort,
    get_categorical_fields,
    get_numeric_fields,
    group_and_calculate_stats,
    make_json_serializable,
    generate_text_insights,
)

logger = logging.getLogger(__name__)


def _can_access(request, file_obj):
    """Return True if the user is allowed to view this file."""
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return True
    return file_obj.user is None or (
        request.user.is_authenticated and file_obj.user == request.user
    )


def result_view(request, file_id):
    """Display analysis results for a processed file."""
    file_obj = get_object_or_404(UploadedFile, id=file_id)

    if not _can_access(request, file_obj):
        return HttpResponse("You don't have permission to view this file.", status=403)

    if not file_obj.processed and not file_obj.error_message:
        messages.info(request, 'File is still being processed. Please refresh the page.')
        return render(request, 'analytics_app/result.html', {'file': file_obj, 'processing': True})

    if file_obj.error_message:
        messages.error(request, f'Error processing file: {file_obj.error_message}')
        return render(request, 'analytics_app/result.html', {'file': file_obj, 'error': True})

    data = ProcessedData.objects.filter(uploaded_file=file_obj).select_related('uploaded_file')

    chart_data, analysis_data = {}, {}
    column_stats_for_insights = {}

    for pd_obj in data:
        col = pd_obj.column_name
        stats = pd_obj.stats
        if isinstance(stats, str):
            try:
                stats = json.loads(stats)
            except Exception:
                stats = {}
        if not isinstance(stats, dict):
            try:
                stats = dict(stats)
            except Exception:
                stats = {}

        analysis_data[col] = {
            'stats': stats,
            'urgent': [],
            'data_type': pd_obj.data_type,
        }
        if stats.get('missing', 0) > 0:
            analysis_data[col]['urgent'].append(f"{stats.get('missing', 0)} missing values detected.")

        column_stats_for_insights[col] = stats

        if 'histogram' in stats:
            sample_vals = stats.get('sample_values')
            if isinstance(sample_vals, (list, tuple)) and sample_vals:
                chart_data[col] = sample_vals
            else:
                hist = stats.get('histogram') or {}
                counts = hist.get('counts') if isinstance(hist, dict) else None
                chart_data[col] = counts if isinstance(counts, list) else []

    try:
        df = pd.read_csv(file_obj.file.path)
        categorical_fields = get_categorical_fields(df)
        data_preview = df.head(50).to_dict(orient='records')
        # Generate insights
        insights = generate_text_insights(df, column_stats_for_insights)
        # Correlation matrix
        numeric_cols = get_numeric_fields(df)
        corr_matrix = None
        corr_labels = []
        if len(numeric_cols) >= 2:
            try:
                corr_df = df[numeric_cols].corr()
                corr_matrix = make_json_serializable(corr_df.values.tolist())
                corr_labels = numeric_cols
            except Exception:
                pass
    except Exception:
        categorical_fields = []
        data_preview = []
        insights = []
        corr_matrix = None
        corr_labels = []

    context = {
        'file': file_obj,
        'data': data,
        'chart_data': chart_data,
        'analysis_data': analysis_data,
        'chart_data_json': json.dumps(make_json_serializable(chart_data)),
        'analysis_data_json': json.dumps(make_json_serializable(analysis_data)),
        'processed_chart_data_json': json.dumps(make_json_serializable(file_obj.processed_chart_data or {})),
        'numeric_fields_json': json.dumps(file_obj.numeric_fields or []),
        'categorical_fields_json': json.dumps(categorical_fields),
        'data_preview': data_preview,
        'file_id': file_id,
        'insights': insights,
        'corr_matrix_json': json.dumps(corr_matrix) if corr_matrix else 'null',
        'corr_labels_json': json.dumps(corr_labels),
        'show_modal': request.GET.get('show_modal', '0'),
    }
    return render(request, 'analytics_app/result.html', context)


def full_data_view(request, file_id):
    """Show up to 1 000 rows of the raw data."""
    file_obj = get_object_or_404(UploadedFile, id=file_id)

    if not _can_access(request, file_obj):
        return HttpResponse("You don't have permission to view this file.", status=403)

    if not file_obj.processed:
        messages.info(request, 'File is still being processed. Please refresh.')
        return render(request, 'analytics_app/full_data.html', {'file': file_obj, 'processing': True})

    if file_obj.error_message:
        messages.error(request, f'Error processing file: {file_obj.error_message}')
        return render(request, 'analytics_app/full_data.html', {'file': file_obj, 'error': True})

    try:
        df = pd.read_csv(file_obj.file.path)
        full_data = df.head(1000).to_dict(orient='records')
        num_rows_displayed = len(full_data)
        total_rows = len(df)
    except Exception as e:
        logger.error("Error reading file for full_data_view: %s", e, exc_info=True)
        full_data, num_rows_displayed, total_rows = [], 0, 0

    return render(request, 'analytics_app/full_data.html', {
        'file': file_obj,
        'full_data': full_data,
        'num_rows_displayed': num_rows_displayed,
        'total_rows': total_rows,
    })


def generate_chart_view(request, file_id):
    """Generate and return a Matplotlib chart image (PNG/SVG/PDF)."""
    logger.info("Chart generation for file_id=%s params=%s", file_id, request.GET)
    file_obj = get_object_or_404(UploadedFile, id=file_id)
    chart_type = request.GET.get('chart_type', 'line')
    x_axis = request.GET.get('x_axis')
    y_axis = request.GET.get('y_axis')

    if not x_axis and chart_type not in ('correlation', 'pie', 'histogram', 'boxplot'):
        return HttpResponse("X-axis must be specified for this chart type.", status=400)

    try:
        df = pd.read_csv(file_obj.file.path)
    except Exception as e:
        return HttpResponse(f"Error reading file: {e}", status=500)

    df = apply_filter(df, request.GET.get('filter_column'),
                      request.GET.get('filter_operator'),
                      request.GET.get('filter_value'))
    df = apply_sort(df, request.GET.get('sort_column'), request.GET.get('sort_order'))

    plt.figure(figsize=(10, 6))

    if chart_type in ('line', 'bar'):
        if not y_axis:
            return HttpResponse("Y-axis must be specified for this chart type.", status=400)
        chart_data = group_and_calculate_stats(df, x_axis, y_axis)
        if not chart_data:
            return HttpResponse("Could not generate data for the selected axes.", status=404)
        x_data = [i['x'] for i in chart_data]
        y_data = [i['y'] for i in chart_data]
        if chart_type == 'line':
            plt.plot(x_data, y_data, marker='o')
        else:
            plt.bar(x_data, y_data)
        plt.xlabel(x_axis); plt.ylabel(y_axis)
        plt.title(f'{chart_type.capitalize()} Chart: {y_axis} vs {x_axis}')

    elif chart_type == 'scatter':
        if not y_axis:
            return HttpResponse("Y-axis must be specified.", status=400)
        if x_axis not in df.columns or y_axis not in df.columns:
            return HttpResponse("Invalid axis specified.", status=400)
        if not (pd.api.types.is_numeric_dtype(df[x_axis]) and pd.api.types.is_numeric_dtype(df[y_axis])):
            return HttpResponse("Both axes must be numeric for a scatter plot.", status=400)
        plt.scatter(df[x_axis], df[y_axis], alpha=0.6)
        plt.xlabel(x_axis); plt.ylabel(y_axis)
        plt.title(f'Scatter: {y_axis} vs {x_axis}')

    elif chart_type == 'histogram':
        if x_axis not in df.columns:
            return HttpResponse("Invalid column specified.", status=400)
        if not pd.api.types.is_numeric_dtype(df[x_axis]):
            return HttpResponse("X-axis must be numeric for a histogram.", status=400)
        plt.hist(df[x_axis].dropna(), bins=20, edgecolor='black')
        plt.xlabel(x_axis); plt.ylabel('Frequency')
        plt.title(f'Histogram of {x_axis}')

    elif chart_type == 'pie':
        if x_axis not in df.columns:
            return HttpResponse("Invalid column specified.", status=400)
        if pd.api.types.is_numeric_dtype(df[x_axis]):
            return HttpResponse("X-axis must be categorical for a pie chart.", status=400)
        counts = df[x_axis].value_counts()
        if len(counts) > 10:
            top10 = counts.nlargest(10)
            other = counts.iloc[10:].sum()
            if other > 0:
                top10['Other'] = other
            counts = top10
        plt.figure(figsize=(8, 8))
        plt.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140)
        plt.title(f'Pie Chart of {x_axis}')

    elif chart_type == 'boxplot':
        if x_axis not in df.columns:
            return HttpResponse("Invalid column specified.", status=400)
        if not pd.api.types.is_numeric_dtype(df[x_axis]):
            return HttpResponse("Boxplot requires a numeric column.", status=400)
        plt.boxplot(df[x_axis].dropna())
        plt.ylabel(x_axis)
        plt.title(f'Box Plot of {x_axis}')

    elif chart_type == 'correlation':
        numeric_cols = get_numeric_fields(df)
        if len(numeric_cols) < 2:
            return HttpResponse("Correlation matrix requires at least two numeric columns.", status=400)
        corr = df[numeric_cols].corr()
        fig, ax = plt.subplots(figsize=(max(6, len(numeric_cols)), max(5, len(numeric_cols))))
        cax = ax.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
        fig.colorbar(cax)
        ax.set_xticks(np.arange(len(numeric_cols)))
        ax.set_yticks(np.arange(len(numeric_cols)))
        ax.set_xticklabels(numeric_cols, rotation=45, ha='right')
        ax.set_yticklabels(numeric_cols)
        for i in range(len(numeric_cols)):
            for j in range(len(numeric_cols)):
                ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha='center', va='center', color='w', fontsize=8)
        ax.set_title("Correlation Matrix")
        fig.tight_layout()
    else:
        return HttpResponse("Invalid chart type specified.", status=400)

    plt.grid(True, linestyle='--', alpha=0.4)
    plt.tight_layout()

    output_format = request.GET.get('format', 'png')
    fmt_map = {'svg': ('image/svg+xml', 'svg'), 'pdf': ('application/pdf', 'pdf')}
    content_type, ext = fmt_map.get(output_format, ('image/png', 'png'))

    buf = io.BytesIO()
    plt.savefig(buf, format=ext, dpi=150)
    plt.close()
    buf.seek(0)

    if request.GET.get('download') == 'true':
        resp = HttpResponse(buf.getvalue(), content_type=content_type)
        resp['Content-Disposition'] = f'attachment; filename="{chart_type}_{file_id}.{ext}"'
        return resp
    return HttpResponse(buf.getvalue(), content_type=content_type)


def missing_values_chart_view(request, file_id):
    """Return a bar chart of missing-value counts per column."""
    file_obj = get_object_or_404(UploadedFile, id=file_id)
    try:
        df = pd.read_csv(file_obj.file.path)
    except Exception as e:
        return HttpResponse(f"Error reading file: {e}", status=500)

    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        return HttpResponse("No missing values found in this dataset.", status=200)

    plt.figure(figsize=(10, max(4, len(missing) * 0.5)))
    missing.plot(kind='barh', color='#e74c3c')
    plt.title('Missing Values per Column')
    plt.xlabel('Number of Missing Values')
    plt.ylabel('Column')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close()
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


def chart_data_api(request, file_id):
    """Return JSON chart data for client-side Chart.js rendering."""
    file_obj = get_object_or_404(UploadedFile, id=file_id)
    chart_type = request.GET.get('chart_type', 'line')
    x_axis = request.GET.get('x_axis')
    y_axis = request.GET.get('y_axis')

    try:
        df = pd.read_csv(file_obj.file.path)
    except Exception as e:
        return JsonResponse({'error': f"Error reading file: {e}"}, status=500)

    try:
        df = df.fillna(0)

        if chart_type in ('line', 'bar'):
            cdata = group_and_calculate_stats(df, x_axis, y_axis)
            return JsonResponse({
                'x': [i['x'] for i in cdata],
                'y': [i['y'] for i in cdata],
                'label': y_axis,
            })

        elif chart_type == 'scatter':
            sample = df.sample(n=min(1000, len(df)))
            points = [{'x': x, 'y': y} for x, y in
                      zip(sample[x_axis].tolist(), sample[y_axis].tolist())]
            return JsonResponse({'data': points, 'x_label': x_axis, 'y_label': y_axis})

        elif chart_type == 'pie':
            counts = df[x_axis].value_counts().head(10)
            return JsonResponse({
                'labels': counts.index.tolist(),
                'data': counts.values.tolist(),
                'label': x_axis,
            })

        elif chart_type == 'histogram':
            counts, bins = np.histogram(
                pd.to_numeric(df[x_axis], errors='coerce').dropna(), bins=20
            )
            labels = [f"{bins[i]:.2f} – {bins[i+1]:.2f}" for i in range(len(counts))]
            return JsonResponse({'labels': labels, 'data': counts.tolist(), 'label': 'Frequency'})

        elif chart_type == 'correlation':
            numeric_cols = get_numeric_fields(df)
            if len(numeric_cols) < 2:
                return JsonResponse({'error': 'Need at least 2 numeric columns.'}, status=400)
            corr = df[numeric_cols].corr()
            return JsonResponse({
                'labels': numeric_cols,
                'matrix': make_json_serializable(corr.values.tolist()),
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Unsupported chart type'}, status=400)
