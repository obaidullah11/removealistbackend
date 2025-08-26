"""
URL patterns for move management endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_move, name='create_move'),
    path('get/<uuid:move_id>/', views.get_move, name='get_move'),
    path('user-moves/', views.user_moves, name='user_moves'),
    path('update/<uuid:move_id>/', views.update_move, name='update_move'),
    path('delete/<uuid:move_id>/', views.delete_move, name='delete_move'),
]
