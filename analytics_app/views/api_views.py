"""
API views: /api/results/<id>/, /api/files/
"""

import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from ..models import ProcessedData, UploadedFile

logger = logging.getLogger(__name__)


@login_required
def api_analysis_results(request, file_id):
    """Return full analysis results for a single file as JSON."""
    if request.user.is_staff or request.user.is_superuser:
        file_obj = get_object_or_404(UploadedFile, id=file_id)
    else:
        file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    if not file_obj.processed:
        return JsonResponse({'message': 'File is still being processed.'}, status=202)

    if file_obj.error_message:
        return JsonResponse({'error': f'Error processing file: {file_obj.error_message}'}, status=500)

    file_data = {
        'id': file_obj.id,
        'file_name': file_obj.file.name.split('/')[-1],
        'uploaded_at': file_obj.uploaded_at.isoformat(),
        'file_type': file_obj.file_type,
        'processed': file_obj.processed,
        'error_message': file_obj.error_message,
        'num_rows': file_obj.num_rows,
        'file_size': file_obj.size,
        'processed_chart_data': file_obj.processed_chart_data,
        'numeric_fields': file_obj.numeric_fields,
    }

    analysis_results = [
        {
            'column_name': pd_obj.column_name,
            'data_type': pd_obj.data_type,
            'stats': pd_obj.stats,
        }
        for pd_obj in ProcessedData.objects.filter(uploaded_file=file_obj)
    ]

    return JsonResponse({'file_info': file_data, 'analysis_results': analysis_results})


@login_required
def api_all_files(request):
    """Return JSON list of all files uploaded by the current user."""
    files = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')

    files_data = [
        {
            'id': f.id,
            'file_name': f.file.name.split('/')[-1],
            'uploaded_at': f.uploaded_at.isoformat(),
            'file_type': f.file_type,
            'processed': f.processed,
            'error_message': f.error_message,
            'num_rows': f.num_rows,
            'file_size': f.size,
        }
        for f in files
    ]

    return JsonResponse({'files': files_data})
