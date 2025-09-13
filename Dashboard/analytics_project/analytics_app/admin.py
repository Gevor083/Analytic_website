from django.contrib import admin
from .models import UploadedFile, ProcessedData

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'file', 'uploaded_at', 'file_type')
    list_filter = ('user', 'file_type', 'uploaded_at')
    search_fields = ('user__username', 'file')

@admin.register(ProcessedData)
class ProcessedDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaded_file', 'column_name', 'value')
    list_filter = ('uploaded_file', 'column_name')
    search_fields = ('uploaded_file__file', 'column_name')
