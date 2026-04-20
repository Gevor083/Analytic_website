"""
analytics_app/views/__init__.py

Re-exports every view callable from the feature sub-modules so that
  - analytics_app/urls.py (which does `from . import views`) works unchanged
  - any `from analytics_app.views import <name>` import continues to work
"""

from .auth_views import (
    login_view,
    logout_view,
    register_view,
    face_login_view,
    set_theme,
)

from .upload_views import (
    upload_view,
    delete_file_view,
    reanalyze_file_view,
)

from .result_views import (
    result_view,
    full_data_view,
    generate_chart_view,
    missing_values_chart_view,
    chart_data_api,
)

from .admin_views import (
    home_view,
    admin_dashboard_view,
    my_uploads_view,
    health_check,
    api_file_status,
)

from .api_views import (
    api_analysis_results,
    api_all_files,
)

from .export_views import (
    generate_pdf_report_view,
    export_results_view,
)

__all__ = [
    # auth
    'login_view', 'logout_view', 'register_view', 'face_login_view', 'set_theme',
    # upload
    'upload_view', 'delete_file_view', 'reanalyze_file_view',
    # result / charts
    'result_view', 'full_data_view', 'generate_chart_view',
    'missing_values_chart_view', 'chart_data_api',
    # admin / misc
    'home_view', 'admin_dashboard_view', 'my_uploads_view', 'health_check', 'api_file_status',
    # api
    'api_analysis_results', 'api_all_files',
    # export
    'generate_pdf_report_view', 'export_results_view',
]
