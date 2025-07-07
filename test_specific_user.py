#!/usr/bin/env python3
"""Test retrieve_user_profile with specific user ID"""

import requests
import json
import uuid

# Use the specific user ID provided
user_id = "dd060639-cb4c-46a2-aac9-764a979b2d50"

print(f"🔍 Testing retrieve_user_profile for user: {user_id}")

request = {
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

print("\n📤 Sending request...")
print(f"Skill: retrieve_user_profile")
print(f"User ID: {user_id}")

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
                        
                        print("\n📄 Response:")
                        print(text)
                        
                        print("\n" + "="*60)
                        print("🔍 Analysis:")
                        
                        # Check which implementation was used
                        if "📋 **Perfil de Usuário**" in text:
                            print("✅ USING NATIVE A2A SKILL")
                            print("   - Found native skill profile header")
                            
                            # Extract key info if present
                            if "Nome:" in text:
                                lines = text.split('\n')
                                for line in lines:
                                    if "Nome:" in line or "Email:" in line or "Localização:" in line:
                                        print(f"   - {line.strip()}")
                        
                        elif "Perfil não encontrado" in text and "ID:" in text:
                            print("✅ USING NATIVE A2A SKILL")
                            print("   - Native skill error format (profile not found)")
                        
                        elif "Você ainda não possui" in text:
                            print("🔄 USING ADK TOOL (FALLBACK)")
                            print("   - Generic ADK message")
                        
                        else:
                            print("❓ UNKNOWN FORMAT")
                        
                        print("="*60)
                        break
                except:
                    pass
else:
    print(f"❌ Error: {response.text}")