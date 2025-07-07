#!/usr/bin/env python3
"""Debug test for retrieve_user_profile"""

import requests
import json
import uuid

# Test with the SAME user that we just saved
user_id = "test_all_37a91db6"  # User from previous test

print(f"🔍 Testing retrieve_user_profile for user: {user_id}")
print("This user SHOULD have a profile (we just saved it)")

request = {
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
        "message": {
            "messageId": str(uuid.uuid4()),
            "role": "user",
            "parts": [{"text": "show profile"}],
            "metadata": {
                "skill": "retrieve_user_profile",
                "user_id": user_id
            }
        }
    },
    "id": str(uuid.uuid4())
}

print("\n📤 Request metadata:")
print(json.dumps(request["params"]["message"]["metadata"], indent=2))

response = requests.post(
    "http://localhost:8082/",
    json=request,
    headers={
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    },
    stream=True,
    timeout=30
)

print(f"\n📡 Status: {response.status_code}")

if response.status_code == 200:
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('data: ') and 'message' in decoded:
                try:
                    data = json.loads(decoded[6:])
                    result = data.get('result', {})
                    if result.get('kind') == 'message':
                        text = result['parts'][0]['text'] if result.get('parts') else ""
                        
                        print("\n📄 Full response:")
                        print(text)
                        
                        # Analyze response
                        print("\n🔍 Analysis:")
                        if "📋 **Perfil de Usuário**" in text:
                            print("✅ NATIVE SKILL - Found profile header")
                        elif "Perfil não encontrado" in text and "ID:" in text:
                            print("✅ NATIVE SKILL - Profile not found with specific format")
                        elif "Você ainda não possui" in text:
                            print("🔄 ADK FALLBACK - Generic ADK message")
                        
                        # Check if profile data is in response
                        if "Test User" in text or "test.user" in text:
                            print("✅ Profile data found in response!")
                        else:
                            print("❌ Profile data NOT found in response")
                        
                        break
                except:
                    pass