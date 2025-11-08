from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.operations_dashboard, name='operations_dashboard'),

    # Committee Info
    path('committee-info/', views.committee_info, name='operations_committee_info'),

    # Task Management
    path('tasks/', views.task_management, name='operations_task_management'),
    path('tasks/add/', views.add_task, name='operations_add_task'),
    path('tasks/edit/<int:task_id>/', views.edit_task, name='operations_edit_task'),
    path('tasks/delete/<int:task_id>/', views.delete_task, name='operations_delete_task'),

    # Member Management
    path('members/', views.member_management, name='operations_member_management'),
    path('members/add/', views.add_member, name='operations_add_member'),

    # Logistics Management
    path('logistics/', views.logistics_management, name='operations_logistics_management'),
    path('logistics/add/', views.add_resource, name='operations_add_resource'),
    path('logistics/edit/<int:resource_id>/', views.edit_resource, name='operations_edit_resource'),
    path('logistics/delete/<int:resource_id>/', views.delete_resource, name='operations_delete_resource'),

    # File Library
    path('files/', views.file_library, name='operations_file_library'),
    path('files/upload/', views.upload_file, name='operations_upload_file'),
    path('files/delete/<int:file_id>/', views.delete_file, name='operations_delete_file'),

    # Reports
    path('reports/', views.reports, name='operations_reports'),
    path('reports/add/', views.add_report, name='operations_add_report'),

    # Notifications
    path('notifications/', views.notifications, name='operations_notifications'),
    path('notifications/mark-all-read/', views.mark_all_read, name='operations_mark_all_read'),
]