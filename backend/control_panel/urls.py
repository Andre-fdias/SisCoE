# control_panel/urls.py
from django.urls import path
from . import views

app_name = 'control_panel'

urlpatterns = [
    # Páginas principais
    path('', views.dashboard, name='dashboard'),
    path('services/', views.services_view, name='services'),
    path('logs/', views.logs_view, name='logs'),
    path('performance/', views.performance_view, name='performance'),
    path('containers/', views.containers_view, name='containers'),
    path('settings/', views.settings_view, name='settings'),
    
    # API Endpoints
    path('api/health/', views.api_health, name='api_health'),
    path('api/metrics/', views.api_metrics, name='api_metrics'),
    path('api/services/', views.api_services, name='api_services'),
    path('api/containers/', views.api_containers, name='api_containers'),
    
    # Ações
    path('api/restart-service/', views.api_restart_service, name='api_restart_service'),
    path('api/restart-container/', views.api_restart_container, name='api_restart_container'),
    path('api/clear-cache/', views.api_clear_cache, name='api_clear_cache'),
    path('api/send-test-email/', views.api_send_test_email, name='api_send_test_email'),
    path('api/run-health-check/', views.api_run_health_check, name='api_run_health_check'),
    path('api/backup-database/', views.api_backup_database, name='api_backup_database'),
]# backend/control_panel/urls.py
from django.urls import path
from . import views

app_name = 'control_panel'

urlpatterns = [
    # Páginas principais
    path('', views.dashboard, name='dashboard'),
    path('services/', views.services_view, name='services'),
    path('logs/', views.logs_view, name='logs'),
    path('performance/', views.performance_view, name='performance'),
    path('containers/', views.containers_view, name='containers'),
    path('settings/', views.settings_view, name='settings'),
    
    # API Endpoints
    path('api/health/', views.api_health, name='api_health'),
    path('api/metrics/', views.api_metrics, name='api_metrics'),
    path('api/services/', views.api_services, name='api_services'),
    path('api/containers/', views.api_containers, name='api_containers'),
    
    # Ações
    path('api/restart-service/', views.api_restart_service, name='api_restart_service'),
    path('api/restart-container/', views.api_restart_container, name='api_restart_container'),
    path('api/clear-cache/', views.api_clear_cache, name='api_clear_cache'),
    path('api/send-test-email/', views.api_send_test_email, name='api_send_test_email'),
    path('api/run-health-check/', views.api_run_health_check, name='api_run_health_check'),
    path('api/backup-database/', views.api_backup_database, name='api_backup_database'),
]