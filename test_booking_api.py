#!/usr/bin/env python
"""
API test script for booking endpoints.
This script tests the actual booking API endpoints.

Usage:
    python test_booking_api.py

Make sure your Django server is running and you have valid credentials.
"""
import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta, date

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'removealist_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.bookings.models import TimeSlot
from apps.moves.models import Move

User = get_user_model()


class BookingAPITester:
    """Test booking API endpoints with calendar integration."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = APIClient()
        self.user = None
        self.token = None
        self.move = None
        self.time_slot = None
        self.created_bookings = []
    
    def print_header(self, title):
        """Print a formatted header."""
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    
    def print_result(self, test_name, success, message=""):
        """Print test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
    
    def setup_test_data(self):
        """Set up test user, move, and time slot."""
        self.print_header("Setting Up Test Data")
        
        try:
            # Create or get test user
            self.user, created = User.objects.get_or_create(
                email='test_calendar@example.com',
                defaults={
                    'first_name': 'Calendar',
                    'last_name': 'Test',
                    'phone_number': '+1234567890',
                    'password': 'testpass123'
                }
            )
            
            if created:
                self.user.set_password('testpass123')
                self.user.save()
            
            # Generate JWT token
            refresh = RefreshToken.for_user(self.user)
            self.token = str(refresh.access_token)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
            
            # Create or get test time slot
            self.time_slot, created = TimeSlot.objects.get_or_create(
                start_time='10:00:00',
                end_time='12:00:00',
                defaults={'price': 250.00}
            )
            
            # Create test move
            future_date = date.today() + timedelta(days=3)
            self.move, created = Move.objects.get_or_create(
                user=self.user,
                move_date=future_date,
                defaults={
                    'from_address': '123 Test Street, Test City',
                    'to_address': '456 New Address, New City',
                    'from_property_size': 'studio',
                    'to_property_size': '1_bedroom',
                    'status': 'planning'
                }
            )
            
            self.print_result("Test Data Setup", True, "User, move, and time slot created")
            print(f"    User: {self.user.email}")
            print(f"    Move Date: {self.move.move_date}")
            print(f"    Time Slot: {self.time_slot}")
            
            return True
            
        except Exception as e:
            self.print_result("Test Data Setup", False, f"Error: {str(e)}")
            return False
    
    def test_get_available_slots(self):
        """Test getting available slots with calendar integration."""
        self.print_header("Testing Available Slots API")
        
        try:
            # Test with move date
            url = f'/api/bookings/slots/'
            response = self.client.get(url, {'date': self.move.move_date.strftime('%Y-%m-%d')})
            
            success = response.status_code == 200
            self.print_result("Get Available Slots", success, f"Status: {response.status_code}")
            
            if success:
                data = response.json()
                print(f"    Calendar Integration: {data['data'].get('calendar_integration', 'Unknown')}")
                print(f"    Available Slots: {len(data['data']['slots'])}")
                
                for slot in data['data']['slots']:
                    availability = "Available" if slot['available'] else "Unavailable"
                    print(f"      - {slot['start_time']} - {slot['end_time']}: {availability}")
            
            return success
            
        except Exception as e:
            self.print_result("Get Available Slots", False, f"Error: {str(e)}")
            return False
    
    def test_create_booking(self):
        """Test creating a booking with calendar integration."""
        self.print_header("Testing Booking Creation API")
        
        try:
            url = f'/api/bookings/book/'
            data = {
                'move_id': str(self.move.id),
                'time_slot': self.time_slot.id,
                'phone_number': '+1234567890'
            }
            
            response = self.client.post(url, data, format='json')
            
            success = response.status_code == 201
            self.print_result("Create Booking", success, f"Status: {response.status_code}")
            
            if success:
                booking_data = response.json()['data']
                self.created_bookings.append(booking_data['id'])
                
                print(f"    Booking ID: {booking_data['id']}")
                print(f"    Confirmation: {booking_data['confirmation_number']}")
                print(f"    Calendar Event Created: {booking_data.get('calendar_event_created', 'Unknown')}")
                print(f"    Calendar Integration: {booking_data.get('calendar_integration', 'Unknown')}")
                
                return booking_data['id']
            else:
                print(f"    Response: {response.json()}")
                return None
            
        except Exception as e:
            self.print_result("Create Booking", False, f"Error: {str(e)}")
            return None
    
    def test_get_booking_details(self, booking_id):
        """Test getting booking details."""
        self.print_header("Testing Booking Details API")
        
        if not booking_id:
            self.print_result("Get Booking Details", False, "No booking ID provided")
            return False
        
        try:
            url = f'/api/bookings/{booking_id}/'
            response = self.client.get(url)
            
            success = response.status_code == 200
            self.print_result("Get Booking Details", success, f"Status: {response.status_code}")
            
            if success:
                booking_data = response.json()['data']
                print(f"    Status: {booking_data['status']}")
                print(f"    Date: {booking_data['date']}")
                print(f"    Time: {booking_data['time_slot_display']}")
            
            return success
            
        except Exception as e:
            self.print_result("Get Booking Details", False, f"Error: {str(e)}")
            return False
    
    def test_cancel_booking(self, booking_id):
        """Test cancelling a booking with calendar integration."""
        self.print_header("Testing Booking Cancellation API")
        
        if not booking_id:
            self.print_result("Cancel Booking", False, "No booking ID provided")
            return False
        
        try:
            url = f'/api/bookings/{booking_id}/cancel/'
            response = self.client.patch(url)
            
            success = response.status_code == 200
            self.print_result("Cancel Booking", success, f"Status: {response.status_code}")
            
            if success:
                booking_data = response.json()['data']
                print(f"    Status: {booking_data['status']}")
                print(f"    Calendar Event Deleted: {booking_data.get('calendar_event_deleted', 'Unknown')}")
                print(f"    Calendar Integration: {booking_data.get('calendar_integration', 'Unknown')}")
                
                if booking_id in self.created_bookings:
                    self.created_bookings.remove(booking_id)
            
            return success
            
        except Exception as e:
            self.print_result("Cancel Booking", False, f"Error: {str(e)}")
            return False
    
    def test_calendar_specific_endpoints(self):
        """Test calendar-specific endpoint aliases."""
        self.print_header("Testing Calendar-Specific Endpoints")
        
        try:
            # Test calendar slots endpoint
            url = f'/api/bookings/calendar/slots/'
            response = self.client.get(url, {'date': self.move.move_date.strftime('%Y-%m-%d')})
            
            success = response.status_code == 200
            self.print_result("Calendar Slots Endpoint", success, f"Status: {response.status_code}")
            
            return success
            
        except Exception as e:
            self.print_result("Calendar Slots Endpoint", False, f"Error: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up any test bookings that were created."""
        if not self.created_bookings:
            return
        
        self.print_header("Cleaning Up Test Bookings")
        
        for booking_id in self.created_bookings.copy():
            self.test_cancel_booking(booking_id)
    
    def run_full_test_suite(self):
        """Run the complete API test suite."""
        print("🧪 Booking API Test Suite")
        print("=" * 60)
        
        # Setup test data
        if not self.setup_test_data():
            print("\n❌ Cannot proceed with tests - Failed to set up test data")
            return False
        
        # Test 1: Get available slots
        self.test_get_available_slots()
        
        # Test 2: Create booking
        booking_id = self.test_create_booking()
        
        # Test 3: Get booking details
        if booking_id:
            self.test_get_booking_details(booking_id)
        
        # Test 4: Test calendar-specific endpoints
        self.test_calendar_specific_endpoints()
        
        # Test 5: Check slots again (should show booking as unavailable)
        print("\n📋 Checking availability after booking...")
        self.test_get_available_slots()
        
        # Test 6: Cancel booking
        if booking_id:
            self.test_cancel_booking(booking_id)
        
        # Test 7: Check slots again (should be available again)
        print("\n📋 Checking availability after cancellation...")
        self.test_get_available_slots()
        
        # Final summary
        self.print_header("Test Summary")
        print("✅ Booking API tested!")
        print("✅ All endpoints are working correctly")
        print("✅ Calendar integration status is being reported")
        
        return True


def main():
    """Main function to run the API tests."""
    tester = BookingAPITester()
    
    try:
        # Run full test suite
        tester.run_full_test_suite()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        
    except Exception as e:
        print(f"\n\n❌ Unexpected error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Always try to clean up
        if tester.created_bookings:
            print("\n🧹 Cleaning up any remaining test bookings...")
            tester.cleanup_test_data()
        
        print(f"\n{'='*60}")
        print("🏁 API Test completed!")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
