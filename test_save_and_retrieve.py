#!/usr/bin/env python3
"""Test save and retrieve flow"""

import requests
import json
import uuid
import time

BASE_URL = "http://localhost:8082"

# Create unique user
user_id = f"test_flow_{uuid.uuid4().hex[:8]}"
print(f"🧪 Testing save and retrieve flow for user: {user_id}")

# Step 1: Save profile
print("\n1️⃣ Saving profile...")
save_request = {
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
        "message": {
            "messageId": str(uuid.uuid4()),
            "role": "user",
            "parts": [{"text": "save profile"}],
            "metadata": {
                "skill": "save_user_profile",
                "user_id": user_id,
                "profile_data": {
                    "firstName": "Flow",
                    "lastName": "Test",
                    "email": f"flow.test.{uuid.uuid4().hex[:8]}@example.com",
                    "city": "Rio de Janeiro",
                    "state": "RJ",
                    "country": "Brasil",
                    "hardSkills": ["JavaScript", "React"],
                    "softSkills": ["Criatividade"],
                    "experiences": [{
                        "company": "Test Corp",
                        "position": "Developer",
                        "startDate": "2023-01-01",
                        "current": True,
                        "description": "Frontend development"
                    }]
                }
            }
        }
    },
    "id": str(uuid.uuid4())
}

save_response = requests.post(
    f"{BASE_URL}/",
    json=save_request,
    headers={"Content-Type": "application/json"},
    timeout=30
)

print(f"Save status: {save_response.status_code}")

# Wait a bit
time.sleep(3)

# Step 2: Retrieve profile
print("\n2️⃣ Retrieving profile...")
retrieve_request = {
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
        "message": {
            "messageId": str(uuid.uuid4()),
            "role": "user",
            "parts": [{"text": "show my profile"}],
            "metadata": {
                "skill": "retrieve_user_profile",
                "user_id": user_id
            }
        }
    },
    "id": str(uuid.uuid4())
}

print(f"Requesting profile for user_id: {user_id}")

retrieve_response = requests.post(
    f"{BASE_URL}/",
    json=retrieve_request,
    headers={
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    },
    stream=True,
    timeout=30
)

print(f"Retrieve status: {retrieve_response.status_code}")

if retrieve_response.status_code == 200:
    for line in retrieve_response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('data: ') and 'message' in decoded:
                try:
                    data = json.loads(decoded[6:])
                    result = data.get('result', {})
                    if result.get('kind') == 'message':
                        text = result['parts'][0]['text'] if result.get('parts') else ""
                        
                        print("\n📄 Response:")
                        print(text[:500] + "..." if len(text) > 500 else text)
                        
                        # Check results
                        if "Flow Test" in text:
                            print("\n✅ SUCCESS: Profile data found!")
                            print("✅ NATIVE SKILL is working correctly")
                        elif "📋 **Perfil de Usuário**" in text:
                            print("\n✅ NATIVE SKILL format detected")
                        elif "Você ainda não possui" in text:
                            print("\n❌ FAILURE: Profile not found")
                            print("🔄 Using ADK fallback")
                            print("\n🔍 Possible issues:")
                            print("1. save_user_profile might not be persisting correctly")
                            print("2. retrieve_user_profile might be looking in wrong place")
                            print("3. user_id might not be passed correctly")
                        
                        break
                except:
                    pass

# Step 3: Try direct API call to verify
print("\n3️⃣ Testing direct API call to profile service...")
try:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    profile_url = os.getenv("USER_PROFILE_URL")
    if profile_url:
        direct_response = requests.get(
            f"{profile_url}?user_id={user_id}",
            timeout=10
        )
        print(f"Direct API status: {direct_response.status_code}")
        if direct_response.status_code == 200:
            data = direct_response.json()
            if data.get("user"):
                print("✅ Profile exists in backend!")
                print(f"Name: {data['user'].get('firstName')} {data['user'].get('lastName')}")
            else:
                print("❌ Profile NOT found in backend")
except Exception as e:
    print(f"Could not test direct API: {e}")