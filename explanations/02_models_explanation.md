# Database Models Explanation

## UploadedFile Model

```python
class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to=get_upload_path, validators=[validate_file_size, validate_file_type])
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    file_type = models.CharField(max_length=20, default='csv')
    processed = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    size = models.BigIntegerField(default=0)
```

### Field Explanations:
- `user`: Links to Django's built-in User model. Can be null for anonymous uploads.
- `file`: Stores the uploaded file. Uses custom path and validators.
- `uploaded_at`: Timestamp of upload, indexed for faster queries.
- `file_type`: Type of file (csv, json, sql).
- `processed`: Indicates if file has been processed.
- `error_message`: Stores any processing errors.
- `size`: File size in bytes.

### Validators:
1. `validate_file_size`:
   - Checks if file size is within limits
   - Limit set in settings.MAX_UPLOAD_SIZE

2. `validate_file_type`:
   - Verifies file extension
   - Allowed types in settings.ALLOWED_FILE_TYPES

## ProcessedData Model

```python
class ProcessedData(models.Model):
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    column_name = models.CharField(max_length=255)
    value = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    stats = models.JSONField(default=dict)
```

### Field Explanations:
- `uploaded_file`: Links to the original uploaded file
- `column_name`: Name of the analyzed column
- `value`: Calculated numerical result
- `created_at`: When the analysis was completed
- `stats`: JSON field for flexible statistics storage

## Model Relationships

1. **User -> UploadedFile**
   - One-to-Many relationship
   - One user can have multiple uploads
   - Cascade deletion: files deleted when user is deleted

2. **UploadedFile -> ProcessedData**
   - One-to-Many relationship
   - One file can have multiple processed results
   - Cascade deletion: results deleted when file is deleted

## Database Optimizations

1. **Indexes**
   ```python
   class Meta:
       ordering = ['-uploaded_at']
       indexes = [
           models.Index(fields=['user', '-uploaded_at']),
           models.Index(fields=['file_type']),
       ]
   ```

2. **Query Optimization**
   - Indexed fields for faster searches
   - Ordering by upload date for efficient pagination
   - Composite index for user-based queries