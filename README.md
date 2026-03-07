# Analytics Website

A comprehensive Django-based web application for data analytics, featuring modern UI drag-and-drop file uploads, automated background data analysis via Celery, interactive Client-Side chart generation (Chart.js), and a secure face recognition-based admin login system.

## 🚀 Key Features

### Core Functionality
- **Modern Drag & Drop File Uploads**: Upload CSV, JSON, or XLSX files using a smart, interactive drop zone.
- **Asynchronous Data Analysis**: Heavy Pandas statistical calculations (IQRs, Outliers) are delegated to Celery Workers to prevent server blocking.
- **Data Visualization**: Generate lightning-fast interactive canvas charts and graphs using **Chart.js** on the client side (zero-RAM footprint).
- **Interactive DataTables**: Preview up to 50 rows of sanitized data utilizing client-side searching, sorting, and pagination without reloading.
- **Bento-Box Dashboards**: Clean, modern component dashboards displaying Min, Max, Mean, Missing arrays, and Data Types.
- **Native Dark Mode**: A synchronized backend session architecture ensures dark-mode requests are saved and loaded purely unconditionally from the server, eliminating UI flashing.
- **Export Capabilities**: Export analysis results and dynamically generated charts to high-quality PDF reports.

### Security
- **Face Recognition Login**: Secure admin authentication using live webcam integration mappings.
- **CSRF & Sessions**: Secure session management intercepting malicious cross-site headers.
- **Strict File Normalization**: Safely captures JSON/XLSX structures, mapping them strictly to memory-buffered CSV outputs.
- **HTTPS/SSL ready** for webcam streaming accesses.

## 🛠 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL (recommended) or SQLite
- Redis (Required for celery asynchronous task processing)
- Webcam (Required for face recognition features)

### Windows Setup (Special Requirements for Face Recognition)
Due to dependencies on dlib and CMake, follow these steps carefully:

1. **Install CMake**:
   Download and install CMake from https://cmake.org/download/

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

## 💻 Usage

### Starting the Application
```bash
# 1. Start the Redis Server (Ensure Redis is running on port 6379)
# 2. Start the Celery Queue
celery -A analytics_project worker --loglevel=info -P gevent 

# 3. Start the Web Server
python manage.py runserver
```
Access the application at `http://localhost:8000`

### Face Login
- Navigate to `/face-login/`
- Allow camera access in your browser
- Position your face properly inside the camera bounding boxes
- Click "Capture Image" then "Login"

## 📁 Project Structure

```text
analytic_website/
├── analytics_app/              # Main Django app
│   ├── static/analytics_app/   # Scripts, custom components.css, and base styling
│   ├── templates/              # HTML templates (Bootstrap 5, Chart.js integrations)
│   ├── tasks.py                # Celery worker calculations
│   └── views.py                # Thin HTTP routers and /api/ microservices
├── analytics_project/          # Django settings, WSGI, ASGI context
├── faces/                      # Encrypted reference imagery
├── uploads/                    # User uploaded raw files
├── explanations/               # Markdown developer architecture guides
└── requirements.txt            # Python dependencies lists
```

## 🌐 JSON API Endpoints
The platform utilizes headless endpoints for rich front-end rendering:
- `GET /api/chart_data/<file_id>/?chart_type=pie` - Retrieves JSON data packets parsed perfectly for Chart.js.
- `POST /set_theme/` - Changes session-level CSS theming dynamically.
- `GET /api/results/<file_id>/` - Gets raw analytic JSON arrays.

## 🤝 Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing_chart`)
3. Write thin views and test locally via `python manage.py test`
4. Commit & push
5. Open a Pull Request

## ⚖️ License
This project is licensed under the MIT License - see the LICENSE file for details.
