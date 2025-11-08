from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.pm_dashboard, name='pm_dashboard'),

    # Program Info
    path('program-info/', views.program_info, name='pm_program_info'),

    # Committee Management
    path('committees/', views.committee_management, name='pm_committee_management'),
    path('committees/add/', views.add_committee, name='pm_add_committee'),
    path('committees/edit/<int:committee_id>/', views.edit_committee, name='pm_edit_committee'),
    path('committees/delete/<int:committee_id>/', views.delete_committee, name='pm_delete_committee'),

    # Task Management
    path('tasks/', views.task_management, name='pm_task_management'),
    path('tasks/add/', views.add_task, name='pm_add_task'),
    path('tasks/edit/<int:task_id>/', views.edit_task, name='pm_edit_task'),
    path('tasks/delete/<int:task_id>/', views.delete_task, name='pm_delete_task'),

    # Activity Management
    path('activities/', views.activity_management, name='pm_activity_management'),
    path('activities/add/', views.add_activity, name='pm_add_activity'),

    # Reports
    path('reports/', views.reports, name='pm_reports'),

    # Notifications
    path('notifications/', views.notifications, name='pm_notifications'),
    path('notifications/mark-all-read/', views.mark_all_read, name='pm_mark_all_read'),

    # Supervisor Management
    path('supervisors/', views.supervisor_management, name='pm_supervisor_management'),
    path('supervisors/add/', views.add_supervisor, name='pm_add_supervisor'),
    path('supervisors/delete/<int:supervisor_id>/', views.delete_supervisor, name='pm_delete_supervisor'),

]