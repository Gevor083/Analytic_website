"""
Upload-related views: upload, delete, re-analyse.
"""

import csv
import json
import logging
import os

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..models import UploadedFile
from ..utils import get_upload_path

logger = logging.getLogger(__name__)


def upload_view(request):
    """Accept and validate a file upload, then queue background processing."""
    if request.method != 'POST':
        return render(request, 'analytics_app/upload.html')

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        logger.warning("Upload attempt with no file.")
        return render(request, 'analytics_app/upload.html', {'error': 'No file was uploaded.'})

    filename = uploaded_file.name.lower()
    file_type = next(
        (ext for ext in settings.ALLOWED_FILE_TYPES if filename.endswith(f'.{ext}')),
        None,
    )
    if not file_type:
        logger.warning("Unsupported file type uploaded: %s", filename)
        return render(request, 'analytics_app/upload.html', {
            'error': f'Unsupported file type. Allowed types: {", ".join(settings.ALLOWED_FILE_TYPES)}'
        })

    if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
        logger.warning("File too large: %s (%d bytes)", filename, uploaded_file.size)
        return render(request, 'analytics_app/upload.html', {
            'error': f'File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / (1024 * 1024):.0f} MB.'
        })

    if uploaded_file.size == 0:
        logger.warning("Empty file uploaded: %s", filename)
        return render(request, 'analytics_app/upload.html', {'error': 'The uploaded file is empty.'})

    try:
        # Convert JSON / XLSX → CSV in memory before saving
        if file_type in ['json', 'xlsx']:
            try:
                uploaded_file.seek(0)
                if file_type == 'json':
                    data = json.load(uploaded_file)
                    if isinstance(data, dict):
                        if len(data) == 1 and isinstance(list(data.values())[0], list):
                            data = list(data.values())[0]
                        else:
                            data = [data]
                    from io import StringIO
                    buf = StringIO()
                    writer = csv.DictWriter(buf, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                    csv_content = buf.getvalue()

                elif file_type == 'xlsx':
                    df = pd.read_excel(uploaded_file, engine='openpyxl')
                    if df is None or df.empty:
                        raise ValueError("Converted file contains no data.")
                    from io import StringIO
                    buf = StringIO()
                    df.to_csv(buf, index=False)
                    csv_content = buf.getvalue()

                if not csv_content or not csv_content.strip():
                    raise ValueError("Failed to generate CSV content.")

                from django.core.files.base import ContentFile
                base_name = uploaded_file.name.rsplit('.', 1)[0]
                uploaded_file = ContentFile(
                    csv_content.encode('utf-8'),
                    name=f'{base_name}.csv',
                )
                file_type = 'csv'
                logger.info("Converted %s to CSV successfully.", filename)

            except Exception as e:
                logger.error("Error converting %s to CSV: %s", filename, e, exc_info=True)
                return render(request, 'analytics_app/upload.html',
                              {'error': f'Error converting file to CSV: {str(e)}'})

        obj = UploadedFile.objects.create(
            file=uploaded_file,
            file_type=file_type,
            user=request.user if request.user.is_authenticated else None,
        )
        logger.info("File %d (%s) uploaded by user %s.", obj.id, filename,
                    request.user.id if request.user.is_authenticated else 'anonymous')

        from ..tasks import process_uploaded_file
        try:
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                process_uploaded_file.apply(args=(obj.id,))
                logger.info("File %d processed eagerly.", obj.id)
            else:
                process_uploaded_file.delay(obj.id)
                logger.info("File %d queued for background processing.", obj.id)
        except Exception as e:
            logger.error("Error queuing file %d: %s", obj.id, e, exc_info=True)
            obj.error_message = str(e)
            obj.save()
            return render(request, 'analytics_app/upload.html',
                          {'error': f'Unexpected error: {str(e)}'})

        messages.success(request, 'File uploaded successfully! Processing has started…')
        return redirect(reverse('result', kwargs={'file_id': obj.id}))

    except Exception as e:
        logger.error("Unexpected error during upload: %s", e, exc_info=True)
        return render(request, 'analytics_app/upload.html', {'error': f'Unexpected error: {str(e)}'})


@login_required
def delete_file_view(request, file_id):
    """
    Delete an uploaded file.  Only the owning user (or staff) may do this.
    Requires a POST request.
    """
    if request.user.is_staff or request.user.is_superuser:
        file_obj = get_object_or_404(UploadedFile, id=file_id)
    else:
        file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    if request.method == 'POST':
        try:
            file_path = file_obj.file.path
            if os.path.exists(file_path):
                os.remove(file_path)
            file_obj.delete()
            messages.success(request, 'File deleted successfully.')
        except Exception as e:
            logger.error("Error deleting file %d: %s", file_id, e, exc_info=True)
            messages.error(request, 'Error deleting file.')
        return redirect('my_uploads')
    return redirect('my_uploads')


@login_required
def reanalyze_file_view(request, file_id):
    """Reset processing state and re-queue background analysis."""
    if request.user.is_staff or request.user.is_superuser:
        file_obj = get_object_or_404(UploadedFile, id=file_id)
    else:
        file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    file_obj.processed = False
    file_obj.error_message = None
    file_obj.save()

    from ..tasks import process_uploaded_file
    try:
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            process_uploaded_file.apply(args=(file_obj.id,))
        else:
            process_uploaded_file.delay(file_obj.id)
        messages.success(request, 'File re-analysis started successfully!')
    except Exception as e:
        messages.error(request, f'Error re-analyzing file: {str(e)}')

    return redirect(reverse('result', kwargs={'file_id': file_id}))
