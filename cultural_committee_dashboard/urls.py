from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.cultural_dashboard, name='cultural_dashboard'),

    # Committee Info
    path('committee-info/', views.committee_info, name='cultural_committee_info'),

    # Task Management
    path('tasks/', views.task_management, name='cultural_task_management'),
    path('tasks/add/', views.add_task, name='cultural_add_task'),
    path('tasks/edit/<int:task_id>/', views.edit_task, name='cultural_edit_task'),
    path('tasks/delete/<int:task_id>/', views.delete_task, name='cultural_delete_task'),
    path('tasks/<int:task_id>/sessions/', views.view_task_sessions, name='cultural_view_task_sessions'),
    path('sessions/<int:session_id>/toggle-completion/', views.toggle_session_completion, name='cultural_toggle_session_completion'),

    # Member Management
    path('members/', views.member_management, name='cultural_member_management'),
    path('members/add/', views.add_member, name='cultural_add_member'),

    # File Library
    path('files/', views.file_library, name='cultural_file_library'),
    path('files/upload/', views.upload_file, name='cultural_upload_file'),
    path('files/delete/<int:file_id>/', views.delete_file, name='cultural_delete_file'),

    # Discussions
    path('discussions/', views.discussions, name='cultural_discussions'),
    path('discussions/add/', views.add_discussion, name='cultural_add_discussion'),
    path('discussions/<int:discussion_id>/', views.discussion_detail, name='cultural_discussion_detail'),

    # Reports
    path('reports/', views.reports, name='cultural_reports'),
    path('reports/add/', views.add_report, name='cultural_add_report'),

    # Notifications
    path('notifications/', views.notifications, name='cultural_notifications'),
    path('notifications/mark-all-read/', views.mark_all_read, name='cultural_mark_all_read'),

    # Daily Phrases
    path('daily-phrases/', views.daily_phrases, name='cultural_daily_phrases'),
    path('daily-phrases/add/', views.add_daily_phrase, name='cultural_add_daily_phrase'),
    path('daily-phrases/edit/<int:phrase_id>/', views.edit_daily_phrase, name='cultural_edit_daily_phrase'),
    path('daily-phrases/delete/<int:phrase_id>/', views.delete_daily_phrase, name='cultural_delete_daily_phrase'),
    path('daily-phrases/toggle/<int:phrase_id>/', views.toggle_daily_phrase, name='cultural_toggle_daily_phrase'),
]