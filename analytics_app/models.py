from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
import os
import json

def validate_file_size(value):
    if value.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(f'File size cannot exceed {settings.MAX_UPLOAD_SIZE/(1024*1024)}MB')

def validate_file_type(value):
    ext = os.path.splitext(value.name)[1][1:].lower()
    if ext not in settings.ALLOWED_FILE_TYPES:
        raise ValidationError(f'Unsupported file type. Allowed types: {", ".join(settings.ALLOWED_FILE_TYPES)}')

class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(
        # Store files directly under MEDIA_ROOT (uploads/) so files are not nested
        upload_to='',
        validators=[validate_file_size, validate_file_type]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    file_type = models.CharField(max_length=20, default='csv')
    processed = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    size = models.BigIntegerField(default=0)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', '-uploaded_at']),
            models.Index(fields=['file_type']),
        ]

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

class ProcessedData(models.Model):
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='processed_data')
    column_name = models.CharField(max_length=255, db_index=True)
    value = models.FloatField()
    stats = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['uploaded_file', 'column_name']),
        ]
        unique_together = ['uploaded_file', 'column_name']

    def save(self, *args, **kwargs):
        # Coerce stats to a dictionary if it's a JSON string or other unexpected type
        if isinstance(self.stats, str):
            try:
                self.stats = json.loads(self.stats)
            except Exception:
                self.stats = {}
        if self.stats is None:
            self.stats = {}
        try:
            # Ensure it's a plain dict (JSONField accepts mappings but keep consistent)
            if not isinstance(self.stats, dict):
                self.stats = dict(self.stats)
        except Exception:
            self.stats = {}
        super().save(*args, **kwargs)
