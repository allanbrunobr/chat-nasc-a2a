#!/usr/bin/env python3
"""Test skill detection in A2A"""

import requests
import json
import uuid

user_id = "dd060639-cb4c-46a2-aac9-764a979b2d50"

print("🧪 Testing skill detection and execution path")
print("="*60)

# Test 1: With explicit skill in metadata
print("\n1️⃣ Test with explicit skill in metadata:")
request1 = {
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
        "message": {
            "messageId": str(uuid.uuid4()),
            "role": "user",
            "parts": [{"text": "test"}],
            "metadata": {
                "skill": "retrieve_user_profile",
                "user_id": user_id
            }
        }
    },
    "id": str(uuid.uuid4())
}

print("Request metadata:", json.dumps(request1["params"]["message"]["metadata"], indent=2))

# Test 2: Without skill in metadata
print("\n2️⃣ Test without skill in metadata:")
request2 = {
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
        "message": {
            "messageId": str(uuid.uuid4()),
            "role": "user",
            "parts": [{"text": "mostre meu perfil"}],
            "metadata": {
                "user_id": user_id
            }
        }
    },
    "id": str(uuid.uuid4())
}

print("Request metadata:", json.dumps(request2["params"]["message"]["metadata"], indent=2))

# Execute both tests
for i, request in enumerate([request1, request2], 1):
    print(f"\n{'='*60}")
    print(f"Executing test {i}...")
    
    try:
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
                                
                                # Just show first 150 chars
                                preview = text[:150] + "..." if len(text) > 150 else text
                                print(f"Response: {preview}")
                                
                                if "📋 **Perfil" in text:
                                    print("✅ NATIVE SKILL")
                                elif "Você ainda não" in text:
                                    print("🔄 ADK FALLBACK")
                                
                                break
                        except:
                            pass
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*60)
print("Summary:")
print("- Test 1 (with skill metadata) should use NATIVE skill")
print("- Test 2 (without skill metadata) should use ADK")
print("If both show ADK fallback, the native skill execution is not working")