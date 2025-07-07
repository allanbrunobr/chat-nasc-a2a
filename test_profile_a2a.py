#!/usr/bin/env python3
"""Test A2A retrieve_user_profile with Allan's ID"""

import requests
import json
import uuid

# Allan's user ID
user_id = "dd060639-cb4c-46a2-aac9-764a979b2d50"

print(f"🔍 Testing A2A retrieve_user_profile for Allan Bruno")
print(f"User ID: {user_id}")
print("="*60)

# Test via A2A protocol
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

print("\n📤 Sending request to A2A server on port 8082...")

try:
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
    
    print(f"📡 Status: {response.status_code}")
    
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
                            
                            print("\n📄 Response preview:")
                            print(text[:500] + "..." if len(text) > 500 else text)
                            
                            print("\n" + "="*60)
                            print("🔍 Analysis:")
                            
                            if "Allan Bruno" in text:
                                print("✅ SUCCESS! Profile retrieved correctly via A2A native skill")
                                print("✅ Name found in response")
                            elif "allanbruno@gmail.com" in text:
                                print("✅ SUCCESS! Email found - profile data is present")
                            elif "📋 **Perfil de Usuário**" in text:
                                print("✅ SUCCESS! Native skill format detected")
                            elif "Você ainda não possui" in text:
                                print("❌ FAILURE! Skill thinks profile doesn't exist")
                                print("   The native skill is not working correctly")
                            else:
                                print("⚠️  Unknown response format")
                            
                            break
                    except:
                        pass
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {e}")

print("\n✨ Test complete!")