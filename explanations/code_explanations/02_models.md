# Models.py Explanation

Let's examine `analytics_app/models.py`, which defines our database structure:

```python
# File validation functions
def validate_file_size(value):
    """
    Validates that uploaded files don't exceed maximum size
    Args:
        value: The uploaded file object
    Raises:
        ValidationError if file is too large
    """
    if value.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(f'File size cannot exceed {settings.MAX_UPLOAD_SIZE/(1024*1024)}MB')

def validate_file_type(value):
    """
    Validates file extensions against allowed types
    Args:
        value: The uploaded file object
    Raises:
        ValidationError if file type is not allowed
    """
    ext = os.path.splitext(value.name)[1][1:].lower()
    if ext not in settings.ALLOWED_FILE_TYPES:
        raise ValidationError(f'Unsupported file type. Allowed types: {", ".join(settings.ALLOWED_FILE_TYPES)}')

class UploadedFile(models.Model):
    """
    Stores information about uploaded files and their processing status
    """
    # Links to Django's built-in User model (optional link for anonymous uploads)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # The actual uploaded file
    file = models.FileField(
        upload_to='',  # Files stored directly in MEDIA_ROOT
        validators=[validate_file_size, validate_file_type]
    )
    
    # Metadata fields
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    file_type = models.CharField(max_length=20, default='csv')
    processed = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    size = models.BigIntegerField(default=0)

    class Meta:
        ordering = ['-uploaded_at']  # Newest files first
        indexes = [
            models.Index(fields=['user', '-uploaded_at']),  # For user's file lists
            models.Index(fields=['file_type']),  # For filtering by type
        ]

class ProcessedData(models.Model):
    """
    Stores the results of file processing
    """
    # Links to the original uploaded file
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    
    # Results data
    column_name = models.CharField(max_length=255)
    value = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    stats = models.JSONField(default=dict)  # Flexible statistics storage

## Model Relationships

1. User → UploadedFile
   - One user can have many uploaded files
   - Files are deleted when user is deleted (CASCADE)
   - Optional relationship (null=True) allows anonymous uploads

2. UploadedFile → ProcessedData
   - One file can have many processed results
   - Results are deleted when file is deleted (CASCADE)
   - Each result links to specific column and contains statistics

## Database Optimizations

1. Indexes
   - Uploaded files ordered by upload date
   - Composite index for user's file lists
   - File type index for filtering

2. Data Integrity
   - File validation before save
   - Automatic timestamp recording
   - Size tracking
   - Error message storage

3. Performance
   - Indexed fields for common queries
   - Efficient relationship traversal
   - JSON field for flexible data storage