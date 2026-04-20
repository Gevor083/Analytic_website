from django.contrib import admin
from .models import UploadedFile, ProcessedData


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'short_filename', 'file_type', 'num_rows', 'size_kb', 'processed', 'uploaded_at')
    list_filter = ('file_type', 'processed', 'uploaded_at')
    search_fields = ('user__username', 'file')
    readonly_fields = ('uploaded_at', 'size', 'num_rows', 'processed', 'error_message')
    ordering = ('-uploaded_at',)
    list_per_page = 50

    @admin.display(description='File Name')
    def short_filename(self, obj):
        return obj.file.name.split('/')[-1] if obj.file else '(none)'

    @admin.display(description='Size (KB)')
    def size_kb(self, obj):
        return f"{obj.size / 1024:.1f}" if obj.size else '0'


@admin.register(ProcessedData)
class ProcessedDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaded_file', 'column_name', 'data_type', 'value', 'created_at')
    list_filter = ('data_type', 'created_at')
    search_fields = ('uploaded_file__file', 'column_name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 50
