#!/usr/bin/env python3
"""Test retrieve_user_profile with Allan's user ID"""

import os
import requests
import json
import uuid

# Allan's user ID
user_id = "dd060639-cb4c-46a2-aac9-764a979b2d50"

print(f"🔍 Testing retrieve_user_profile for Allan Bruno")
print(f"User ID: {user_id}")
print("="*60)

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
    # First, restart the server
    print("Starting A2A server...")
    import subprocess
    import time
    
    # Start server in background
    process = subprocess.Popen(
        ["python", "-m", "nai_a2a"],
        cwd="/Users/bruno/0 - AI projects/Xertica - AI/nai-api-a2a",
        env={**os.environ, "A2A_PORT": "8082", "PYTHONPATH": "/Users/bruno/0 - AI projects/Xertica - AI/nai-api-a2a:/opt/anaconda3/lib/python3.12/site-packages"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(10)
    
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
                            
                            # Check if profile data is present
                            if "Allan Bruno" in text:
                                print("✅ SUCCESS! Profile data found")
                                print("✅ NATIVE SKILL is working correctly!")
                            elif "📋 **Perfil de Usuário**" in text:
                                print("✅ NATIVE SKILL format detected")
                                if "allanbruno@gmail.com" in text:
                                    print("✅ Email found - profile is correct")
                            elif "Você ainda não possui" in text:
                                print("❌ FAILURE! Using ADK fallback")
                                print("Profile not being retrieved correctly")
                            
                            break
                    except:
                        pass
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {e}")
finally:
    # Kill the server
    if 'process' in locals():
        process.terminate()
        print("\nServer stopped.")

