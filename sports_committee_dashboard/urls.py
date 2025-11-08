from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.sports_dashboard, name='sports_dashboard'),

    # Committee Info
    path('committee-info/', views.committee_info, name='sports_committee_info'),

    # Task Management
    path('tasks/', views.task_management, name='sports_task_management'),
    path('tasks/add/', views.add_task, name='sports_add_task'),
    path('tasks/edit/<int:task_id>/', views.edit_task, name='sports_edit_task'),
    path('tasks/delete/<int:task_id>/', views.delete_task, name='sports_delete_task'),

    # Member Management
    path('members/', views.member_management, name='sports_member_management'),
    path('members/add/', views.add_member, name='sports_add_member'),

    # File Library
    path('files/', views.file_library, name='sports_file_library'),
    path('files/upload/', views.upload_file, name='sports_upload_file'),
    path('files/delete/<int:file_id>/', views.delete_file, name='sports_delete_file'),

    # Match Management
    path('matches/', views.match_management, name='sports_match_management'),
    path('matches/add/', views.add_match, name='sports_add_match'),
    path('matches/edit/<int:match_id>/', views.edit_match, name='sports_edit_match'),
    path('matches/delete/<int:match_id>/', views.delete_match, name='sports_delete_match'),

    # Reports
    path('reports/', views.reports, name='sports_reports'),
    path('reports/add/', views.add_report, name='sports_add_report'),

    # Notifications
    path('notifications/', views.notifications, name='sports_notifications'),
    path('notifications/mark-all-read/', views.mark_all_read, name='sports_mark_all_read'),
]