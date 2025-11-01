from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import UploadedFile, ProcessedData
import pandas as pd
import json
from django.contrib import messages
import os
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import numpy as np
import datetime


def make_json_serializable(o):
    # primitives
    if o is None:
        return None
    if isinstance(o, (str, bool, int, float)):
        return o
    # numpy scalar types
    if isinstance(o, (np.integer, np.int64, np.int32)):
        return int(o)
    if isinstance(o, (np.floating, np.float64, np.float32)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    # datetime
    if isinstance(o, (datetime.datetime, datetime.date)):
        return o.isoformat()
    # lists/tuples
    if isinstance(o, (list, tuple)):
        return [make_json_serializable(x) for x in o]
    # numpy arrays
    if isinstance(o, np.ndarray):
        return [make_json_serializable(x) for x in o.tolist()]
    # dicts
    if isinstance(o, dict):
        return {str(k): make_json_serializable(v) for k, v in o.items()}
    # pandas types
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
    # fallback
    try:
        return json.loads(json.dumps(o))
    except Exception:
        return str(o)


# Գլխավոր էջ
def home_view(request):
    return render(request, 'analytics_app/index.html')


# Upload էջ
def upload_view(request):
    if request.method != 'POST':
        return render(request, 'analytics_app/upload.html')

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return render(request, 'analytics_app/upload.html', {'error': 'No file was uploaded.'})

    # Validate file type
    filename = uploaded_file.name.lower()
    file_type = next((ext for ext in settings.ALLOWED_FILE_TYPES if filename.endswith(f'.{ext}')), None)
    if not file_type:
        return render(request, 'analytics_app/upload.html', 
                     {'error': f'Unsupported file type. Allowed types: {", ".join(settings.ALLOWED_FILE_TYPES)}'})

    # Validate file size
    if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
        return render(request, 'analytics_app/upload.html', 
                     {'error': f'File too large. Maximum size is {settings.MAX_UPLOAD_SIZE/(1024*1024)}MB'})

    if uploaded_file.size == 0:
        return render(request, 'analytics_app/upload.html', {'error': 'The uploaded file is empty.'})

    try:
        obj = UploadedFile.objects.create(
            file=uploaded_file,
            file_type=file_type,
            user=request.user if request.user.is_authenticated else None
        )

        # Queue the file for processing. In development we may run tasks eagerly
        from .tasks import process_uploaded_file
        try:
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                # Run synchronously in-process to avoid needing a broker/worker in dev
                process_uploaded_file(obj.id)
            else:
                process_uploaded_file.delay(obj.id)
        except Exception as e:
            # Record error on the UploadedFile and show a friendly message
            obj.error_message = str(e)
            obj.save()
            return render(request, 'analytics_app/upload.html', {'error': f'Unexpected error: {str(e)}'})

        messages.success(request, 'File uploaded successfully! Processing has started...')

        # Redirect straight away; processing runs in background or was executed inline above
        return redirect(f"{reverse('result', kwargs={'file_id': obj.id})}?show_modal=1")

    except Exception as e:
        # Return upload page with error message on unexpected exception
        return render(request, 'analytics_app/upload.html', {'error': f'Unexpected error: {str(e)}'})

# Արդյունքների էջ
def result_view(request, file_id):
    file_obj = get_object_or_404(UploadedFile, id=file_id)
    
    if not file_obj.processed and not file_obj.error_message:
        messages.info(request, 'File is still being processed. Please refresh the page.')
        return render(request, 'analytics_app/result.html', {'file': file_obj, 'processing': True})
    
    if file_obj.error_message:
        messages.error(request, f'Error processing file: {file_obj.error_message}')
        return render(request, 'analytics_app/result.html', {'file': file_obj, 'error': True})
    
    data = ProcessedData.objects.filter(uploaded_file=file_obj).select_related('uploaded_file')
    
    chart_data = {}
    analysis_data = {}
    
    for processed_data in data:
        column_name = processed_data.column_name
        stats = processed_data.stats
        # Ensure stats is a dict (some DB records may have JSON stored as a string
        # or other unexpected types). This prevents errors like "'str' object has no attribute 'get'".
        if isinstance(stats, str):
            try:
                stats = json.loads(stats)
            except Exception:
                stats = {}
        if not isinstance(stats, dict):
            try:
                # Try to coerce mapping-like objects to dict
                stats = dict(stats)
            except Exception:
                stats = {}

        analysis_data[column_name] = {
            'stats': stats,
            'urgent': [],
        }

        if stats.get('missing', 0) > 0:
            analysis_data[column_name]['urgent'].append(f"{stats.get('missing', 0)} missing values detected.")

        if 'histogram' in stats:
            # For the JS line charts we prefer a numeric array of sample values.
            # Tasks now include 'sample_values' when possible. Fall back to histogram counts
            # (not ideal for a line chart but safe) or an empty list to avoid JS exceptions.
            sample_vals = stats.get('sample_values') if isinstance(stats.get('sample_values'), (list, tuple)) else None
            if sample_vals and len(sample_vals) > 0:
                chart_data[column_name] = sample_vals
            else:
                hist = stats.get('histogram') or {}
                counts = hist.get('counts') if isinstance(hist, dict) else None
                if isinstance(counts, list):
                    chart_data[column_name] = counts
                else:
                    chart_data[column_name] = []
    # Also provide JSON-serialized strings specifically for the JS in the template
    chart_data = make_json_serializable(chart_data)
    analysis_data = make_json_serializable(analysis_data)

    chart_data_json = json.dumps(chart_data)
    analysis_data_json = json.dumps(analysis_data)

    context = {
        'file': file_obj,
        'data': data,
        'chart_data': chart_data,
        'analysis_data': analysis_data,
        'chart_data_json': chart_data_json,
        'analysis_data_json': analysis_data_json,
    }
    context['show_modal'] = request.GET.get('show_modal', '0')
    return render(request, 'analytics_app/result.html', context)


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
        return redirect('my_uploads')
    return redirect('my_uploads')


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
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        errors = []
        if not username:
            errors.append('Username is required.')
        if not email:
            errors.append('Email is required.')
        if not password:
            errors.append('Password is required.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        if errors:
            return render(request, 'analytics_app/register.html', {'error': ' '.join(errors)})
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect('home')
        except Exception as e:
            return render(request, 'analytics_app/register.html', {'error': f'Error: {str(e)}'})
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


# Health check used by docker-compose and monitoring
from django.http import HttpResponse
from django.db import connections
from django.db.utils import OperationalError
try:
    from redis import Redis
    from redis.exceptions import ConnectionError as RedisConnectionError
except Exception:
    Redis = None
    RedisConnectionError = Exception

def health_check(request):
    # Check database connection
    try:
        connections['default'].ensure_connection()
    except OperationalError:
        return HttpResponse('Database unavailable', status=503)

    # Check Redis connection (optional)
    if Redis is not None:
        try:
            redis_client = Redis.from_url('redis://redis:6379/0')
            redis_client.ping()
        except RedisConnectionError:
            return HttpResponse('Redis unavailable', status=503)

    return HttpResponse('OK', status=200)
