from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('schedule/', views.schedule_calendar, name='schedule_calendar'),
    path('<int:program_id>/', views.schedule_calendar, name='schedule_calendar'),

    # New day events URL
    path('day/<int:program_id>/<int:year>/<int:month>/<int:day>/', views.day_events, name='day_events'),

    # Event Management
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/add/', views.add_event, name='add_event'),
    path('event/add/<int:program_id>/', views.add_event, name='add_event'),
    path('event/edit/<int:event_id>/', views.edit_event, name='edit_event'),
    path('event/delete/<int:event_id>/', views.delete_event, name='delete_event'),

    path('object/<str:object_type>/<int:object_id>/', views.object_detail, name='object_detail'),
    path('objects/<str:object_type>/<int:program_id>/', views.object_list, name='object_list'),
    path('albums/', views.public_albums, name='public_albums'),
    path('albums/<int:album_id>/', views.public_album_detail, name='public_album_detail'),

    path('schedule/export/ics/', views.export_calendar_ics, name='export_calendar_ics'),
    path('schedule/export/excel/', views.export_calendar_excel, name='export_calendar_excel'),

    path('list/', views.calendar_list_view, name='calendar_list'),

]