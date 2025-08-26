"""
Serializers for authentication endpoints.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User
from apps.common.validators import validate_phone_number, validate_name


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    agree_to_terms = serializers.BooleanField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'phone_number', 'password', 'confirm_password',
            'first_name', 'last_name', 'agree_to_terms'
        ]
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered")
        return value
    
    def validate_phone_number(self, value):
        """Validate phone number format."""
        validate_phone_number(value)
        return value
    
    def validate_first_name(self, value):
        """Validate first name."""
        validate_name(value)
        return value
    
    def validate_last_name(self, value):
        """Validate last name."""
        validate_name(value)
        return value
    
    def validate_agree_to_terms(self, value):
        """Validate terms agreement."""
        if not value:
            raise serializers.ValidationError("You must agree to the terms and conditions")
        return value
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': ['Passwords do not match']
            })
        return attrs
    
    def create(self, validated_data):
        """Create a new user."""
        validated_data.pop('confirm_password')
        validated_data.pop('agree_to_terms')
        
        user = User.objects.create_user(
            username=validated_data['email'],  # Django requires username
            **validated_data
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        """Validate login credentials."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            
            if not user:
                raise serializers.ValidationError({
                    'non_field_errors': ['Invalid email or password']
                })
            
            if not user.is_active:
                raise serializers.ValidationError({
                    'non_field_errors': ['User account is disabled']
                })
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError({
                'non_field_errors': ['Must include email and password']
            })


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile.
    """
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone_number',
            'avatar', 'is_email_verified', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'is_email_verified', 'created_at']
    
    def validate_phone_number(self, value):
        """Validate phone number format."""
        validate_phone_number(value)
        return value
    
    def validate_first_name(self, value):
        """Validate first name."""
        validate_name(value)
        return value
    
    def validate_last_name(self, value):
        """Validate last name."""
        validate_name(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """
    current_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    
    def validate_current_password(self, value):
        """Validate current password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    token = serializers.CharField()


class ResendEmailSerializer(serializers.Serializer):
    """
    Serializer for resending verification email.
    """
    email = serializers.EmailField()


class ForgotPasswordSerializer(serializers.Serializer):
    """
    Serializer for forgot password.
    """
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for password reset.
    """
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


class AvatarUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for avatar upload.
    """
    avatar = serializers.ImageField()
    
    class Meta:
        model = User
        fields = ['avatar']
    
    def validate_avatar(self, value):
        """Validate avatar file."""
        # Check file size (10MB limit)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size exceeds 10MB limit")
        
        # Check file format
        allowed_formats = ['jpeg', 'jpg', 'png']
        file_extension = value.name.lower().split('.')[-1]
        if file_extension not in allowed_formats:
            raise serializers.ValidationError("Unsupported file format. Please use PNG, JPG, or JPEG")
        
        return value
