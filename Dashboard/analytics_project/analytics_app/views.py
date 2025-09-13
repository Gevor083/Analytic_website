from django.shortcuts import render, redirect, get_object_or_404
from .models import UploadedFile, ProcessedData
import pandas as pd
import json
from django.contrib import messages
import os
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User


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
        # Only allow CSV, JSON, SQL
        if filename.endswith('.csv'):
            file_type = 'csv'
        elif filename.endswith('.json'):
            file_type = 'json'
        elif filename.endswith('.sql'):
            file_type = 'sql'
        else:
            return render(request, 'analytics_app/upload.html', {
                'error': 'Unsupported file type. Please upload CSV, JSON, or SQL files.'
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

            # Strictly select only float and int columns, EXCLUDE bool columns and columns with only bool values
            numeric_columns = []
            for col in df.columns:
                # Ensure column is a Series
                if not isinstance(df[col], pd.Series):
                    continue
                if pd.api.types.is_bool_dtype(df[col]):
                    continue
                non_null = df[col].dropna()
                if not non_null.empty and non_null.apply(lambda x: isinstance(x, bool)).all():
                    continue
                if pd.api.types.is_float_dtype(df[col]) or pd.api.types.is_integer_dtype(df[col]):
                    numeric_columns.append(col)
            chart_data = {}
            analysis_data = {}
            for col in numeric_columns:
                col_data = df[col].dropna()
                stats = {}
                try:
                    stats = {
                        'mean': float(col_data.mean()) if not col_data.empty else None,
                        'median': float(col_data.median()) if not col_data.empty else None,
                        'min': float(col_data.min()) if not col_data.empty else None,
                        'max': float(col_data.max()) if not col_data.empty else None,
                        'std': float(col_data.std()) if not col_data.empty else None,
                        'missing': int(df[col].isna().sum()) if isinstance(df[col].isna(), pd.Series) else 0,
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
                    if not col_data.empty and isinstance(col_data, pd.Series):
                        hist_result = pd.cut(col_data, bins=10, retbins=True, labels=False, include_lowest=True)
                        hist_bins = pd.cut(col_data, bins=10, retbins=True)[1]
                        hist_counts = [int((hist_result == i).sum()) for i in range(10)]
                        hist_data = {
                            'bins': [float(b) for b in hist_bins],
                            'counts': hist_counts
                        }
                    else:
                        hist_data = {'bins': [], 'counts': []}
                except Exception as e:
                    stats['error'] = f'Error in stats calculation: {str(e)}'
                    hist_data = {'bins': [], 'counts': []}
                # Urgent info
                urgent = []
                if stats.get('missing', 0) > 0:
                    urgent.append(f"{stats['missing']} missing values detected.")
                if stats.get('outlier_count', 0) > 0:
                    urgent.append(f"{stats['outlier_count']} outliers detected.")
                if stats.get('count', 0) == 0:
                    urgent.append("No valid data in this column.")
                # Store all analysis
                analysis_data[col] = {
                    'stats': stats,
                    'urgent': urgent,
                    'histogram': hist_data,
                    'line': df[col].tolist() if isinstance(df[col], pd.Series) else [],
                }
                # Save total as before
                try:
                    total = float(df[col].sum()) if isinstance(df[col], pd.Series) and not df[col].empty else 0.0
                except Exception:
                    total = 0.0
                ProcessedData.objects.create(
                    uploaded_file=obj,
                    column_name=col,
                    value=total
                )
                chart_data[col] = df[col].tolist() if isinstance(df[col], pd.Series) else []
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


@login_required
def my_uploads_view(request):
    uploads = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'analytics_app/my_uploads.html', {'uploads': uploads})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'analytics_app/login.html', {'error': 'Invalid username or password.'})
    return render(request, 'analytics_app/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            return render(request, 'analytics_app/register.html', {'error': 'Username already exists.'})
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect('home')
    return render(request, 'analytics_app/register.html')


@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_dashboard_view(request):
    from django.contrib.auth.models import User
    from .models import UploadedFile
    users = User.objects.all()
    uploads = UploadedFile.objects.select_related('user').all()
    total_users = users.count()
    total_uploads = uploads.count()
    uploads_by_user = {user: uploads.filter(user=user) for user in users}
    context = {
        'users': users,
        'uploads': uploads,
        'total_users': total_users,
        'total_uploads': total_uploads,
        'uploads_by_user': uploads_by_user,
    }
    return render(request, 'analytics_app/admin_dashboard.html', context)
