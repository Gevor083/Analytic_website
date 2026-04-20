"""
Admin / general views: home, my_uploads, admin_dashboard, health_check.
"""

import json
import logging
from datetime import timedelta
from collections import Counter

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from ..models import UploadedFile

logger = logging.getLogger(__name__)

try:
    from redis import Redis
    from redis.exceptions import ConnectionError as RedisConnectionError
except Exception:
    Redis = None
    RedisConnectionError = Exception


def home_view(request):
    """Render the landing / home page."""
    return render(request, 'analytics_app/index.html')


@login_required
def my_uploads_view(request):
    """Display the current user's upload history with pagination."""
    all_uploads = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')
    total_uploaded_files = all_uploads.count()
    processed_count = all_uploads.filter(processed=True).count()
    last_upload_date = all_uploads.first().uploaded_at if all_uploads.exists() else None

    average_rows_per_dataset = 0
    if total_uploaded_files > 0:
        total_rows = sum(u.num_rows for u in all_uploads)
        average_rows_per_dataset = total_rows / total_uploaded_files

    paginator = Paginator(all_uploads, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'uploads': page_obj,
        'page_obj': page_obj,
        'total_uploaded_files': total_uploaded_files,
        'processed_count': processed_count,
        'last_upload_date': last_upload_date,
        'average_rows_per_dataset': average_rows_per_dataset,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, 'analytics_app/my_uploads.html', context)


@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_dashboard_view(request):
    """Staff-only dashboard with user & upload statistics, charts, and pagination."""
    users = User.objects.all().order_by('username')
    all_uploads = UploadedFile.objects.select_related('user').order_by('-uploaded_at')

    upload_paginator = Paginator(all_uploads, 50)
    upload_page = upload_paginator.get_page(request.GET.get('page'))

    # ── Activity chart data: last 14 days ─────────────────────────
    today = timezone.now().date()
    activity_labels = [(today - timedelta(days=i)).strftime('%b %d') for i in reversed(range(14))]
    activity_data = []
    for i in reversed(range(14)):
        day = today - timedelta(days=i)
        count = UploadedFile.objects.filter(
            uploaded_at__date=day
        ).count()
        activity_data.append(count)

    # ── File type distribution ─────────────────────────────────────
    type_counts = Counter(all_uploads.values_list('file_type', flat=True))
    type_data = {k.upper(): v for k, v in type_counts.items()}

    context = {
        'users': users,
        'uploads': upload_page,
        'upload_page_obj': upload_page,
        'total_users': users.count(),
        'total_uploads': all_uploads.count(),
        'processed_count': all_uploads.filter(processed=True).count(),
        'error_count': all_uploads.filter(error_message__isnull=False).exclude(error_message='').count(),
        'uploads_by_user': {user: list(UploadedFile.objects.filter(user=user)) for user in users},
        'activity_labels_json': json.dumps(activity_labels),
        'activity_data_json': json.dumps(activity_data),
        'type_data_json': json.dumps(type_data),
    }
    return render(request, 'analytics_app/admin_dashboard.html', context)


def health_check(request):
    """Simple health-check used by monitoring / docker-compose."""
    try:
        connections['default'].ensure_connection()
    except OperationalError:
        return HttpResponse('Database unavailable', status=503)

    if Redis is not None:
        try:
            import os
            from django.conf import settings
            redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
            redis_client = Redis.from_url(redis_url)
            redis_client.ping()
        except RedisConnectionError:
            pass  # Redis is optional in dev

    return HttpResponse('OK', status=200)


def api_file_status(request, file_id):
    """
    Lightweight polling endpoint for the result page.
    Returns JSON with processed status so the front-end can redirect automatically.
    """
    try:
        f = UploadedFile.objects.get(id=file_id)
    except UploadedFile.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    return JsonResponse({
        'id': f.id,
        'processed': f.processed,
        'error_message': f.error_message,
        'num_rows': f.num_rows,
    })
