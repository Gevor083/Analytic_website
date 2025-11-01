# Settings.py Explanation

Let's start with `analytics_project/settings.py`, which is the main configuration file:

```python
# Core Django Settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
# DEBUG controls development features. Set to False in production for security

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']
# List of hosts/domains this Django site can serve

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',     # Django admin interface
    'django.contrib.auth',      # Authentication system
    'django.contrib.contenttypes',  # Content type system
    'django.contrib.sessions',   # Session framework
    'django.contrib.messages',   # Messaging framework
    'django.contrib.staticfiles',  # Static file management
    'analytics_app',            # Our main application
]

# File Upload Settings
MAX_UPLOAD_SIZE = 30 * 1024 * 1024  # 30MB size limit
ALLOWED_FILE_TYPES = ['csv', 'json', 'sql']  # Allowed file extensions

# Media and Static Files
MEDIA_URL = '/uploads/'  # URL prefix for user-uploaded files
MEDIA_ROOT = BASE_DIR / 'uploads'  # Physical location of uploaded files
STATIC_URL = 'static/'  # URL prefix for static files (CSS, JS, etc.)

# Celery Settings
USE_REDIS = os.getenv('USE_REDIS', 'False').lower() == 'true'
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_EAGER', 'False').lower() == 'true'
# Celery configuration for background task processing
```

## Important Settings Explained

### File Upload Configuration
- `MAX_UPLOAD_SIZE`: Limits file size to 30MB
- `ALLOWED_FILE_TYPES`: Only allows CSV, JSON, and SQL files
- Files are stored in the 'uploads' directory

### Static and Media Files
- `MEDIA_URL`: How uploaded files are accessed in the browser
- `MEDIA_ROOT`: Where uploaded files are stored on disk
- `STATIC_URL`: How static files (CSS, JS) are accessed

### Security Settings
- `DEBUG`: Development mode, should be False in production
- `ALLOWED_HOSTS`: Restricts which domains can serve the site
- Default security middleware enabled

### Database Configuration
- Uses SQLite by default (defined in DATABASES setting)
- Can be configured for PostgreSQL in production

### Background Tasks
- Celery configured for async processing
- Can use Redis as message broker
- Development mode can run tasks synchronously