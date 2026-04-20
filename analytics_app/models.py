from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
import os
import json


def validate_file_size(value):
    if value.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(
            f'File size cannot exceed {settings.MAX_UPLOAD_SIZE / (1024 * 1024):.0f} MB.'
        )


def validate_file_type(value):
    ext = os.path.splitext(value.name)[1][1:].lower()
    if ext not in settings.ALLOWED_FILE_TYPES:
        raise ValidationError(
            f'Unsupported file type. Allowed types: {", ".join(settings.ALLOWED_FILE_TYPES)}'
        )


def get_upload_path(instance, filename):
    """
    Generate a collision-safe upload path using UUID so two users uploading
    a file with the same name do not overwrite each other.
    Path format:  <user_id|anon>/<uuid4hex>.<ext>
    """
    import uuid
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'bin'
    uid = uuid.uuid4().hex
    user_dir = str(instance.user_id) if instance.user_id else 'anon'
    return os.path.join(user_dir, f"{uid}.{ext}")


class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(
        upload_to=get_upload_path,
        validators=[validate_file_size, validate_file_type],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    file_type = models.CharField(max_length=20, default='csv')
    processed = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    size = models.BigIntegerField(default=0)
    processed_chart_data = models.JSONField(default=dict)
    numeric_fields = models.JSONField(default=list)
    num_rows = models.BigIntegerField(default=0)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', '-uploaded_at']),
            models.Index(fields=['file_type']),
        ]

    def save(self, *args, **kwargs):
        if self.file:
            try:
                self.size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.file.name.split('/')[-1] if self.file else '(no file)'
        return f"UploadedFile #{self.id} – {name} (user={self.user}, rows={self.num_rows})"


class ProcessedData(models.Model):
    uploaded_file = models.ForeignKey(
        UploadedFile, on_delete=models.CASCADE, related_name='processed_data'
    )
    column_name = models.CharField(max_length=255, db_index=True)
    data_type = models.CharField(max_length=50, default='unknown')
    value = models.FloatField()
    stats = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['uploaded_file', 'column_name']),
        ]
        unique_together = ['uploaded_file', 'column_name']

    def save(self, *args, **kwargs):
        if isinstance(self.stats, str):
            try:
                self.stats = json.loads(self.stats)
            except Exception:
                self.stats = {}
        if self.stats is None:
            self.stats = {}
        if not isinstance(self.stats, dict):
            try:
                self.stats = dict(self.stats)
            except Exception:
                self.stats = {}
        super().save(*args, **kwargs)

    def __str__(self):
        return f"ProcessedData – file #{self.uploaded_file_id}, col='{self.column_name}'"
