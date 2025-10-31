# Docker development setup

This project includes a simple Docker setup to run the Django web app, Postgres and Redis, and a Celery worker.

Files added:
- `Dockerfile` – builds the Django app image
- `docker-compose.yml` – starts `db` (Postgres), `redis`, `web` (Django) and `worker` (Celery)
- `.dockerignore` – excludes local files from the image
- `requirements.txt` – Python dependencies for the image

Quick start (from `analytics_project` folder):

1. Ensure your `.env` has correct values for DB_* and other variables. Example values are already present in `analytics_project/.env` – update them if needed.

2. Build and start services:
```bash
docker compose up --build
```

3. The web app will be available at http://localhost:8000. Logs will stream to your terminal.

Notes:
- The compose file mounts the project directory and `uploads/` into the container so code changes are reflected immediately.
- By default the web command runs migrations automatically before starting the Django dev server. Adjust the `command` in `docker-compose.yml` if you prefer a different startup sequence.
- For production, replace `runserver` with a proper WSGI server (Gunicorn/uvicorn) and fine tune static file serving.
