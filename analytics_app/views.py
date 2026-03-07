"""
Django views for the analytics app.

This module contains all the view functions for handling HTTP requests and responses
in the analytics application. It includes views for file upload, result display,
chart generation, user authentication, and API endpoints.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import UploadedFile, ProcessedData
import pandas as pd
import json
import csv
from django.contrib import messages
import os
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import numpy as np
import datetime
from collections import defaultdict


def make_json_serializable(o):
    # Handle NaN values
    if isinstance(o, float) and (np.isnan(o) or o == float('inf') or o == float('-inf')):
        return None  # or 0, but None is safer for stats
    # primitives
    if o is None:
        return None
    if isinstance(o, (str, bool, int, float)):
        return o
    # numpy scalar types
    if isinstance(o, (np.integer, np.int64, np.int32)):
        return int(o)
    if isinstance(o, (np.floating, np.float64, np.float32)):
        val = float(o)
        if np.isnan(val) or val == float('inf') or val == float('-inf'):
            return None
        return val
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
        return json.dumps(o, default=str)
    except Exception:
        return str(o)


import logging

logger = logging.getLogger(__name__)

# Գլխավոր էջ
def home_view(request):
    """
    Renders the home page of the analytics application.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered home page template.
    """
    return render(request, 'analytics_app/index.html')


# Upload էջ
def upload_view(request):
    """
    Handles file upload requests.

    Validates the uploaded file for type, size, and emptiness. Creates an UploadedFile
    instance and queues it for processing. Redirects to the result page upon success.

    Args:
        request: The HTTP request object containing the uploaded file.

    Returns:
        HttpResponse: Rendered upload page with errors or redirect to result page.
    """
    if request.method != 'POST':
        return render(request, 'analytics_app/upload.html')

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        logger.warning("Upload attempt with no file.")
        return render(request, 'analytics_app/upload.html', {'error': 'No file was uploaded.'})

    # Validate file type
    filename = uploaded_file.name.lower()
    file_type = next((ext for ext in settings.ALLOWED_FILE_TYPES if filename.endswith(f'.{ext}')), None)
    if not file_type:
        logger.warning(f"Unsupported file type uploaded: {filename}")
        return render(request, 'analytics_app/upload.html',
                     {'error': f'Unsupported file type. Allowed types: {", ".join(settings.ALLOWED_FILE_TYPES)}'})

    # Validate file size
    if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
        logger.warning(f"File too large uploaded: {filename} ({uploaded_file.size} bytes)")
        return render(request, 'analytics_app/upload.html',
                     {'error': f'File too large. Maximum size is {settings.MAX_UPLOAD_SIZE/(1024*1024)}MB'})

    if uploaded_file.size == 0:
        logger.warning(f"Empty file uploaded: {filename}")
        return render(request, 'analytics_app/upload.html', {'error': 'The uploaded file is empty.'})

    try:
        # Convert JSON or XLSX to CSV if necessary
        if file_type in ['json', 'xlsx']:
            try:
                uploaded_file.seek(0)  # Ensure we're at the beginning of the file
                if file_type == 'json':
                    # Read JSON file
                    data = json.load(uploaded_file)
                    # If your JSON has a nested list inside (like "users"), extract it:
                    if isinstance(data, dict):
                        # Check if it's a single object or has nested list
                        if isinstance(data, dict) and len(data) == 1 and isinstance(list(data.values())[0], list):
                            # Extract nested list
                            data = data[list(data.keys())[0]]
                        else:
                            # Single object, wrap in list
                            data = [data]
                    # Now write CSV
                    from io import StringIO
                    csv_buffer = StringIO()
                    writer = csv.DictWriter(csv_buffer, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                    csv_content = csv_buffer.getvalue()

                elif file_type == 'xlsx':
                    uploaded_file.seek(0)  # Ensure we're at the beginning for XLSX
                    df = pd.read_excel(uploaded_file, engine='openpyxl')

                    # Validate that we got a DataFrame with data
                    if df is None or df.empty:
                        raise ValueError("Converted file contains no data")

                    # Ensure we have proper column names
                    if df.columns is None or len(df.columns) == 0:
                        raise ValueError("Converted file has no valid columns")

                    # Convert to CSV in memory
                    from io import StringIO
                    csv_buffer = StringIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_content = csv_buffer.getvalue()

                # Validate CSV content
                if not csv_content or len(csv_content.strip()) == 0:
                    raise ValueError("Failed to generate CSV content")

                # Create a new file-like object for the CSV content
                from django.core.files.base import ContentFile
                csv_file = ContentFile(csv_content.encode('utf-8'), name=uploaded_file.name.rsplit('.', 1)[0] + '.csv')

                # Update file and file_type
                uploaded_file = csv_file
                file_type = 'csv'
                logger.info(f"Converted {filename} to CSV format successfully.")

            except Exception as e:
                logger.error(f"Error converting {filename} to CSV: {e}", exc_info=True)
                return render(request, 'analytics_app/upload.html', {'error': f'Error converting file to CSV: {str(e)}'})

        obj = UploadedFile.objects.create(
            file=uploaded_file,
            file_type=file_type,
            user=request.user if request.user.is_authenticated else None
        )
        logger.info(f"File {obj.id} ({filename}) uploaded successfully by user {request.user.id if request.user.is_authenticated else 'anonymous'}.")

        # Queue the file for processing. In development we may run tasks eagerly
        from .tasks import process_uploaded_file
        try:
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                # Run the task synchronously in a reliable way (use apply to execute locally)
                process_uploaded_file.apply(args=(obj.id,))
                logger.info(f"File {obj.id} processed eagerly.")
            else:
                process_uploaded_file.delay(obj.id)
                logger.info(f"File {obj.id} queued for background processing.")
        except Exception as e:
            logger.error(f"Error queuing/processing file {obj.id}: {e}", exc_info=True)
            # Record error on the UploadedFile and show a friendly message
            obj.error_message = str(e)
            obj.save()
            return render(request, 'analytics_app/upload.html', {'error': f'Unexpected error: {str(e)}'})

        messages.success(request, 'File uploaded successfully! Processing has started...')

        # Redirect straight away; processing runs in background or was executed inline above
        return redirect(reverse('result', kwargs={'file_id': obj.id}))

    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}", exc_info=True)
        # Return upload page with error message on unexpected exception
        return render(request, 'analytics_app/upload.html', {'error': f'Unexpected error: {str(e)}'})

# Արդյունքների էջ
def result_view(request, file_id):
    """
    Displays the result page for a processed file.

    Args:
        request: The HTTP request object.
        file_id: The ID of the uploaded file.

    Returns:
        HttpResponse: Rendered result page.
    """
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

        analysis_data[column_name] = {
            'stats': stats,
            'urgent': [],
            'data_type': processed_data.data_type,
        }

        if stats.get('missing', 0) > 0:
            analysis_data[column_name]['urgent'].append(f"{stats.get('missing', 0)} missing values detected.")

        if 'histogram' in stats:
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

    chart_data = make_json_serializable(chart_data)
    analysis_data = make_json_serializable(analysis_data)

    chart_data_json = json.dumps(chart_data)
    analysis_data_json = json.dumps(analysis_data)

    processed_chart_data = file_obj.processed_chart_data or {}
    numeric_fields = file_obj.numeric_fields or []

    try:
        df = pd.read_csv(file_obj.file.path)
        categorical_fields = get_categorical_fields(df)
        
        # Get data preview (first 50 rows) for datatables
        data_preview = df.head(50).to_dict(orient='records')
    except Exception:
        categorical_fields = []
        data_preview = [] # Ensure data_preview is always defined

    processed_chart_data_json = json.dumps(make_json_serializable(processed_chart_data))
    numeric_fields_json = json.dumps(numeric_fields)
    categorical_fields_json = json.dumps(categorical_fields)

    logger.debug(f"Numeric Fields: {numeric_fields}")
    logger.debug(f"Categorical Fields: {categorical_fields}")

    context = {
        'file': file_obj,
        'data': data,
        'chart_data': chart_data,
        'analysis_data': analysis_data,
        'chart_data_json': chart_data_json,
        'analysis_data_json': analysis_data_json,
        'processed_chart_data_json': processed_chart_data_json,
        'numeric_fields_json': numeric_fields_json,
        'categorical_fields_json': categorical_fields_json,
        'data_preview': data_preview, # Add data_preview to context
        'file_id': file_id,
    }
    context['show_modal'] = request.GET.get('show_modal', '0')
    return render(request, 'analytics_app/result.html', context)


def delete_file_view(request, file_id):
    """
    Deletes the uploaded file and its associated data.

    Args:
        request: The HTTP request object.
        file_id: The ID of the file to delete.

    Returns:
        HttpResponse: Redirect to my_uploads page.
    """
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
    """
    Displays the user's uploaded files with statistics.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered my_uploads page.
    """
    uploads = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')
    total_uploaded_files = uploads.count()
    last_upload_date = uploads.first().uploaded_at if uploads.exists() else None
    
    average_rows_per_dataset = 0
    if total_uploaded_files > 0:
        total_rows = sum(upload.num_rows for upload in uploads)
        average_rows_per_dataset = total_rows / total_uploaded_files

    context = {
        'uploads': uploads,
        'total_uploaded_files': total_uploaded_files,
        'last_upload_date': last_upload_date,
        'average_rows_per_dataset': average_rows_per_dataset,
    }
    return render(request, 'analytics_app/my_uploads.html', context)


def login_view(request):
    """
    Handles user login.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Redirect to home or rendered login page.
    """
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
    """
    Logs out the user and redirects to login page.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Redirect to login page.
    """
    logout(request)
    return redirect('login')


def register_view(request):
    """
    Handles user registration.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Redirect to home or rendered register page.
    """
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
    """
    Displays the admin dashboard with user and upload statistics.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered admin dashboard page.
    """
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
from django.http import HttpResponse, FileResponse, JsonResponse
from django.db import connections
from django.db.utils import OperationalError
import matplotlib.pyplot as plt
import io
try:
    from redis import Redis
    from redis.exceptions import ConnectionError as RedisConnectionError
except Exception:
    Redis = None
    RedisConnectionError = Exception

def health_check(request):
    """
    Performs health checks for database and Redis.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: OK or error status.
    """
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


def get_numeric_fields(df):
    """
    Identify numeric fields in a DataFrame.
    Returns a list of column names that are numeric.
    """
    numeric_fields = []
    for col in df.columns:
        # Check if the column can be converted to numeric
        try:
            numeric_series = pd.to_numeric(df[col], errors='coerce')
            # Ensure at least some values are numeric and not all NaN
            if numeric_series.notna().sum() > 0:
                numeric_fields.append(col)
        except Exception:
            continue
    return numeric_fields


def detect_outliers_iqr(series):
    """
    Detects outliers in a pandas Series using the Interquartile Range (IQR) method.
    Returns a list of outlier values.
    """
    if not pd.api.types.is_numeric_dtype(series):
        return []

    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = series[(series < lower_bound) | (series > upper_bound)].tolist()
    return outliers


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
        std_val = row['std']
        count_val = row['count']

        result.append({
            'x': x_val,
            'y': mean_val,  # For line chart, y is the mean
            'stats': {
                'mean': mean_val,
                'median': median_val,
                'min': min_val,
                'max': max_val,
                'std': std_val,
                'count': count_val
            }
        })

    return result

def get_categorical_fields(df, max_unique=20):

    """

    Identify categorical fields in a DataFrame, suitable for pie charts.

    Returns a list of column names with a limited number of unique values.

    """

    categorical_fields = []

    for col in df.columns:

        # Check if the column is non-numeric and has a reasonable number of unique values

        if df[col].dtype == 'object' or df[col].nunique() <= max_unique:

            categorical_fields.append(col)

    return categorical_fields

def apply_filter(df, filter_column, filter_operator, filter_value):
    """
    Applies a filter to the DataFrame based on column, operator, and value.

    Args:
        df: The pandas DataFrame.
        filter_column: The column to filter.
        filter_operator: The operator (eq, ne, gt, etc.).
        filter_value: The value to filter by.

    Returns:
        DataFrame: The filtered DataFrame.
    """
    if not filter_column or not filter_operator or not filter_value:
        return df

    if filter_column not in df.columns:
        return df # Or raise an error

    try:
        # Attempt to convert filter_value to the column's dtype for accurate comparison
        if pd.api.types.is_numeric_dtype(df[filter_column]):
            filter_value = pd.to_numeric(filter_value)
        elif pd.api.types.is_datetime64_any_dtype(df[filter_column]):
            filter_value = pd.to_datetime(filter_value)
    except ValueError:
        # If conversion fails, treat as string comparison
        pass

    if filter_operator == 'eq':
        df = df[df[filter_column] == filter_value]
    elif filter_operator == 'ne':
        df = df[df[filter_column] != filter_value]
    elif filter_operator == 'gt':
        df = df[df[filter_column] > filter_value]
    elif filter_operator == 'lt':
        df = df[df[filter_column] < filter_value]
    elif filter_operator == 'ge':
        df = df[df[filter_column] >= filter_value]
    elif filter_operator == 'le':
        df = df[df[filter_column] <= filter_value]
    
    return df

def apply_sort(df, sort_column, sort_order):
    """
    Sorts the DataFrame by the specified column and order.

    Args:
        df: The pandas DataFrame.
        sort_column: The column to sort by.
        sort_order: 'asc' or 'desc'.

    Returns:
        DataFrame: The sorted DataFrame.
    """
    if not sort_column or sort_column not in df.columns:
        return df

    ascending = True if sort_order == 'asc' else False
    df = df.sort_values(by=sort_column, ascending=ascending)
    return df

def generate_chart_view(request, file_id):
    """
    Generates and returns a chart image based on the file data.

    Args:
        request: The HTTP request object.
        file_id: The ID of the uploaded file.

    Returns:
        HttpResponse: The chart image or error.
    """
    logger.info(f"Chart generation requested for file_id: {file_id} with params: {request.GET}")
    file_obj = get_object_or_404(UploadedFile, id=file_id)
    chart_type = request.GET.get('chart_type', 'line')
    x_axis = request.GET.get('x_axis')
    y_axis = request.GET.get('y_axis')

    if not x_axis and chart_type not in ['correlation', 'pie', 'histogram', 'boxplot']:
        logger.error(f"Chart generation failed for file_id {file_id}: X-axis not specified for chart type {chart_type}.")
        return HttpResponse("X-axis must be specified for this chart type.", status=400)

    logger.debug(f"Chart Type: {chart_type}, X-axis: {x_axis}, Y-axis: {y_axis}")

    try:
        df = pd.read_csv(file_obj.file.path)
    except Exception as e:
        logger.error(f"Error reading file {file_obj.file.path} for chart generation (file_id: {file_id}): {e}", exc_info=True)
        return HttpResponse(f"Error reading file: {e}", status=500)

    # Apply filtering
    filter_column = request.GET.get('filter_column')
    filter_operator = request.GET.get('filter_operator')
    filter_value = request.GET.get('filter_value')
    df = apply_filter(df, filter_column, filter_operator, filter_value)

    # Apply sorting
    sort_column = request.GET.get('sort_column')
    sort_order = request.GET.get('sort_order')
    df = apply_sort(df, sort_column, sort_order)

    plt.figure(figsize=(10, 6))

    if chart_type in ['line', 'bar']:
        if not y_axis:
            logger.error(f"Chart generation failed for file_id {file_id}: Y-axis not specified for chart type {chart_type}.")
            return HttpResponse("Y-axis must be specified for this chart type.", status=400)
        
        chart_data = group_and_calculate_stats(df, x_axis, y_axis)
        
        if not chart_data:
            logger.error(f"Chart generation failed for file_id {file_id}: Could not generate data for selected axes ({x_axis}, {y_axis}).")
            return HttpResponse(f"Could not generate data for the selected axes.", status=404)

        x_data = [item['x'] for item in chart_data]
        y_data = [item['y'] for item in chart_data]
        logger.debug(f"Line/Bar Chart Data - x_data: {x_data}, y_data: {y_data}")
    
        if chart_type == 'line':
            plt.plot(x_data, y_data)
        elif chart_type == 'bar':
            plt.bar(x_data, y_data)
        
        plt.xlabel(x_axis)
        plt.ylabel(y_axis)
        plt.title(f'{chart_type.capitalize()} Chart: {y_axis} vs {x_axis}')
        plt.tight_layout()

    elif chart_type == 'scatter':
        if not y_axis:
            logger.error(f"Chart generation failed for file_id {file_id}: Y-axis not specified for scatter plot.")
            return HttpResponse("Y-axis must be specified for this chart type.", status=400)
        if x_axis not in df.columns or y_axis not in df.columns:
            logger.error(f"Chart generation failed for file_id {file_id}: Invalid axis specified for scatter plot (X: {x_axis}, Y: {y_axis}).")
            return HttpResponse("Invalid axis specified.", status=400)
        if not pd.api.types.is_numeric_dtype(df[x_axis]) or not pd.api.types.is_numeric_dtype(df[y_axis]):
            logger.error(f"Chart generation failed for file_id {file_id}: Non-numeric axes for scatter plot (X: {x_axis}, Y: {y_axis}).")
            return HttpResponse("Both X and Y axes must be numeric for a scatter plot.", status=400)
        logger.debug(f"Scatter Plot Data - X-axis: {df[x_axis].tolist()}, Y-axis: {df[y_axis].tolist()}")
        
        plt.scatter(df[x_axis], df[y_axis])
        plt.xlabel(x_axis)
        plt.ylabel(y_axis)
        plt.title(f'Scatter Plot: {y_axis} vs {x_axis}')
        plt.tight_layout()

    elif chart_type == 'histogram':
        if x_axis not in df.columns:
            logger.error(f"Chart generation failed for file_id {file_id}: Invalid column specified for histogram (X: {x_axis}).")
            return HttpResponse("Invalid column specified for histogram.", status=400)
        if not pd.api.types.is_numeric_dtype(df[x_axis]):
            logger.error(f"Chart generation failed for file_id {file_id}: Non-numeric X-axis for histogram (X: {x_axis}).")
            return HttpResponse("X-axis must be numeric for a histogram.", status=400)
        logger.debug(f"Histogram Data - X-axis: {df[x_axis].dropna().tolist()}")
        
        plt.hist(df[x_axis].dropna(), bins=20)
        plt.xlabel(x_axis)
        plt.ylabel('Frequency')
        plt.title(f'Histogram of {x_axis}')
        plt.tight_layout()

    elif chart_type == 'pie':
        if x_axis not in df.columns:
            return HttpResponse("Invalid column specified for pie chart.", status=400)
        
        # For pie charts, we need a categorical-like column with a reasonable number of unique values
        if pd.api.types.is_numeric_dtype(df[x_axis]):
            return HttpResponse("X-axis must be categorical or have a limited number of unique values for a pie chart.", status=400)

        counts = df[x_axis].value_counts()
        logger.debug(f"Pie Chart Data - Counts: {counts.to_dict()}")
        if len(counts) > 10:
            top_10 = counts.nlargest(10)
            other_sum = counts.iloc[10:].sum()
            if other_sum > 0:
                top_10['Other'] = other_sum
            counts = top_10

        plt.figure(figsize=(8, 8))
        plt.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140)
        plt.title(f'Pie Chart of {x_axis}')
        plt.ylabel('')
        plt.tight_layout()
        plt.tight_layout()

    elif chart_type == 'boxplot':
        if x_axis not in df.columns:
            return HttpResponse("Invalid column specified for boxplot.", status=400)
        
        if not pd.api.types.is_numeric_dtype(df[x_axis]):
            return HttpResponse("Boxplot is only available for numeric fields.", status=400)
        logger.debug(f"Box Plot Data - X-axis: {df[x_axis].dropna().tolist()}")
        
        plt.boxplot(df[x_axis].dropna())
        plt.ylabel(x_axis)
        plt.title(f'Box Plot of {x_axis}')
        plt.tight_layout()

    elif chart_type == 'correlation':
        numeric_cols = get_numeric_fields(df)
        if len(numeric_cols) < 2:
            return HttpResponse("Correlation matrix requires at least two numeric columns.", status=400)
        
        corr = df[numeric_cols].corr()
        logger.debug(f"Correlation Matrix: {corr}")
        
        fig, ax = plt.subplots()
        cax = ax.imshow(corr, cmap='coolwarm')
        
        fig.colorbar(cax)
        
        ax.set_xticks(np.arange(len(numeric_cols)))
        ax.set_yticks(np.arange(len(numeric_cols)))
        
        ax.set_xticklabels(numeric_cols)
        ax.set_yticklabels(numeric_cols)
        
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        for i in range(len(numeric_cols)):
            for j in range(len(numeric_cols)):
                text = ax.text(j, i, f"{corr.iloc[i, j]:.2f}",
                               ha="center", va="center", color="w")
        
        ax.set_title("Correlation Matrix")
        fig.tight_layout()

    else:
        return HttpResponse("Invalid chart type specified.", status=400)

    plt.grid(True)
    buf = io.BytesIO()
    
    download = request.GET.get('download') == 'true'
    output_format = request.GET.get('format', 'png') # Default to png

    if output_format == 'svg':
        plt.savefig(buf, format='svg')
        content_type = 'image/svg+xml'
    elif output_format == 'pdf':
        plt.savefig(buf, format='pdf')
        content_type = 'application/pdf'
    else: # Default to png
        plt.savefig(buf, format='png')
        content_type = 'image/png'

    plt.close()
    buf.seek(0)

    if download:
        filename = f'{chart_type}_chart_{file_id}.{output_format}'
        response = HttpResponse(buf.getvalue(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return HttpResponse(buf.getvalue(), content_type=content_type)

def missing_values_chart_view(request, file_id):
    """
    Generates a chart showing missing values per column.

    Args:
        request: The HTTP request object.
        file_id: The ID of the uploaded file.

    Returns:
        HttpResponse: The chart image.
    """
    file_obj = get_object_or_404(UploadedFile, id=file_id)

    try:
        df = pd.read_csv(file_obj.file.path)
    except Exception as e:
        return HttpResponse(f"Error reading file: {e}", status=500)

    missing_values = df.isnull().sum()
    missing_values = missing_values[missing_values > 0]

    if missing_values.empty:
        return HttpResponse("No missing values found in this dataset.", status=200)

    plt.figure(figsize=(10, 8))
    missing_values.plot(kind='barh')
    plt.title('Missing Values per Column')
    plt.xlabel('Number of Missing Values')
    plt.ylabel('Columns')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)

    return HttpResponse(buf.getvalue(), content_type='image/png')

@login_required
def reanalyze_file_view(request, file_id):
    """
    Re-analyzes the uploaded file by resetting and re-queuing processing.

    Args:
        request: The HTTP request object.
        file_id: The ID of the file to re-analyze.

    Returns:
        HttpResponse: Redirect to result page.
    """
    file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    # Reset processing status
    file_obj.processed = False
    file_obj.error_message = None
    file_obj.save()

    # Re-queue the processing task
    from .tasks import process_uploaded_file
    try:
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            process_uploaded_file.apply(args=(file_obj.id,))
        else:
            process_uploaded_file.delay(file_obj.id)
        messages.success(request, 'File re-analysis started successfully!')
    except Exception as e:
        messages.error(request, f'Error re-analyzing file: {str(e)}')

    # Redirect to result page
    return redirect(reverse('result', kwargs={'file_id': file_id}))


@login_required
def api_analysis_results(request, file_id):
    try:
        file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    except Exception:
        return JsonResponse({'error': 'File not found or you do not have permission to access it.'}, status=404)

    if not file_obj.processed:
        return JsonResponse({'message': 'File is still being processed.'}, status=202)
    
    if file_obj.error_message:
        return JsonResponse({'error': f'Error processing file: {file_obj.error_message}'}, status=500)

    processed_data_qs = ProcessedData.objects.filter(uploaded_file=file_obj)
    
    # Serialize UploadedFile data
    file_data = {
        'id': file_obj.id,
        'file_name': file_obj.file.name.split('/')[-1],
        'uploaded_at': file_obj.uploaded_at.isoformat(),
        'file_type': file_obj.file_type,
        'processed': file_obj.processed,
        'error_message': file_obj.error_message,
        'num_rows': file_obj.num_rows,
        'num_columns': file_obj.num_columns,
        'file_size': file_obj.file.size,
        'processed_chart_data': file_obj.processed_chart_data,
        'numeric_fields': file_obj.numeric_fields,
    }

    # Serialize ProcessedData
    analysis_results = []
    for pd_obj in processed_data_qs:
        analysis_results.append({
            'column_name': pd_obj.column_name,
            'data_type': pd_obj.data_type,
            'stats': pd_obj.stats,
        })

    response_data = {
        'file_info': file_data,
        'analysis_results': analysis_results,
    }

    return JsonResponse(response_data)

@login_required
def api_all_files(request):
    """
    Returns a JSON list of all files uploaded by the user.

    Args:
        request: The HTTP request object.

    Returns:
        JsonResponse: List of files.
    """
    files = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')

    files_data = []
    for file_obj in files:
        files_data.append({
            'id': file_obj.id,
            'file_name': file_obj.file.name.split('/')[-1],
            'uploaded_at': file_obj.uploaded_at.isoformat(),
            'file_type': file_obj.file_type,
            'processed': file_obj.processed,
            'error_message': file_obj.error_message,
            'num_rows': file_obj.num_rows,
            'num_columns': file_obj.num_columns,
            'file_size': file_obj.file.size,
        })

    return JsonResponse({'files': files_data})


@login_required
def generate_pdf_report_view(request, file_id):
    """
    Generates a PDF report for the analyzed file.

    Args:
        request: The HTTP request object.
        file_id: The ID of the uploaded file.

    Returns:
        HttpResponse: The PDF file or error.
    """
    file_obj = get_object_or_404(UploadedFile, id=file_id)

    if not file_obj.processed:
        return HttpResponse("File is still being processed.", status=202)

    if file_obj.error_message:
        return HttpResponse(f"Error processing file: {file_obj.error_message}", status=500)

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()
        story = []

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=20,
            alignment=1,  # Center
            textColor=colors.darkblue,
            fontName='Helvetica-Bold',
        )
        heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontSize=18,
            spaceAfter=15,
            textColor=colors.navy,
            fontName='Helvetica-Bold',
        )
        heading3_style = ParagraphStyle(
            'CustomHeading3',
            parent=styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold',
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=5,
        )

        # Header
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.grey,
            alignment=1,
        )
        story.append(Paragraph("Analytics App - Data Analysis Report", header_style))
        story.append(Spacer(1, 10))

        # Title
        story.append(Paragraph(f"Analytics Report for {file_obj.file.name.split('/')[-1]}", title_style))
        story.append(Spacer(1, 20))

        # File Info
        story.append(Paragraph("File Information", heading2_style))
        # Get number of columns from the dataframe
        try:
            df = pd.read_csv(file_obj.file.path)
            num_columns = len(df.columns)
        except Exception:
            num_columns = "Unknown"
        file_info = [
            ["File Name", file_obj.file.name.split('/')[-1]],
            ["Uploaded At", file_obj.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')],
            ["File Type", file_obj.file_type],
            ["Number of Rows", str(file_obj.num_rows)],
            ["Number of Columns", str(num_columns)],
        ]
        table = Table(file_info, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.aliceblue, colors.lightcyan]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

        # Analysis Results
        story.append(Paragraph("Analysis Results", heading2_style))
        processed_data = ProcessedData.objects.filter(uploaded_file=file_obj)

        for pd_obj in processed_data:
            story.append(Paragraph(f"Column: {pd_obj.column_name} ({pd_obj.data_type})", heading3_style))
            stats = pd_obj.stats
            if isinstance(stats, str):
                try:
                    stats = json.loads(stats)
                except:
                    stats = {}

            stats_table_data = [["Statistic", "Value"]]
            for key, value in stats.items():
                if isinstance(value, list):
                    truncated = ', '.join(map(str, value[:5]))
                    if len(value) > 5:
                        truncated += '...'
                    stats_table_data.append([key, truncated])
                else:
                    val_str = str(value)
                    if len(val_str) > 50:
                        val_str = val_str[:50] + '...'
                    stats_table_data.append([key, val_str])

            stats_table = Table(stats_table_data, colWidths=[2*inch, 4*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.aliceblue, colors.lightcyan]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 15))

        # Charts (if available)
        story.append(Paragraph("Charts", heading2_style))
        story.append(Paragraph("Charts are available in the web interface. Visit the results page to view and download charts.", normal_style))

        # Footer
        story.append(Spacer(1, 20))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1,
        )
        story.append(Paragraph("Generated by Analytics App", footer_style))

        doc.build(story)
        buffer.seek(0)

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="analytics_report_{file_id}.pdf"'
        return response

    except Exception as e:
        logger.error(f"Error generating PDF report for file {file_id}: {e}", exc_info=True)
        return HttpResponse(f"Error generating PDF: {e}", status=500)


@login_required
def export_results_view(request, file_id):
    """
    Exports the file data in the specified format.

    Args:
        request: The HTTP request object.
        file_id: The ID of the uploaded file.

    Returns:
        HttpResponse: The exported file.
    """
    file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    if not file_obj.processed:
        return HttpResponse("File is still being processed.", status=202)

    if file_obj.error_message:
        return HttpResponse(f"Error processing file: {file_obj.error_message}", status=500)

    format_type = request.GET.get('format', 'csv')

    try:
        df = pd.read_csv(file_obj.file.path)
    except Exception as e:
        return HttpResponse(f"Error reading file: {e}", status=500)

    buffer = io.BytesIO()

    if format_type == 'csv':
        df.to_csv(buffer, index=False)
        content_type = 'text/csv'
        extension = 'csv'
    elif format_type == 'json':
        df.to_json(buffer, orient='records')
        content_type = 'application/json'
        extension = 'json'
    elif format_type == 'excel':
        df.to_excel(buffer, index=False, engine='openpyxl')
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        extension = 'xlsx'
    else:
        return HttpResponse("Invalid format specified.", status=400)

    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="exported_data_{file_id}.{extension}"'
    return response


def full_data_view(request, file_id):
    """
    Displays the full data of the uploaded file, limited to 1000 rows.

    Args:
        request: The HTTP request object.
        file_id: The ID of the uploaded file.

    Returns:
        HttpResponse: Rendered full data page.
    """
    file_obj = get_object_or_404(UploadedFile, id=file_id)

    if not file_obj.processed:
        messages.info(request, 'File is still being processed. Please refresh the page.')
        return render(request, 'analytics_app/full_data.html', {'file': file_obj, 'processing': True})

    if file_obj.error_message:
        messages.error(request, f'Error processing file: {file_obj.error_message}')
        return render(request, 'analytics_app/full_data.html', {'file': file_obj, 'error': True})

    try:
        df = pd.read_csv(file_obj.file.path)
        # Limit to 1000 rows
        full_data = df.head(1000).to_dict(orient='records')
        num_rows_displayed = len(full_data)
        total_rows = len(df)
    except Exception as e:
        logger.error(f"Error reading file for full data view: {e}", exc_info=True)
        full_data = []
        num_rows_displayed = 0
        total_rows = 0

    context = {
        'file': file_obj,
        'full_data': full_data,
        'num_rows_displayed': num_rows_displayed,
        'total_rows': total_rows,
    }
    return render(request, 'analytics_app/full_data.html', context)


def face_login_view(request):
    """
    Handles face-based login for admin users.

    On GET: Renders the face login page.
    On POST: Processes the captured image, detects and encodes the face, compares to stored encodings, and logs in if matched.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered face login page or redirect to admin.
    """
    if request.method == 'POST':
        import face_recognition
        import cv2
        import numpy as np
        import os
        from django.contrib.auth import authenticate, login
        from django.contrib.auth.models import User

        # Get the image data from the POST request
        image_data = request.POST.get('image')
        if not image_data:
            return render(request, 'analytics_app/face_login.html', {'error': 'No image data received.'})

        # Decode the base64 image
        try:
            import base64
            header, encoded = image_data.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        except Exception as e:
            logger.error(f"Error decoding image: {e}")
            return render(request, 'analytics_app/face_login.html', {'error': 'Invalid image data.'})

        # Detect faces in the image
        face_locations = face_recognition.face_locations(img)
        if not face_locations:
            return render(request, 'analytics_app/face_login.html', {'error': 'No face detected in the image.'})

        # Assume the first face is the one to use
        face_encoding = face_recognition.face_encodings(img, face_locations)[0]

        # Load known face encodings from faces/ directory
        faces_dir = os.path.join(settings.BASE_DIR, 'faces')
        known_encodings = []
        known_usernames = []

        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    username = os.path.splitext(filename)[0]
                    image_path = os.path.join(faces_dir, filename)
                    try:
                        known_image = face_recognition.load_image_file(image_path)
                        known_face_locations = face_recognition.face_locations(known_image)
                        if known_face_locations:
                            known_encoding = face_recognition.face_encodings(known_image, known_face_locations)[0]
                            known_encodings.append(known_encoding)
                            known_usernames.append(username)
                    except Exception as e:
                        logger.error(f"Error loading face image {filename}: {e}")

        # Compare faces
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)

        if True in matches:
            best_match_index = np.argmin(face_distances)
            matched_username = known_usernames[best_match_index]
            try:
                user = User.objects.get(username=matched_username, is_staff=True)
                login(request, user)
                return redirect('/admin/')
            except User.DoesNotExist:
                return render(request, 'analytics_app/face_login.html', {'error': 'Matched user is not an admin.'})
        else:
            return render(request, 'analytics_app/face_login.html', {'error': 'Face not recognized.'})

    return render(request, 'analytics_app/face_login.html')

from django.http import JsonResponse
import json
from django.views.decorators.http import require_POST

@require_POST
def set_theme(request):
    try:
        data = json.loads(request.body)
        theme = data.get('theme', 'light')
        if theme in ['light', 'dark']:
            request.session['theme'] = theme
            return JsonResponse({'status': 'ok', 'theme': theme})
        return JsonResponse({'status': 'error', 'message': 'Invalid theme'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

from django.http import JsonResponse
import pandas as pd

def chart_data_api(request, file_id):
    """
    Returns JSON formatted data for client-side Chart.js rendering.
    """
    file_obj = get_object_or_404(UploadedFile, id=file_id)
    chart_type = request.GET.get('chart_type', 'line')
    x_axis = request.GET.get('x_axis')
    y_axis = request.GET.get('y_axis')

    try:
        df = pd.read_csv(file_obj.file.path)
    except Exception as e:
        return JsonResponse({'error': f"Error reading file: {e}"}, status=500)

    try:
        # We need to fillna so JSON serialization doesn't fail with NaNs
        df = df.fillna(0) 

        if chart_type in ['line', 'bar']:
            cdata = group_and_calculate_stats(df, x_axis, y_axis)
            x_data = [item['x'] for item in cdata]
            y_data = [item['y'] for item in cdata]
            return JsonResponse({'x': x_data, 'y': y_data, 'label': y_axis})

        elif chart_type == 'scatter':
            # take sample to avoid overflowing browser
            df_sampled = df.sample(n=min(1000, len(df)))
            x_data = df_sampled[x_axis].tolist()
            y_data = df_sampled[y_axis].tolist()
            # For chart.js scatter we need array of objects {x, y}
            points = [{'x': x, 'y': y} for x, y in zip(x_data, y_data)]
            return JsonResponse({'data': points, 'x_label': x_axis, 'y_label': y_axis})

        elif chart_type == 'pie':
            counts = df[x_axis].value_counts().head(10) # max 10 slices
            return JsonResponse({'labels': counts.index.tolist(), 'data': counts.values.tolist(), 'label': x_axis})
            
        elif chart_type == 'histogram':
            import numpy as np
            counts, bins = np.histogram(pd.to_numeric(df[x_axis], errors='coerce').dropna(), bins=20)
            labels = [f"{bins[i]:.2f} - {bins[i+1]:.2f}" for i in range(len(counts))]
            return JsonResponse({'labels': labels, 'data': counts.tolist(), 'label': 'Frequency'})
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Unsupported chart type'}, status=400)
