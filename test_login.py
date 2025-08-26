#!/usr/bin/env python3
"""
Test script for login API endpoint
"""
import requests
import json

# Test data
login_data = {
    "email": "muhammadobaidu4llah1122@gmail.com",
    "password": "Obaid123"
}

# API endpoint
url = "http://localhost:8000/api/auth/login/"

try:
    # Make the request
    response = requests.post(url, json=login_data, headers={'Content-Type': 'application/json'})
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body:")
    print(json.dumps(response.json(), indent=2))
    
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except json.JSONDecodeError as e:
    print(f"JSON decode error: {e}")
    print(f"Raw response: {response.text}")
except Exception as e:
    print(f"Unexpected error: {e}")
