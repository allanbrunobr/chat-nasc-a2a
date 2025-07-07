#!/usr/bin/env python3
"""Debug API response format"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

user_id = "dd060639-cb4c-46a2-aac9-764a979b2d50"
url = f"{os.getenv('USER_PROFILE_URL')}?user_id={user_id}"

print(f"🔍 Direct API call to: {url}")

response = requests.get(url, timeout=10)
print(f"\n📡 Status: {response.status_code}")
print(f"📦 Size: {len(response.text)} bytes")

if response.status_code == 200:
    data = response.json()
    
    print("\n🔍 Response structure:")
    print(f"Type: {type(data)}")
    print(f"Keys: {list(data.keys())[:10]}")  # First 10 keys
    
    # Check for different possible structures
    if 'user' in data:
        print("\n✅ Found 'user' key")
        print(f"User data type: {type(data['user'])}")
        if data['user']:
            print("User data is NOT empty")
        else:
            print("User data is EMPTY")
    
    if 'user_id' in data:
        print(f"\n✅ Found 'user_id': {data['user_id']}")
    
    if 'name' in data:
        print(f"✅ Found 'name': {data['name']}")
        
    if 'email' in data:
        print(f"✅ Found 'email': {data['email']}")
    
    # Print first 500 chars of JSON
    print("\n📄 Response preview:")
    print(json.dumps(data, indent=2)[:500] + "...")