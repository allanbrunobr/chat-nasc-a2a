#!/usr/bin/env python3
"""Detailed test script for NAI with specific user ID"""

import requests
import json
import sys

BASE_URL = "http://localhost:8080"
USER_ID = "dd060639-cb4c-46a2-aac9-764a979b2d50"

def test_endpoint(endpoint, method="GET", data=None):
    """Test a specific endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testing {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        else:
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            try:
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"Response (text): {response.text[:200]}")
        else:
            print(f"Error: {response.text}")
        
        return response
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

def main():
    print("🧪 NAI Detailed Test")
    print(f"📍 Server: {BASE_URL}")
    print(f"👤 User ID: {USER_ID}")
    
    # Test 1: Check server health
    print("\n" + "="*60)
    print("Test 1: Server Health Check")
    test_endpoint("/docs")
    
    # Test 2: Simple greeting
    print("\n" + "="*60)
    print("Test 2: Simple Greeting")
    payload = {
        "user_id": USER_ID,
        "messages": [{"role": "user", "content": "Olá"}]
    }
    response = test_endpoint("/run", "POST", payload)
    
    # Test 3: Profile request
    print("\n" + "="*60)
    print("Test 3: Profile Request")
    payload = {
        "user_id": USER_ID,
        "messages": [{"role": "user", "content": "Mostre meu perfil"}]
    }
    response = test_endpoint("/run", "POST", payload)
    
    # Test 4: Create profile
    print("\n" + "="*60)
    print("Test 4: Create Profile")
    payload = {
        "user_id": USER_ID,
        "messages": [{"role": "user", "content": "Quero criar meu perfil"}]
    }
    response = test_endpoint("/run", "POST", payload)
    
    # Test 5: Check database connection
    print("\n" + "="*60)
    print("Test 5: Database Connection (via state check)")
    payload = {
        "user_id": USER_ID,
        "messages": [{"role": "user", "content": "Olá"}],
        "state": {"test": "checking state persistence"}
    }
    response = test_endpoint("/run", "POST", payload)

if __name__ == "__main__":
    main()