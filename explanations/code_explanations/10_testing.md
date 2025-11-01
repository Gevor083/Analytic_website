# Tests and Error Handling

Let's examine the testing and error handling components:

## Unit Tests (tests.py)
```python
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from .models import UploadedFile, ProcessedData

class FileUploadTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
    def test_file_upload(self):
        """Test file upload functionality"""
        # Login
        self.client.login(username='testuser', password='testpass123')
        
        # Create test file
        file_content = b'col1,col2\n1,2\n3,4'
        test_file = SimpleUploadedFile(
            "test.csv",
            file_content,
            content_type="text/csv"
        )
        
        # Upload file
        response = self.client.post('/upload/', {'file': test_file})
        
        # Check response
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Verify file was saved
        self.assertTrue(UploadedFile.objects.exists())
        
    def test_invalid_file_type(self):
        """Test file type validation"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create invalid file
        file_content = b'invalid content'
        test_file = SimpleUploadedFile(
            "test.txt",
            file_content,
            content_type="text/plain"
        )
        
        # Try to upload
        response = self.client.post('/upload/', {'file': test_file})
        
        # Check error response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Unsupported file type')

class ProcessingTests(TestCase):
    def setUp(self):
        # Create test data
        self.file_obj = UploadedFile.objects.create(
            file='test.csv',
            file_type='csv'
        )
    
    def test_csv_processing(self):
        """Test CSV processing logic"""
        # Process file
        from .tasks import process_uploaded_file
        process_uploaded_file(self.file_obj.id)
        
        # Check results
        self.file_obj.refresh_from_db()
        self.assertTrue(self.file_obj.processed)
        self.assertTrue(ProcessedData.objects.filter(
            uploaded_file=self.file_obj
        ).exists())
```

## Error Handling

### View Error Handling
```python
def upload_view(request):
    try:
        # File validation
        if not uploaded_file:
            raise ValidationError('No file was uploaded.')
        
        # Size check
        if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
            raise ValidationError(f'File too large. Maximum size is {settings.MAX_UPLOAD_SIZE/(1024*1024)}MB')
        
        # Process file
        obj = UploadedFile.objects.create(...)
        
    except ValidationError as e:
        return render(request, 'analytics_app/upload.html', 
                     {'error': str(e)})
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Upload error: {str(e)}")
        return render(request, 'analytics_app/upload.html',
                     {'error': 'An unexpected error occurred.'})
```

### Task Error Handling
```python
@shared_task
def process_uploaded_file(file_id):
    try:
        # Get file
        file_obj = UploadedFile.objects.get(id=file_id)
        
        # Process file
        results = process_file(file_obj)
        
        # Store results
        store_results(file_obj, results)
        
    except UploadedFile.DoesNotExist:
        logger.error(f"File {file_id} not found")
        raise
        
    except Exception as e:
        logger.error(f"Processing error for file {file_id}: {str(e)}")
        if file_obj:
            file_obj.error_message = str(e)
            file_obj.save()
        raise
```

## Logging Configuration
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'error.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'analytics_app': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Error Pages

### 404 Template
```html
{% extends 'analytics_app/base.html' %}

{% block content %}
<div class="error-page">
    <h1>404 - Page Not Found</h1>
    <p>The page you're looking for doesn't exist.</p>
    <a href="{% url 'index' %}" class="btn btn-primary">
        Return Home
    </a>
</div>
{% endblock %}
```

### 500 Template
```html
{% extends 'analytics_app/base.html' %}

{% block content %}
<div class="error-page">
    <h1>500 - Server Error</h1>
    <p>Something went wrong. Please try again later.</p>
    <a href="{% url 'index' %}" class="btn btn-primary">
        Return Home
    </a>
</div>
{% endblock %}
```

## Testing Best Practices

1. **Test Coverage**
   - Model tests
   - View tests
   - Form tests
   - Task tests

2. **Test Types**
   - Unit tests
   - Integration tests
   - Function tests
   - Security tests

3. **Test Data**
   - Fixtures
   - Factory Boy
   - Mock objects
   - Test utilities

4. **Error Scenarios**
   - Input validation
   - Edge cases
   - Error conditions
   - Recovery paths