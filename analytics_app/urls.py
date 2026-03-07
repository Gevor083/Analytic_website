from django.urls import path
from . import views
from .views import health_check

urlpatterns = [
    path('', views.home_view, name='home'),
    path('upload/', views.upload_view, name='upload'),
    path('result/<int:file_id>/', views.result_view, name='result'),
    path('my_uploads/', views.my_uploads_view, name='my_uploads'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('moderator_dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('delete_file/<int:file_id>/', views.delete_file_view, name='delete_file'),
    path('chart/<int:file_id>/', views.generate_chart_view, name='generate_chart'),
    path('missing_values_chart/<int:file_id>/', views.missing_values_chart_view, name='missing_values_chart'),
    path('reanalyze_file/<int:file_id>/', views.reanalyze_file_view, name='reanalyze_file'),
    path('health/', health_check, name='health_check'),
    path('api/results/<int:file_id>/', views.api_analysis_results, name='api_analysis_results'),
    path('api/files/', views.api_all_files, name='api_all_files'),
    path('generate_pdf_report/<int:file_id>/', views.generate_pdf_report_view, name='generate_pdf_report'),
    path('export/<int:file_id>/', views.export_results_view, name='export_results'),
    path('full_data/<int:file_id>/', views.full_data_view, name='full_data'),
    path('face-login/', views.face_login_view, name='face_login'),
    path('set_theme/', views.set_theme, name='set_theme'),
    path('api/chart_data/<int:file_id>/', views.chart_data_api, name='chart_data_api'),
]
