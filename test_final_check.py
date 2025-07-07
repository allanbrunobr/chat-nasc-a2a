#!/usr/bin/env python3
"""Final test to check which implementation is being used"""

import requests
import json
import uuid

print("🧪 Testing which implementation is used for retrieve_user_profile")
print("="*60)

user_id = "test_implementation_check"

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

print(f"📤 Sending request for user: {user_id}")
print(f"   Skill: retrieve_user_profile")

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
    
    print(f"\n📡 Response status: {response.status_code}")
    
    if response.status_code == 200:
        print("\n🔍 Analyzing response to determine implementation...")
        
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data: ') and 'message' in decoded:
                    try:
                        data = json.loads(decoded[6:])
                        result = data.get('result', {})
                        if result.get('kind') == 'message':
                            text = result['parts'][0]['text'] if result.get('parts') else ""
                            
                            # Check response patterns
                            print("\n📄 Response analysis:")
                            
                            # Native skill indicators
                            if "📋 **Perfil de Usuário**" in text:
                                print("✅ NATIVE SKILL - Found '📋 **Perfil de Usuário**' header")
                            elif "Perfil não encontrado" in text and "ID: " in text:
                                print("✅ NATIVE SKILL - Found specific error format with ID")
                            
                            # ADK tool indicators  
                            elif "Você ainda não possui um perfil cadastrado" in text:
                                print("🔄 ADK TOOL - Found ADK-style message")
                            elif "Vamos criar um agora?" in text:
                                print("🔄 ADK TOOL - Found ADK prompt pattern")
                            
                            print(f"\nResponse preview: {text[:150]}...")
                            
                            print("\n" + "="*60)
                            print("CONCLUSION:")
                            if "📋 **Perfil de Usuário**" in text or ("Perfil não encontrado" in text and "ID: " in text):
                                print("✅ The retrieve_user_profile is using NATIVE A2A SKILL")
                            else:
                                print("🔄 The retrieve_user_profile is using ADK TOOL")
                            print("="*60)
                            
                            break
                    except Exception as e:
                        pass
                        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n📝 Note: Check server logs for detailed execution path (look for 🎯 or 🔄 emojis)")