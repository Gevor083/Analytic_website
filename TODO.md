# TODO — Analytic Website

## ✅ Completed
- [x] Split views.py (1 462 lines) into feature modules (auth, upload, result, api, export, admin)
- [x] Created `analytics_app/utils.py` — all shared helpers in one place (no more duplication)
- [x] Fixed ownership checks on `delete_file_view`, `result_view`, `api_analysis_results`, `export`, `pdf`
- [x] Fixed CELERY_BROKER_URL duplicate in settings.py
- [x] Fixed duplicate `from django.db import models` in models.py
- [x] UUID-based upload paths — no filename collisions between users
- [x] `logout_view` now POST-only (CSRF logout attack prevention)
- [x] Celery retry logic (3 retries, 10 s delay)
- [x] Pagination in `my_uploads_view` and `admin_dashboard_view` (25/50 per page)
- [x] AI-style text insights (missing values, outliers, correlations) on result page
- [x] Correlation matrix data added to result context (JSON for Chart.js heatmap)
- [x] `__str__` methods on both models
- [x] Enhanced Django admin (extra columns, filters, pagination, readonly fields)
- [x] Structured LOGGING config in settings.py
- [x] Comprehensive test suite (utils, upload, auth, ownership, API, pagination, health, models)
- [x] `docker-compose.yml` with web + celery + celery-beat + postgres + redis
- [x] `Dockerfile` for production builds

## 🔲 Next Steps
- [ ] Add `django-axes` for login rate limiting / brute-force protection
- [ ] Real-time progress bar for file processing (Celery + AJAX polling or Django Channels)
- [ ] Interactive Chart.js correlation heatmap with hover tooltips on result page
- [ ] Email verification on registration
- [ ] Password reset flow
- [ ] User profile / avatar page
- [ ] Chart.js fully replaces Matplotlib PNG charts on result page
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Nginx config for static files in production
