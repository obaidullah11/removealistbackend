"""
Authentication views for the RemoveList application.
"""
import secrets
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import EmailVerificationToken, PasswordResetToken
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    ChangePasswordSerializer, EmailVerificationSerializer, ResendEmailSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, AvatarUploadSerializer
)
# Import functions directly instead of Celery tasks
from .tasks import send_verification_email, send_password_reset_email
from apps.common.utils import success_response, error_response

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register_email(request):
    """
    Register a new user with email.
    """
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Create verification token
        token = secrets.token_urlsafe(32)
        EmailVerificationToken.objects.create(
            user=user,
            token=token
        )
        
        # Send verification email (direct call instead of Celery task)
        try:
            send_verification_email(user.id, token)
        except Exception as e:
            # Log error but don't fail registration
            print(f"Failed to send verification email: {e}")
        
        return success_response(
            "Registration successful! Please check your email for verification.",
            {
                'user_id': str(user.id),
                'email': user.email,
                'verification_required': True
            },
            status.HTTP_201_CREATED
        )
    
    return error_response(
        "Registration failed",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user and return JWT tokens.
    """
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Check if email is verified
        if not user.is_email_verified:
            return error_response(
                "Email verification required",
                {'non_field_errors': ['Please verify your email before logging in']},
                status.HTTP_400_BAD_REQUEST
            )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return success_response(
            "Login successful!",
            {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_email_verified': user.is_email_verified,
                    'avatar': user.avatar.url if user.avatar else None
                }
            }
        )
    
    return error_response(
        "Invalid credentials",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify user email with token.
    """
    serializer = EmailVerificationSerializer(data=request.data)
    
    if serializer.is_valid():
        token = serializer.validated_data['token']
        
        try:
            verification_token = EmailVerificationToken.objects.get(token=token)
            
            if verification_token.is_used:
                return error_response(
                    "Token already used",
                    {'token': ['This verification link has already been used']},
                    status.HTTP_400_BAD_REQUEST
                )
            
            if verification_token.is_expired:
                return error_response(
                    "This verification link has expired",
                    {'token': ['Token has expired']},
                    status.HTTP_400_BAD_REQUEST
                )
            
            # Mark token as used and verify user
            verification_token.is_used = True
            verification_token.save()
            
            user = verification_token.user
            user.is_email_verified = True
            user.save()
            
            return success_response(
                "Email verified successfully",
                {'verified': True}
            )
            
        except EmailVerificationToken.DoesNotExist:
            return error_response(
                "Invalid verification token",
                {'token': ['Invalid or expired token']},
                status.HTTP_400_BAD_REQUEST
            )
    
    return error_response(
        "Invalid token",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_email(request):
    """
    Resend verification email.
    """
    serializer = ResendEmailSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_email_verified:
                return success_response(
                    "If your email is registered, a verification link has been sent."
                )
            
            # Create new verification token
            token = secrets.token_urlsafe(32)
            EmailVerificationToken.objects.create(
                user=user,
                token=token
            )
            
            # Send verification email (direct call instead of Celery task)
            try:
                send_verification_email(user.id, token)
            except Exception as e:
                print(f"Failed to send verification email: {e}")
            
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        
        return success_response(
            "If your email is registered, a verification link has been sent."
        )
    
    return error_response(
        "Invalid email",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """
    Send password reset email.
    """
    serializer = ForgotPasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Create password reset token
            token = secrets.token_urlsafe(32)
            PasswordResetToken.objects.create(
                user=user,
                token=token
            )
            
            # Send password reset email (direct call instead of Celery task)
            try:
                send_password_reset_email(user.id, token)
            except Exception as e:
                print(f"Failed to send password reset email: {e}")
            
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        
        return success_response(
            "If an account exists with this email, you will receive a password reset link."
        )
    
    return error_response(
        "Invalid email",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Reset password with token.
    """
    serializer = ResetPasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            
            if reset_token.is_used:
                return error_response(
                    "Token already used",
                    {'token': ['This reset link has already been used']},
                    status.HTTP_400_BAD_REQUEST
                )
            
            if reset_token.is_expired:
                return error_response(
                    "This reset link has expired",
                    {'token': ['Token has expired']},
                    status.HTTP_400_BAD_REQUEST
                )
            
            # Reset password and mark token as used
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            reset_token.is_used = True
            reset_token.save()
            
            return success_response("Password reset successfully")
            
        except PasswordResetToken.DoesNotExist:
            return error_response(
                "Invalid reset token",
                {'token': ['Invalid or expired token']},
                status.HTTP_400_BAD_REQUEST
            )
    
    return error_response(
        "Invalid data",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password (authenticated).
    """
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        new_password = serializer.validated_data['new_password']
        
        user = request.user
        user.set_password(new_password)
        user.save()
        
        return success_response("Password updated successfully")
    
    return error_response(
        "Password change failed",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user by blacklisting refresh token.
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return success_response("Logged out successfully")
    
    except Exception as e:
        return error_response(
            "Logout failed",
            {'detail': [str(e)]},
            status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh JWT access token.
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return error_response(
                "Refresh token required",
                {'refresh_token': ['This field is required']},
                status.HTTP_400_BAD_REQUEST
            )
        
        token = RefreshToken(refresh_token)
        
        return success_response(
            "Token refreshed successfully",
            {
                'access_token': str(token.access_token),
                'refresh_token': str(token)
            }
        )
    
    except Exception as e:
        return error_response(
            "Token refresh failed",
            {'detail': [str(e)]},
            status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Get user profile.
    """
    serializer = UserProfileSerializer(request.user)
    return success_response(
        "Profile retrieved successfully",
        serializer.data
    )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update user profile.
    """
    serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return success_response(
            "Profile updated successfully",
            serializer.data
        )
    
    return error_response(
        "Profile update failed",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_avatar(request):
    """
    Upload user avatar.
    """
    serializer = AvatarUploadSerializer(request.user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return success_response(
            "Avatar updated successfully",
            {'avatar': request.user.avatar.url if request.user.avatar else None}
        )
    
    return error_response(
        "Avatar upload failed",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )
