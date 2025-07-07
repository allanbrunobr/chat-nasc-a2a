#!/usr/bin/env python3
"""Test user profile using ADK API"""

import requests
import json

user_id = "dd060639-cb4c-46a2-aac9-764a979b2d50"

print(f"🔍 Testing user {user_id} via ADK API")
print("="*60)

# Call ADK API directly (port 8080)
request = {
    "user_id": user_id,
    "session_id": "test_session",
    "message": "mostre meu perfil completo"
}

print("📤 Calling ADK API on port 8080...")
print(f"Message: {request['message']}")

try:
    response = requests.post(
        "http://localhost:8080/run",
        json=request,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    print(f"\n📡 Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        response_text = data.get("response", "")
        
        print("\n📄 ADK Response:")
        print(response_text)
        
        print("\n🔍 Analysis:")
        if "Nome:" in response_text or "Email:" in response_text:
            print("✅ USER EXISTS - Profile data found!")
            
            # Extract key info
            lines = response_text.split('\n')
            for line in lines:
                if any(key in line for key in ["Nome:", "Email:", "Telefone:", "Localização:"]):
                    print(f"   {line.strip()}")
                    
        elif "não possui um perfil" in response_text:
            print("❌ USER DOES NOT EXIST - No profile found")
        else:
            print("❓ Unclear response")
            
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {e}")

print("\n" + "="*60)
print("This test used the ADK API directly (not A2A)")