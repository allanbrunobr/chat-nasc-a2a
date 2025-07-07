#!/usr/bin/env python3
"""Test user directly via backend API"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

user_id = "dd060639-cb4c-46a2-aac9-764a979b2d50"
profile_url = os.getenv("USER_PROFILE_URL")

print(f"🔍 Testing user {user_id} directly via backend API")
print(f"API URL: {profile_url}")
print("="*60)

if not profile_url:
    print("❌ USER_PROFILE_URL not found in environment")
    exit(1)

try:
    # Make direct API call
    url = f"{profile_url}?user_id={user_id}"
    print(f"\n📤 GET {url}")
    
    response = requests.get(url, timeout=10)
    
    print(f"\n📡 Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n📄 API Response:")
        
        if data.get("user"):
            print("✅ USER EXISTS!")
            user_data = data["user"]
            
            print("\n👤 User Profile:")
            print(f"   ID: {user_data.get('id', user_id)}")
            print(f"   Name: {user_data.get('firstName', '')} {user_data.get('lastName', '')}")
            print(f"   Email: {user_data.get('email', '')}")
            print(f"   Phone: {user_data.get('phone', '')}")
            print(f"   Location: {user_data.get('city', '')}, {user_data.get('state', '')}")
            
            if user_data.get('hardSkills'):
                print(f"   Hard Skills: {', '.join(user_data['hardSkills'][:5])}")
            if user_data.get('softSkills'):
                print(f"   Soft Skills: {', '.join(user_data['softSkills'][:3])}")
                
        else:
            print("❌ USER NOT FOUND - Empty response")
            print(f"Full response: {data}")
            
    elif response.status_code == 404:
        print("❌ USER NOT FOUND - 404 response")
    else:
        print(f"❌ Error response: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)