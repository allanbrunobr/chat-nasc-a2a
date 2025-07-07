#!/usr/bin/env python3
"""Debug full A2A flow"""

import requests
import json
import uuid

# Test with a NEW user to ensure clean state
user_id = f"debug_{uuid.uuid4().hex[:8]}"

print("🔍 FULL DEBUG TEST")
print(f"User ID: {user_id}")
print("="*60)

# Step 1: Save a profile
print("\n1️⃣ SAVING PROFILE...")
save_request = {
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
        "message": {
            "messageId": str(uuid.uuid4()),
            "role": "user",
            "parts": [{"text": "save"}],
            "metadata": {
                "skill": "save_user_profile",
                "user_id": user_id,
                "profile_data": {
                    "firstName": "Debug",
                    "lastName": "Test",
                    "email": f"debug.{uuid.uuid4().hex[:8]}@test.com",
                    "city": "Brasília",
                    "state": "DF",
                    "country": "Brasil",
                    "hardSkills": ["Debug", "Testing"],
                    "softSkills": ["Patience"]
                }
            }
        }
    },
    "id": str(uuid.uuid4())
}

response = requests.post(
    "http://localhost:8082/",
    json=save_request,
    headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
    stream=True,
    timeout=10
)

save_worked = False
for line in response.iter_lines():
    if line and b'message' in line:
        try:
            decoded = line.decode('utf-8')
            if decoded.startswith('data: '):
                data = json.loads(decoded[6:])
                result = data.get('result', {})
                if result.get('kind') == 'message':
                    text = result['parts'][0]['text'] if result.get('parts') else ""
                    if "sucesso" in text.lower():
                        print("✅ Profile saved successfully")
                        save_worked = True
                    else:
                        print(f"Response: {text[:100]}...")
                    break
        except:
            pass

if not save_worked:
    print("❌ Save failed, aborting test")
    exit(1)

# Step 2: Retrieve the profile
print("\n2️⃣ RETRIEVING PROFILE...")
print("Sending request with metadata:")
retrieve_request = {
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
        "message": {
            "messageId": str(uuid.uuid4()),
            "role": "user",
            "parts": [{"text": "get profile"}],
            "metadata": {
                "skill": "retrieve_user_profile",
                "user_id": user_id
            }
        }
    },
    "id": str(uuid.uuid4())
}

print(json.dumps(retrieve_request["params"]["message"]["metadata"], indent=2))

response = requests.post(
    "http://localhost:8082/",
    json=retrieve_request,
    headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
    stream=True,
    timeout=10
)

print(f"\nStatus: {response.status_code}")

for line in response.iter_lines():
    if line and b'message' in line:
        try:
            decoded = line.decode('utf-8')
            if decoded.startswith('data: '):
                data = json.loads(decoded[6:])
                result = data.get('result', {})
                if result.get('kind') == 'message':
                    text = result['parts'][0]['text'] if result.get('parts') else ""
                    
                    print("\n📄 RESPONSE:")
                    print(text[:500] + "..." if len(text) > 500 else text)
                    
                    print("\n🔍 ANALYSIS:")
                    if "📋 **Perfil de Usuário**" in text:
                        print("✅ SUCCESS! Native skill executed")
                        print("Profile data should be visible above")
                    elif "Debug Test" in text:
                        print("✅ Profile data found (but maybe not native format)")
                    elif "Você ainda não possui" in text:
                        print("❌ FAILURE! ADK fallback - profile not found")
                        print("\nPossible issues:")
                        print("1. Native skill not being called")
                        print("2. Different user_id being used") 
                        print("3. Session/context issue")
                    
                    break
        except:
            pass

print("\n" + "="*60)
print("Check server logs for '🎯 NATIVE SKILL PATH' messages")