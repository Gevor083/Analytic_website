## Running the Project with Docker
## Running the Project with Docker
## Running the Project with Docker
## Running the Project with Docker
## Running the Project with Docker
## Running the Project with Docker

This project is containerized using Docker and Docker Compose for easy setup and deployment. Below are the instructions and requirements specific to this project:

### Project-Specific Docker Requirements
- **Python Version:** The Dockerfile uses `python:3.13-slim` as the base image.
- **Dependencies:** All Python dependencies are installed from `requirements.txt` inside a virtual environment (`.venv`).
- **Entrypoint:** The application is started via `entrypoint.sh`.

### Environment Variables
- The project supports environment variables via an `.env` file located at `./analytics_project/.env`.
- To enable environment variable loading, uncomment the `env_file` line in `docker-compose.yml`:
  ```yaml
  env_file: ./analytics_project/.env
  ```
- No required environment variables are specified in the Dockerfiles or compose file, but you may need to set Django or Celery settings in `.env` as needed for your deployment.

### Build and Run Instructions
1. **Build and Start the Application:**
   ```sh
   docker compose up --build
   ```
   This will build the image and start the Django application on port 8000.

2. **Access the Application:**
   - The Django app will be available at [http://localhost:8000](http://localhost:8000).

### Ports Exposed
- **python-app:**
  - Exposes port `8000` (mapped to host port `8000`).

### Special Configuration
- The application code and dependencies are installed in a Python virtual environment for isolation.
- The container runs as a non-root user (`appuser`) for improved security.
- If you need to add a database (e.g., PostgreSQL) or Redis, uncomment and configure the relevant sections in `docker-compose.yml`.
- Uploaded files are stored in the `uploads/` directory. If you want to persist uploads, consider mounting a volume in Docker Compose.

### Additional Notes
- The `.dockerignore` file is used to exclude unnecessary files (such as `.env`, `.git`, etc.) from the build context.
- The `entrypoint.sh` script is used to start the Django app and can be customized to also start Celery workers if needed.

---
*Update this section as you add new services or environment variables to the project.*
