"""
URL patterns for inventory management endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('rooms/', views.get_rooms, name='get_rooms'),
    path('rooms/', views.create_room, name='create_room'),  # Same URL, different methods
    path('rooms/<uuid:room_id>/', views.get_room, name='get_room'),
    path('rooms/<uuid:room_id>/', views.update_room, name='update_room'),  # Same URL, different methods
    path('rooms/<uuid:room_id>/packed/', views.mark_room_packed, name='mark_room_packed'),
    path('rooms/<uuid:room_id>/', views.delete_room, name='delete_room'),  # Same URL, different methods
    path('rooms/<uuid:room_id>/image/', views.upload_room_image, name='upload_room_image'),
]
