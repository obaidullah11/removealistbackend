"""
URL patterns for authentication endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/email/', views.register_email, name='register_email'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('refresh/', views.refresh_token, name='refresh_token'),
    
    # Email verification
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-email/', views.resend_email, name='resend_email'),
    
    # Password management
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Profile management
    path('profile/', views.profile, name='profile'),
    path('profile/', views.update_profile, name='update_profile'),  # Same URL, different methods
    path('profile/avatar/', views.upload_avatar, name='upload_avatar'),
]
