from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.sharia_dashboard, name='sharia_dashboard'),

    # Committee Info
    path('committee-info/', views.committee_info, name='sharia_committee_info'),

    # Task Management
    path('tasks/', views.task_management, name='sharia_task_management'),
    path('tasks/add/', views.add_task, name='sharia_add_task'),
    path('tasks/edit/<int:task_id>/', views.edit_task, name='sharia_edit_task'),
    path('tasks/delete/<int:task_id>/', views.delete_task, name='sharia_delete_task'),

    # Member Management
    path('members/', views.member_management, name='sharia_member_management'),
    path('members/add/', views.add_member, name='sharia_add_member'),
    path('members/view/<int:member_id>/', views.view_member, name='sharia_view_member'),
    path('members/edit/<int:member_id>/', views.edit_member, name='sharia_edit_member'),
    path('members/delete/<int:member_id>/', views.delete_member, name='sharia_delete_member'),

    # File Library
    path('files/', views.file_library, name='sharia_file_library'),
    path('files/upload/', views.upload_file, name='sharia_upload_file'),
    path('files/delete/<int:file_id>/', views.delete_file, name='sharia_delete_file'),

    # Daily Messages
    path('messages/', views.message_management, name='sharia_message_management'),
    path('messages/add/', views.add_message, name='sharia_add_message'),
    path('messages/view/<int:message_id>/', views.view_message, name='sharia_view_message'),
    path('messages/edit/<int:message_id>/', views.edit_message, name='sharia_edit_message'),
    path('messages/delete/<int:message_id>/', views.delete_message, name='sharia_delete_message'),

    # Family Competitions
    path('competitions/', views.competition_management, name='sharia_competition_management'),
    path('competitions/add/', views.add_competition, name='sharia_add_competition'),
    path('competitions/view/<int:competition_id>/', views.view_competition, name='sharia_view_competition'),
    path('competitions/edit/<int:competition_id>/', views.edit_competition, name='sharia_edit_competition'),
    path('competitions/delete/<int:competition_id>/', views.delete_competition, name='sharia_delete_competition'),

    # Youth Books
    path('books/', views.book_management, name='sharia_book_management'),
    path('books/add/', views.add_book, name='sharia_add_book'),
    path('books/view/<int:book_id>/', views.view_book, name='sharia_view_book'),
    path('books/edit/<int:book_id>/', views.edit_book, name='sharia_edit_book'),
    path('books/delete/<int:book_id>/', views.delete_book, name='sharia_delete_book'),

    # Reports
    path('reports/', views.reports, name='sharia_reports'),
    path('reports/add/', views.add_report, name='sharia_add_report'),

    # Notifications
    path('notifications/', views.notifications, name='sharia_notifications'),
    path('notifications/mark-all-read/', views.mark_all_read, name='sharia_mark_all_read'),
]