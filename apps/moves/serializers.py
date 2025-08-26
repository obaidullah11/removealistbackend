"""
Serializers for move management.
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Move
from apps.common.validators import validate_name


class MoveCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a move.
    """
    
    class Meta:
        model = Move
        fields = [
            'move_date', 'current_location', 'destination_location',
            'from_property_type', 'from_property_size', 'to_property_type', 'to_property_size', 
            'special_items', 'additional_details',
            'first_name', 'last_name', 'email'
        ]
    
    def validate_move_date(self, value):
        """Validate that move date is in the future."""
        if value <= timezone.now().date():
            raise serializers.ValidationError("Move date must be in the future")
        return value
    
    def validate_from_property_type(self, value):
        """Validate from property type choice."""
        valid_choices = [choice[0] for choice in Move.PROPERTY_TYPE_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Invalid property type. Choose from: {', '.join(valid_choices)}")
        return value
    
    def validate_from_property_size(self, value):
        """Validate from property size choice."""
        valid_choices = [choice[0] for choice in Move.PROPERTY_SIZE_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Invalid property size. Choose from: {', '.join(valid_choices)}")
        return value
    
    def validate_to_property_type(self, value):
        """Validate to property type choice."""
        valid_choices = [choice[0] for choice in Move.PROPERTY_TYPE_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Invalid property type. Choose from: {', '.join(valid_choices)}")
        return value
    
    def validate_to_property_size(self, value):
        """Validate to property size choice."""
        valid_choices = [choice[0] for choice in Move.PROPERTY_SIZE_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Invalid property size. Choose from: {', '.join(valid_choices)}")
        return value
    
    def validate_first_name(self, value):
        """Validate first name."""
        validate_name(value)
        return value
    
    def validate_last_name(self, value):
        """Validate last name."""
        validate_name(value)
        return value
    
    def create(self, validated_data):
        """Create a move with the authenticated user."""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class MoveUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a move.
    """
    
    class Meta:
        model = Move
        fields = [
            'move_date', 'current_location', 'destination_location',
            'from_property_type', 'from_property_size', 'to_property_type', 'to_property_size',
            'special_items', 'additional_details',
            'first_name', 'last_name', 'email', 'status'
        ]
    
    def validate_move_date(self, value):
        """Validate that move date is in the future."""
        if value <= timezone.now().date():
            raise serializers.ValidationError("Move date must be in the future")
        return value
    
    def validate_from_property_type(self, value):
        """Validate from property type choice."""
        valid_choices = [choice[0] for choice in Move.PROPERTY_TYPE_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Invalid property type. Choose from: {', '.join(valid_choices)}")
        return value
    
    def validate_from_property_size(self, value):
        """Validate from property size choice."""
        valid_choices = [choice[0] for choice in Move.PROPERTY_SIZE_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Invalid property size. Choose from: {', '.join(valid_choices)}")
        return value
    
    def validate_to_property_type(self, value):
        """Validate to property type choice."""
        valid_choices = [choice[0] for choice in Move.PROPERTY_TYPE_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Invalid property type. Choose from: {', '.join(valid_choices)}")
        return value
    
    def validate_to_property_size(self, value):
        """Validate to property size choice."""
        valid_choices = [choice[0] for choice in Move.PROPERTY_SIZE_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Invalid property size. Choose from: {', '.join(valid_choices)}")
        return value
    
    def validate_status(self, value):
        """Validate status choice."""
        valid_choices = [choice[0] for choice in Move.STATUS_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Invalid status. Choose from: {', '.join(valid_choices)}")
        return value
    
    def validate_first_name(self, value):
        """Validate first name."""
        validate_name(value)
        return value
    
    def validate_last_name(self, value):
        """Validate last name."""
        validate_name(value)
        return value


class MoveDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for move details (read-only).
    """
    
    class Meta:
        model = Move
        fields = [
            'id', 'move_date', 'current_location', 'destination_location',
            'from_property_type', 'from_property_size', 'to_property_type', 'to_property_size',
            'special_items', 'additional_details',
            'first_name', 'last_name', 'email', 'status', 'progress',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'progress', 'created_at', 'updated_at']


class MoveListSerializer(serializers.ModelSerializer):
    """
    Serializer for move list (summary view).
    """
    
    class Meta:
        model = Move
        fields = [
            'id', 'move_date', 'current_location', 'destination_location',
            'status', 'progress', 'created_at'
        ]
        read_only_fields = ['id', 'progress', 'created_at']
