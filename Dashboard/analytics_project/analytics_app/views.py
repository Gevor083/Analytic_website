from django.shortcuts import render, redirect, get_object_or_404
from .models import UploadedFile, ProcessedData
import pandas as pd
import json
from django.contrib import messages
import os
from django.conf import settings


# Գլխավոր էջ
def home_view(request):
    return render(request, 'analytics_app/index.html')


# Upload էջ
def upload_view(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            return render(request, 'analytics_app/upload.html', {
                'error': 'No file was uploaded.'
            })

        filename = uploaded_file.name.lower()
        if filename.endswith('.csv'):
            file_type = 'csv'
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            file_type = 'excel'
        elif filename.endswith('.json'):
            file_type = 'json'
        elif filename.endswith('.sql'):
            file_type = 'sql'
        else:
            return render(request, 'analytics_app/upload.html', {
                'error': 'Unsupported file type. Please upload CSV, Excel, JSON, or SQL files.'
            })

        if uploaded_file.size == 0:
            return render(request, 'analytics_app/upload.html', {
                'error': 'The uploaded file is empty.'
            })

        try:
            obj = UploadedFile.objects.create(file=uploaded_file, file_type=file_type)

            # Read file according to type
            try:
                if file_type == 'csv':
                    df = pd.read_csv(uploaded_file)
                elif file_type == 'excel':
                    df = pd.read_excel(uploaded_file)
                elif file_type == 'json':
                    df = pd.read_json(uploaded_file)
                elif file_type == 'sql':
                    return render(request, 'analytics_app/upload.html', {
                        'error': 'SQL file import is not supported yet.'
                    })
            except Exception as e:
                return render(request, 'analytics_app/upload.html', {
                    'error': f'Error processing file: {str(e)}'
                })

            if df.empty:
                return render(request, 'analytics_app/upload.html', {
                    'error': 'The uploaded file contains no data.'
                })

            # Strictly select only float and int columns
            numeric_columns = []
            for col in df.columns:
                if pd.api.types.is_float_dtype(df[col]) or pd.api.types.is_integer_dtype(df[col]):
                    numeric_columns.append(col)
            chart_data = {}
            analysis_data = {}
            for col in numeric_columns:
                # Defensive: skip columns that are not Series of float or int
                if not (pd.api.types.is_float_dtype(df[col]) or pd.api.types.is_integer_dtype(df[col])):
                    continue
                col_data = df[col].dropna()
                stats = {
                    'mean': float(col_data.mean()) if not col_data.empty else None,
                    'median': float(col_data.median()) if not col_data.empty else None,
                    'min': float(col_data.min()) if not col_data.empty else None,
                    'max': float(col_data.max()) if not col_data.empty else None,
                    'std': float(col_data.std()) if not col_data.empty else None,
                    'missing': int(df[col].isna().sum()),
                    'count': int(col_data.count()),
                }
                # Outlier detection (IQR method)
                q1 = col_data.quantile(0.25)
                q3 = col_data.quantile(0.75)
                iqr = q3 - q1
                outliers = col_data[(col_data < q1 - 1.5 * iqr) | (col_data > q3 + 1.5 * iqr)]
                stats['outliers'] = outliers.tolist()
                stats['outlier_count'] = len(outliers)
                # Histogram data
                hist_counts, hist_bins = pd.cut(col_data, bins=10, retbins=True, labels=False, include_lowest=True), pd.cut(col_data, bins=10, retbins=True)[1]
                hist_data = {
                    'bins': [float(b) for b in hist_bins],
                    'counts': [int((hist_counts == i).sum()) for i in range(10)]
                }
                # Urgent info
                urgent = []
                if stats['missing'] > 0:
                    urgent.append(f"{stats['missing']} missing values detected.")
                if stats['outlier_count'] > 0:
                    urgent.append(f"{stats['outlier_count']} outliers detected.")
                if stats['count'] == 0:
                    urgent.append("No valid data in this column.")
                # Store all analysis
                analysis_data[col] = {
                    'stats': stats,
                    'urgent': urgent,
                    'histogram': hist_data,
                    'line': df[col].tolist(),
                }
                # Save total as before
                total = float(df[col].sum()) if not df[col].empty else 0.0
                ProcessedData.objects.create(
                    uploaded_file=obj,
                    column_name=col,
                    value=total
                )
                chart_data[col] = df[col].tolist()
            # Store analysis data in session
            request.session['analysis_data'] = json.dumps(analysis_data)
            request.session['chart_data'] = json.dumps(chart_data)
            # ✅ Redirect դեպի result page
            return redirect('result', file_id=obj.id)

        except Exception as e:
            return render(request, 'analytics_app/upload.html', {
                'error': f'Unexpected error: {str(e)}'
            })

    # Եթե GET է, վերադարձնում ենք upload form-ը
    return render(request, 'analytics_app/upload.html')


# Արդյունքների էջ
def result_view(request, file_id):
    file_obj = get_object_or_404(UploadedFile, id=file_id)
    data = ProcessedData.objects.filter(uploaded_file=file_obj)
    chart_data = json.loads(request.session.get('chart_data', '{}'))
    analysis_data = json.loads(request.session.get('analysis_data', '{}'))
    context = {
        'file': file_obj,
        'data': data,
        'chart_data': chart_data,
        'analysis_data': analysis_data
    }
    return render(request, 'analytics_app/result.html', context)


# Վերադարձնում ենք բոլոր վերբեռնված ֆայլերը
def files_view(request):
    files = UploadedFile.objects.all().order_by('-id')
    return render(request, 'analytics_app/files.html', {'files': files})


def delete_file_view(request, file_id):
    file_obj = get_object_or_404(UploadedFile, id=file_id)
    if request.method == 'POST':
        # Delete the file from storage
        file_path = file_obj.file.path
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            file_obj.delete()
            messages.success(request, 'File deleted successfully.')
        except Exception as e:
            messages.error(request, 'Error deleting file.')
        return redirect('files')
    return redirect('files')
