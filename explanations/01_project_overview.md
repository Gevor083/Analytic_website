# Analytics Website Project Overview

## Project Structure
```
analytics_project/   # Main Django project folder
├── settings.py     # Project settings and configurations
├── urls.py        # Main URL routing
├── celery.py      # Celery configuration for background tasks
└── other config files...

analytics_app/      # Main application folder
├── models.py      # Database models
├── views.py       # View functions/controllers
├── tasks.py       # Background tasks
├── admin.py       # Admin interface configuration
├── templates/     # HTML templates
├── static/        # Static files (CSS, JS)
└── migrations/    # Database migrations
```

## Key Components

1. **User Management**
   - Registration
   - Login/Logout
   - User profiles
   - Admin dashboard

2. **File Upload System**
   - Supports CSV, JSON, SQL files
   - File validation
   - Size limit checks
   - File type verification

3. **Data Processing**
   - Asynchronous processing using Celery
   - Statistical analysis
   - Data visualization
   - Error handling

4. **Security Features**
   - User authentication
   - File validation
   - Size limits
   - Secure file storage

5. **Admin Features**
   - User management
   - File oversight
   - Processing status monitoring
   - Error tracking

## Technologies Used

1. **Backend**
   - Django (Web Framework)
   - Celery (Background Tasks)
   - Python (Programming Language)

2. **Frontend**
   - HTML/CSS
   - JavaScript
   - Bootstrap (UI Framework)
   - Font Awesome (Icons)

3. **Data Storage**
   - Database (SQLite/PostgreSQL)
   - File System Storage

## Main Features

1. **File Upload**
   - Users can upload data files
   - Automatic file type detection
   - Size validation
   - Progress tracking

2. **Data Processing**
   - Automated analysis
   - Statistical computations
   - Result generation
   - Error handling

3. **Result Visualization**
   - Data presentation
   - Download options
   - Error reporting

4. **User Management**
   - User registration
   - Authentication
   - Profile management
   - Admin controls