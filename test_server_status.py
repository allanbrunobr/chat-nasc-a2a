#!/usr/bin/env python3
"""Check server status and capabilities"""

import requests
import json

print("🔍 Checking A2A server status...")

# 1. Check agent card
response = requests.get("http://localhost:8082/.well-known/agent.json")
if response.status_code == 200:
    agent_card = response.json()
    print("\n✅ Server is running")
    print(f"Agent: {agent_card['name']}")
    print(f"Version: {agent_card['version']}")
    
    print("\n📋 Registered skills:")
    for skill in agent_card['skills']:
        print(f"  - {skill['id']}: {skill['name']}")
        if skill['id'] == 'retrieve_user_profile':
            print(f"    Description: {skill['description']}")
    
    # Check if native skills are in the card
    skill_ids = [s['id'] for s in agent_card['skills']]
    print("\n🔍 Native skill status:")
    print(f"  - retrieve_user_profile: {'✅' if 'retrieve_user_profile' in skill_ids else '❌'}")
    print(f"  - save_user_profile: {'✅' if 'save_user_profile' in skill_ids else '❌'}")
    print(f"  - find_job_matches: {'✅' if 'find_job_matches' in skill_ids else '❌'}")
    print(f"  - retrieve_vacancy: {'✅' if 'retrieve_vacancy' in skill_ids else '❌'}")
    print(f"  - update_state: {'✅' if 'update_state' in skill_ids else '❌'}")
else:
    print("❌ Server not responding")

# 2. Test a simple message to see server logs
print("\n\n🧪 Sending test message to trigger server logs...")
test_request = {
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
        "message": {
            "messageId": "test-status",
            "role": "user",
            "parts": [{"text": "test"}],
            "metadata": {
                "skill": "retrieve_user_profile",
                "user_id": "test123"
            }
        }
    },
    "id": "test-status"
}

print("Check server logs for:")
print("  - NATIVE_SKILLS_AVAILABLE value")
print("  - '🎯 NATIVE SKILL PATH' or '🔄 ADK TOOL PATH' messages")
print("  - Import errors")

response = requests.post(
    "http://localhost:8082/",
    json=test_request,
    timeout=5
)
print(f"\nTest message sent, status: {response.status_code}")