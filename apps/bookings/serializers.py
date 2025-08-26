"""
Serializers for booking and scheduling.
"""
from rest_framework import serializers
from django.utils import timezone
from .models import TimeSlot, Booking
from apps.moves.models import Move
import re


class TimeSlotSerializer(serializers.ModelSerializer):
    """
    Serializer for time slots.
    """
    available = serializers.SerializerMethodField()
    
    class Meta:
        model = TimeSlot
        fields = ['id', 'start_time', 'end_time', 'available', 'price']
    
    def get_available(self, obj):
        """Check if time slot is available for the requested date."""
        date = self.context.get('date')
        if date:
            return obj.is_available_on_date(date)
        return True


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a booking.
    """
    
    class Meta:
        model = Booking
        fields = ['move_id', 'time_slot', 'phone_number']
    
    def validate_move_id(self, value):
        """Validate that the move belongs to the user."""
        user = self.context['request'].user
        try:
            move = Move.objects.get(id=value, user=user)
            return move
        except Move.DoesNotExist:
            raise serializers.ValidationError("Move not found or doesn't belong to you")
    
    def validate_time_slot(self, value):
        """Validate that the time slot exists and is active."""
        if not value.is_active:
            raise serializers.ValidationError("This time slot is not available")
        return value
    
    def validate_phone_number(self, value):
        """Validate phone number format."""
        # Allow various formats: +1234567890, (123) 456-7890, 123-456-7890, etc.
        pattern = r'^[\+\d\s\-\(\)]{8,20}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Phone number must be 8-20 characters and can include +, spaces, hyphens, and parentheses"
            )
        return value
    
    def validate(self, attrs):
        """Validate booking availability."""
        move = attrs['move_id']
        time_slot = attrs['time_slot']
        date = move.move_date
        
        # Check if time slot is available on the move date
        if not time_slot.is_available_on_date(date):
            raise serializers.ValidationError({
                'time_slot': ['This time slot is not available for the selected date']
            })
        
        # Check if user already has a booking for this move
        if Booking.objects.filter(move=move, status__in=['confirmed', 'in_progress']).exists():
            raise serializers.ValidationError({
                'move_id': ['You already have an active booking for this move']
            })
        
        attrs['date'] = date
        return attrs
    
    def create(self, validated_data):
        """Create a booking."""
        user = self.context['request'].user
        move = validated_data.pop('move_id')
        
        booking = Booking.objects.create(
            user=user,
            move=move,
            **validated_data
        )
        
        # Update move status to scheduled
        move.status = 'scheduled'
        move.save()
        
        return booking


class BookingDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for booking details.
    """
    time_slot_display = serializers.CharField(source='time_slot_display', read_only=True)
    start_time = serializers.TimeField(source='time_slot.start_time', read_only=True)
    end_time = serializers.TimeField(source='time_slot.end_time', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'move_id', 'date', 'start_time', 'end_time', 'time_slot_display',
            'status', 'confirmation_number', 'phone_number', 'created_at'
        ]
        read_only_fields = [
            'id', 'confirmation_number', 'created_at'
        ]


class BookingListSerializer(serializers.ModelSerializer):
    """
    Serializer for booking list (summary view).
    """
    time_slot_display = serializers.CharField(source='time_slot_display', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'move_id', 'date', 'time_slot_display',
            'status', 'confirmation_number', 'created_at'
        ]
        read_only_fields = [
            'id', 'confirmation_number', 'created_at'
        ]
