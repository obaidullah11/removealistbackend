"""
Views for booking and scheduling.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.conf import settings
from datetime import datetime, timedelta, time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os
import pytz  # Add this import

from .models import TimeSlot, Booking
from .serializers import (
    TimeSlotSerializer, BookingCreateSerializer,
    BookingDetailSerializer, BookingListSerializer
)
from apps.authentication.tasks import send_booking_confirmation_email
from apps.common.utils import success_response, error_response, paginated_response

# Your constants
SERVICE_ACCOUNT_FILE = getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_JSON', 
                              os.path.join(os.path.dirname(__file__), 'service_account.json'))
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = getattr(settings, 'GOOGLE_CALENDAR_ID', "muhammadobaidullah1122@gmail.com")


def get_free_slots(date, calendar_id):
    """
    Get free 30-min slots from Google Calendar between 09:00–20:00
    """
    # Authenticate
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("calendar", "v3", credentials=credentials)

    # Define working hours - create timezone-aware datetimes
    tz = pytz.timezone("Asia/Karachi")  # your working timezone
    start_of_day = tz.localize(datetime.combine(date, time(9, 0)))
    end_of_day = tz.localize(datetime.combine(date, time(20, 0)))

    # FreeBusy query
    freebusy_query = {
        "timeMin": start_of_day.isoformat(),
        "timeMax": end_of_day.isoformat(),
        "timeZone": "Asia/Karachi",
        "items": [{"id": calendar_id}],
    }
    busy_times = service.freebusy().query(body=freebusy_query).execute()
    busy_slots = busy_times["calendars"][calendar_id].get("busy", [])

    # Convert busy slots to datetime ranges
    busy_periods = [
        (
            datetime.fromisoformat(busy["start"].replace("Z", "+00:00")),
            datetime.fromisoformat(busy["end"].replace("Z", "+00:00")),
        )
        for busy in busy_slots
    ]

    # Generate 30-min slots
    slots = []
    start_time = start_of_day

    while start_time < end_of_day:
        slot_end = start_time + timedelta(minutes=30)

        # Check if slot overlaps with any busy period
        is_busy = any(
            start_time < busy_end and slot_end > busy_start
            for busy_start, busy_end in busy_periods
        )

        if not is_busy:
            slots.append(
                {
                    "start": start_time.strftime("%Y-%m-%d %H:%M"),
                    "end": slot_end.strftime("%Y-%m-%d %H:%M"),
                }
            )

        start_time = slot_end

    return slots



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def available_slots(request):
    """
    Get available time slots for a specific date from Google Calendar.
    """
    date_str = request.GET.get("date")

    if not date_str:
        return error_response(
            "Date parameter required",
            {"date": ["This parameter is required"]},
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return error_response(
            "Invalid date format",
            {"date": ["Date must be in YYYY-MM-DD format"]},
            status.HTTP_400_BAD_REQUEST,
        )

    slots = get_free_slots(date, CALENDAR_ID)

    return success_response(
        "Available slots retrieved",
        {
            "date": date_str,
            "slots": slots,
        },
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_slot(request):
    """
    Book a time slot for a move (no DB TimeSlot model required).
    Creates event on Google Calendar as well.
    """
    serializer = BookingCreateSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        booking = serializer.save()

        # ---- GOOGLE CALENDAR EVENT ----
        try:
            
            credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            service = build("calendar", "v3", credentials=credentials)

            event = {
                "summary": f"Move Booking - {booking.user.username}",
                "description": f"Phone: {booking.phone_number}, Confirmation: {booking.confirmation_number}",
                "start": {
                    "dateTime": f"{booking.date}T{booking.start_time}",
                    "timeZone": "Asia/Karachi",
                },
                "end": {
                    "dateTime": f"{booking.date}T{booking.end_time}",
                    "timeZone": "Asia/Karachi",
                },
            }


            service.events().insert(
                calendarId="muhammadobaidullah1122@gmail.com",  # or your calendar ID
                body=event
            ).execute()
        except Exception as e:
            # Log but don't block booking
            print("Google Calendar error:", e)

        # ---- SEND CONFIRMATION EMAIL ----
        booking_data = {
            'move_date': booking.date.strftime('%B %d, %Y'),
            'time_slot': booking.time_slot_display,
            'confirmation_number': booking.confirmation_number,
            'phone_number': booking.phone_number,
        }
        send_booking_confirmation_email(booking.user.id, booking_data)

        # ---- RETURN RESPONSE ----
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
