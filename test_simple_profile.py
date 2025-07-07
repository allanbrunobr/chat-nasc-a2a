#!/usr/bin/env python3
"""Simple test for profile retrieval"""

import requests
import json
import uuid
import time

def test_profile():
    user_id = f"test_native_{uuid.uuid4().hex[:8]}"
    
    print(f"🧪 Testing native skill execution")
    print(f"👤 User ID: {user_id}")
    
    # Test 1: Try retrieve profile (should fail - no profile yet)
    print("\n1️⃣ Testing retrieve_user_profile...")
    
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
    
    response = requests.post(
        "http://localhost:8082/",
        json=request,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    
    # Test 2: Save profile
    print("\n2️⃣ Testing save_user_profile...")
    
    profile_data = {
        "firstName": "Test",
        "lastName": "Native",
        "email": f"test.native.{uuid.uuid4().hex[:8]}@example.com",
        "phone": "11999999999",
        "city": "São Paulo",
        "state": "SP",
        "country": "Brasil"
    }
    
    request = {
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
                    "profile_data": profile_data
                }
            }
        },
        "id": str(uuid.uuid4())
    }
    
    response = requests.post(
        "http://localhost:8082/",
        json=request,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    
    time.sleep(2)
    
    # Test 3: Retrieve again (should work now)
    print("\n3️⃣ Testing retrieve_user_profile again...")
    
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
    
    response = requests.post(
        "http://localhost:8082/",
        json=request,
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        },
        stream=True,
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    
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
                            print(f"\n📄 Response preview: {text[:200]}...")
                            
                            # Check for native skill markers
                            if "📋 **Perfil de Usuário**" in text:
                                print("✅ USING NATIVE SKILL!")
                            elif "Você ainda não possui" in text:
                                print("🔄 USING ADK TOOL")
                            break
                    except:
                        pass

if __name__ == "__main__":
    test_profile()