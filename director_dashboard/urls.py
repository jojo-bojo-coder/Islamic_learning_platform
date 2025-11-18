from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('programs/', views.program_management, name='program_management'),
    path('programs/add/', views.add_program, name='add_program'),
    path('programs/edit/<int:program_id>/', views.edit_program, name='edit_program'),
    path('programs/delete/<int:program_id>/', views.delete_program, name='delete_program'),
    # User management URLs
    path('users/', views.user_management, name='user_management'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/toggle-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('users/activity/<int:user_id>/', views.user_activity_log, name='user_activity'),
    path('reports/', views.reports, name='reports'),

    # Albums URLs
    path('albums/', views.album_management, name='album_management'),
    path('albums/add/', views.add_album, name='add_album'),
    path('albums/edit/<int:album_id>/', views.edit_album, name='edit_album'),
    path('albums/delete/<int:album_id>/', views.delete_album, name='delete_album'),
    path('albums/<int:album_id>/', views.album_detail, name='album_detail'),
    path('albums/<int:album_id>/add-photo/', views.add_photo, name='add_photo'),
    path('photos/delete/<int:photo_id>/', views.delete_photo, name='delete_photo'),

    # File Library URLs
    path('files/', views.file_library, name='file_library'),
    path('files/upload/', views.upload_file, name='upload_file'),
    path('files/edit/<int:file_id>/', views.edit_file, name='edit_file'),
    path('files/delete/<int:file_id>/', views.delete_file, name='delete_file'),
    path('files/download/<int:file_id>/', views.download_file, name='download_file'),

    # Alerts URLs
    path('alerts/', views.alerts_management, name='alerts_management'),
    path('alerts/add/', views.add_alert, name='add_alert'),
    path('alerts/mark-read/<int:alert_id>/', views.mark_alert_read, name='mark_alert_read'),
    path('alerts/mark-all-read/', views.mark_all_alerts_read, name='mark_all_alerts_read'),
    path('alerts/delete/<int:alert_id>/', views.delete_alert, name='delete_alert'),

    path('reports/export-pdf/', views.export_reports_pdf, name='export_reports_pdf'),
    path('reports/export-excel/', views.export_reports_excel, name='export_reports_excel'),
]