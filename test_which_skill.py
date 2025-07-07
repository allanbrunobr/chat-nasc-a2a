#!/usr/bin/env python3
"""Test to see which implementation is being used for retrieve_user_profile"""

import requests
import json
import uuid

def test_retrieve_user_profile():
    """Test retrieve_user_profile to see if native skill or ADK tool is used"""
    
    user_id = "test_user_123"
    
    print("🧪 Testing retrieve_user_profile")
    print(f"👤 User ID: {user_id}")
    print("="*60)
    
    # Create request with skill metadata
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
    
    print("📤 Sending request with skill metadata...")
    print(f"Skill: retrieve_user_profile")
    
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
        
        print(f"\n📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("\n🌊 Streaming response:")
            
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data: '):
                        try:
                            data = json.loads(decoded[6:])
                            result = data.get('result', {})
                            
                            # Look for task metadata that indicates native skill
                            if result.get('kind') == 'task':
                                status = result.get('status', {})
                                metadata = status.get('metadata', {})
                                if 'native' in metadata:
                                    print(f"\n✅ NATIVE SKILL USED! Metadata: {metadata}")
                                    return
                            
                            # Check message content for clues
                            elif result.get('kind') == 'message':
                                text = result['parts'][0]['text'] if result.get('parts') else ""
                                
                                # Native skill has specific formatting
                                if "📋 **Perfil de Usuário**" in text:
                                    print("\n✅ Response format suggests NATIVE SKILL")
                                elif "Perfil não encontrado" in text and "ID: " in text:
                                    print("\n✅ Error format suggests NATIVE SKILL")
                                else:
                                    print("\n🔄 Response format suggests ADK TOOL")
                                
                                print(f"\nFirst 200 chars of response: {text[:200]}...")
                                break
                        except:
                            pass
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_retrieve_user_profile()