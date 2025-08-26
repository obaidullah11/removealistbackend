"""
Views for booking and scheduling.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from datetime import datetime
from .models import TimeSlot, Booking
from .serializers import (
    TimeSlotSerializer, BookingCreateSerializer,
    BookingDetailSerializer, BookingListSerializer
)
from apps.authentication.tasks import send_booking_confirmation_email
from apps.common.utils import success_response, error_response, paginated_response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_slots(request):
    """
    Get available time slots for a specific date.
    """
    date_str = request.GET.get('date')
    
    if not date_str:
        return error_response(
            "Date parameter required",
            {'date': ['This parameter is required']},
            status.HTTP_400_BAD_REQUEST
        )
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return error_response(
            "Invalid date format",
            {'date': ['Date must be in YYYY-MM-DD format']},
            status.HTTP_400_BAD_REQUEST
        )
    
    # Get all active time slots
    time_slots = TimeSlot.objects.filter(is_active=True)
    
    # Serialize with date context for availability check
    serializer = TimeSlotSerializer(
        time_slots, 
        many=True, 
        context={'date': date}
    )
    
    return success_response(
        "Available slots retrieved",
        {
            'date': date_str,
            'slots': serializer.data
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_slot(request):
    """
    Book a time slot for a move.
    """
    serializer = BookingCreateSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        booking = serializer.save()
        
        # Send confirmation email
        booking_data = {
            'move_date': booking.date.strftime('%B %d, %Y'),
            'time_slot': booking.time_slot_display,
            'confirmation_number': booking.confirmation_number,
            'phone_number': booking.phone_number,
        }
        send_booking_confirmation_email.delay(booking.user.id, booking_data)
        
        # Return booking details
        detail_serializer = BookingDetailSerializer(booking)
        
        return success_response(
            "Booking confirmed successfully",
            detail_serializer.data,
            status.HTTP_201_CREATED
        )
    
    return error_response(
        "Booking failed",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_bookings(request):
    """
    Get all bookings for the authenticated user.
    """
    bookings = Booking.objects.filter(user=request.user)
    
    # Check if pagination is requested
    if request.GET.get('page'):
        return paginated_response(
            bookings,
            BookingListSerializer,
            request,
            "Bookings retrieved successfully"
        )
    
    # Return all bookings without pagination
    serializer = BookingListSerializer(bookings, many=True)
    
    return success_response(
        "Bookings retrieved successfully",
        serializer.data
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_detail(request, booking_id):
    """
    Get booking details by ID.
    """
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    serializer = BookingDetailSerializer(booking)
    
    return success_response(
        "Booking details retrieved",
        serializer.data
    )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):
    """
    Cancel a booking.
    """
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Check if booking can be cancelled
    if booking.status in ['completed', 'cancelled']:
        return error_response(
            "Cannot cancel booking",
            {'detail': ['This booking cannot be cancelled']},
            status.HTTP_400_BAD_REQUEST
        )
    
    # Cancel the booking
    booking.status = 'cancelled'
    booking.save()
    
    # Update move status back to planning if needed
    if booking.move.status == 'scheduled':
        # Check if there are other active bookings for this move
        other_bookings = Booking.objects.filter(
            move=booking.move,
            status__in=['confirmed', 'in_progress']
        ).exclude(id=booking.id)
        
        if not other_bookings.exists():
            booking.move.status = 'planning'
            booking.move.save()
    
    serializer = BookingDetailSerializer(booking)
    
    return success_response(
        "Booking cancelled successfully",
        serializer.data
    )
