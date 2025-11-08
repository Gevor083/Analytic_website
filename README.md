# Analytics Website

A comprehensive Django-based web application for data analytics, featuring file upload, automated data analysis, chart generation, and secure face recognition-based admin login.

## Features

### Core Functionality
- **File Upload & Analysis**: Upload CSV, JSON, or XLSX files for automated data analysis
- **Data Visualization**: Generate interactive charts and graphs using Plotly
- **Statistical Analysis**: Comprehensive data insights including correlations, distributions, and missing value analysis
- **Export Capabilities**: Export analysis results to PDF reports
- **User Management**: Registration, login, and user-specific file management
- **API Endpoints**: RESTful API for programmatic access to analysis results

### Advanced Features
- **Face Recognition Login**: Secure admin authentication using facial recognition
- **Background Processing**: Asynchronous task processing with Celery
- **Caching**: Redis-based caching for improved performance
- **Database Support**: PostgreSQL (production) or SQLite (development)
- **Responsive Design**: Mobile-friendly interface with Bootstrap styling

### Security
- Face-based admin login with webcam integration
- CSRF protection and secure session management
- File upload validation and size limits
- HTTPS support for camera access

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL (recommended) or SQLite
- Redis (optional, for caching)
- Webcam (for face recognition login)

### Windows Setup (Special Requirements for Face Recognition)
Due to dependencies on dlib and CMake, follow these steps carefully:

1. **Install CMake**:
   ```bash
   # Download and install CMake from https://cmake.org/download/
   # Or use the provided MSI/ZIP in the project directory
   ```

2. **Install dlib**:
   ```bash
   # Navigate to your dlib installation directory (e.g., dlib-20.0)
   python dlib-20.0/setup.py install
   ```

3. **Clone and Setup Project**:
   ```bash
   git clone <repository-url>
   cd analytic_website
   python -m venv venv
   venv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   ```

### Linux/Mac Setup
```bash
git clone <repository-url>
cd analytic_website
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Configuration
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/analytics_db
REDIS_LOCATION=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
```

### Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser
```

### Register Admin Face (for Face Login)
```bash
python manage.py register_face <admin_username>
```
Follow the prompts to capture your face using the webcam.

## Usage

### Starting the Application
```bash
python manage.py runserver
```
Access the application at `http://localhost:8000`

### Face Login
- Navigate to `/face-login/`
- Allow camera access in your browser
- Position your face in the camera view
- Click "Capture Image" then "Login"

### File Analysis Workflow
1. Register/Login as a regular user
2. Upload a data file (CSV, JSON, XLSX)
3. View analysis results and generated charts
4. Export results or re-analyze data

### Background Tasks
Start Celery worker for background processing:
```bash
celery -A analytics_project worker --loglevel=info
```

## Project Structure

```
analytic_website/
├── analytics_app/              # Main Django app
│   ├── management/commands/    # Custom management commands
│   ├── migrations/             # Database migrations
│   ├── static/                 # Static files (CSS, JS)
│   ├── templates/              # HTML templates
│   ├── tasks.py                # Celery tasks
│   ├── views.py                # View functions
│   └── models.py               # Database models
├── analytics_project/          # Django project settings
├── faces/                      # Face recognition reference images
├── uploads/                    # User uploaded files
├── test materials/             # Sample data files
├── explanations/               # Documentation and tutorials
└── requirements.txt            # Python dependencies
```

## API Endpoints

### Analysis Results
- `GET /api/results/<file_id>/` - Get analysis results for a file
- `GET /api/files/` - List all user files

### Authentication
- `POST /login/` - User login
- `POST /register/` - User registration
- `GET /face-login/` - Face recognition login page

## Testing

Run the test suite:
```bash
python manage.py test
```

## Deployment

### Production Setup
1. Set `DEBUG=False` in settings
2. Configure PostgreSQL database
3. Set up Redis for caching
4. Use gunicorn for serving:
   ```bash
   gunicorn analytics_project.wsgi:application --bind 0.0.0.0:8000
   ```
5. Set up reverse proxy (nginx) for static files and SSL

### Docker Support
The application can be containerized using Docker. Ensure all dependencies are properly configured in the Dockerfile.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Face Recognition Issues
- Ensure CMake and dlib are properly installed
- Check webcam permissions in browser
- Verify face images are clear and well-lit

### Database Connection
- Confirm DATABASE_URL in .env file
- Run migrations: `python manage.py migrate`

### Performance
- Enable Redis caching for better performance
- Use PostgreSQL in production
- Monitor Celery tasks for background processing

## Support

For issues and questions, please create an issue in the GitHub repository or contact the development team.
