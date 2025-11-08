from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.scientific_dashboard, name='scientific_dashboard'),

    # Committee Info
    path('committee-info/', views.committee_info, name='scientific_committee_info'),

    # Task Management
    path('tasks/', views.task_management, name='scientific_task_management'),
    path('tasks/add/', views.add_task, name='scientific_add_task'),
    path('tasks/edit/<int:task_id>/', views.edit_task, name='scientific_edit_task'),
    path('tasks/delete/<int:task_id>/', views.delete_task, name='scientific_delete_task'),

    # Member Management
    path('members/', views.member_management, name='scientific_member_management'),
    path('members/add/', views.add_member, name='scientific_add_member'),

    # File Library
    path('files/', views.file_library, name='scientific_file_library'),
    path('files/upload/', views.upload_file, name='scientific_upload_file'),
    path('files/delete/<int:file_id>/', views.delete_file, name='scientific_delete_file'),

    # Lecture Management
    path('lectures/', views.lecture_management, name='scientific_lecture_management'),
    path('lectures/add/', views.add_lecture, name='scientific_add_lecture'),
    path('lectures/edit/<int:lecture_id>/', views.edit_lecture, name='scientific_edit_lecture'),
    path('lectures/delete/<int:lecture_id>/', views.delete_lecture, name='scientific_delete_lecture'),
    path('lectures/attendance/<int:lecture_id>/', views.lecture_attendance, name='scientific_lecture_attendance'),

    # Reports
    path('reports/', views.reports, name='scientific_reports'),
    path('reports/add/', views.add_report, name='scientific_add_report'),

    # Notifications
    path('notifications/', views.notifications, name='scientific_notifications'),
    path('notifications/mark-all-read/', views.mark_all_read, name='scientific_mark_all_read'),
]