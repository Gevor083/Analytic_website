# Testing and Deployment Guide

## Running the Development Server

1. **Start the Development Server**
   ```bash
   python manage.py runserver
   ```
   - Access site at http://localhost:8000
   - Debug mode enabled
   - Auto-reload on code changes

2. **Start Celery Worker** (for background tasks)
   ```bash
   celery -A analytics_project worker -l info
   ```
   - Processes background tasks
   - Handles file processing
   - Real-time logging

## Testing

### Unit Tests
Located in `analytics_app/tests.py`:

```python
class FileUploadTests(TestCase):
    def test_file_upload():
        # Test file upload functionality
    
    def test_file_validation():
        # Test file validation

class ProcessingTests(TestCase):
    def test_csv_processing():
        # Test CSV processing

    def test_json_processing():
        # Test JSON processing
```

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific test
python manage.py test analytics_app.tests.FileUploadTests

# Run with coverage
coverage run manage.py test
coverage report
```

## Deployment Steps

1. **Environment Setup**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   
   # Install requirements
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. **Static Files**
   ```bash
   python manage.py collectstatic
   ```

4. **Security Settings**
   - Set DEBUG = False
   - Configure allowed hosts
   - Set secure SECRET_KEY
   - Enable HTTPS
   - Configure CSRF/XSS protection

## Production Deployment

### Using Docker
1. **Build Image**
   ```bash
   docker build -t analytics-website .
   ```

2. **Run Container**
   ```bash
   docker run -d -p 8000:8000 analytics-website
   ```

### Manual Deployment
1. Set up web server (nginx/Apache)
2. Configure WSGI
3. Set up SSL certificates
4. Configure database
5. Set up Celery worker

## Monitoring and Maintenance

1. **Log Monitoring**
   - Application logs
   - Server logs
   - Celery worker logs

2. **Performance Monitoring**
   - Database queries
   - File processing times
   - Server resources

3. **Regular Maintenance**
   - Database backups
   - Log rotation
   - Security updates
   - Code updates

## Troubleshooting

Common Issues and Solutions:

1. **File Upload Issues**
   - Check file permissions
   - Verify size limits
   - Check storage space

2. **Processing Errors**
   - Check Celery worker status
   - Verify file format
   - Check system resources

3. **Database Issues**
   - Check connections
   - Verify migrations
   - Monitor performance

4. **Server Issues**
   - Check logs
   - Monitor resources
   - Verify configurations