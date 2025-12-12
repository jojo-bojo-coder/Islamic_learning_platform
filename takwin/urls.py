from django.urls import path
from . import views

urlpatterns = [
    path('', views.takwin, name="takwin"),
    path('tarbawiu/', views.tarbawiu, name="tarbawiu"),
    path('shareiu/', views.shareiu, name="shareiu"),
    path('mhari/', views.mhari, name="mhari"),
    path('medad/', views.medad, name="medad"),
    path('toggle_takwin/<int:takwin_id>/', views.toggle_takwin, name='toggle_takwin'),
    path('pdf/<int:takwin_id>/', views.pdf_view_takwin, name='pdf_view_takwin'),
    path('pdf/<int:takwin_id>/file/', views.pdf_file_view_takwin, name='pdf_file_view_takwin'),
]