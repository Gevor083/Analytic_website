# Project Configuration and Management

Let's examine the core configuration files:

## Manage.py
```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytics_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
```

## WSGI Configuration (wsgi.py)
```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytics_project.settings')
application = get_wsgi_application()
```

## ASGI Configuration (asgi.py)
```python
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytics_project.settings')
application = get_asgi_application()
```

## Celery Configuration (celery.py)
```python
import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytics_project.settings')

# Create celery application
app = Celery('analytics_project')

# Load task modules from all registered Django app configs
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()
```

## Command Line Tools

### Custom Management Commands

1. Fix Uploads Command (fix_uploads.py)
```python
from django.core.management.base import BaseCommand
from analytics_app.models import UploadedFile
import os

class Command(BaseCommand):
    help = 'Fix uploaded file locations'

    def handle(self, *args, **options):
        for file in UploadedFile.objects.all():
            # Fix file paths
            # Move files to correct location
            pass
```

2. Wait for DB Command (wait_for_db.py)
```python
from django.core.management.base import BaseCommand
import time

class Command(BaseCommand):
    help = 'Wait for database to be available'

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        time.sleep(2)
        self.stdout.write(self.style.SUCCESS('Database available!'))
```

## Project Structure
```
analytics_project/
├── manage.py           # Main management script
├── requirements.txt    # Project dependencies
├── README.md          # Project documentation
├── analytics_project/ # Main project folder
│   ├── __init__.py
│   ├── settings.py    # Project settings
│   ├── urls.py       # Main URL configuration
│   ├── celery.py     # Celery configuration
│   ├── wsgi.py       # WSGI configuration
│   └── asgi.py       # ASGI configuration
└── analytics_app/    # Main application
    ├── management/   # Custom commands
    ├── migrations/   # Database migrations
    ├── static/      # Static files
    ├── templates/   # HTML templates
    ├── __init__.py
    ├── admin.py     # Admin configuration
    ├── models.py    # Database models
    ├── views.py     # View functions
    ├── tasks.py     # Celery tasks
    └── tests.py     # Unit tests
```

## Key Configuration Features

1. **Project Settings**
   - Environment variables
   - Database configuration
   - Static/Media files
   - Security settings

2. **Application Structure**
   - Modular design
   - Clear separation
   - Easy maintenance

3. **Task Processing**
   - Celery integration
   - Background jobs
   - Async processing

4. **Development Tools**
   - Management commands
   - Database utilities
   - Debugging tools

## Command Line Usage

1. **Database Commands**
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

2. **Server Management**
```bash
# Run development server
python manage.py runserver

# Run Celery worker
celery -A analytics_project worker -l info
```

3. **Static Files**
```bash
# Collect static files
python manage.py collectstatic
```

4. **Custom Commands**
```bash
# Fix uploaded files
python manage.py fix_uploads

# Wait for database
python manage.py wait_for_db
```

## Deployment Considerations

1. **Environment Setup**
   - Production settings
   - Environment variables
   - Security measures

2. **Static Files**
   - Collection
   - Compression
   - CDN configuration

3. **Database**
   - Migration planning
   - Backup strategy
   - Performance tuning

4. **Security**
   - Debug mode off
   - Secret key protection
   - HTTPS configuration