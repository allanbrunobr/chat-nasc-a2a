#!/usr/bin/env python3
"""Test all native A2A skills"""

import requests
import json
import uuid
import time

BASE_URL = "http://localhost:8082"

def test_skill(skill_name, metadata, description):
    """Test a single skill"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {description}")
    print(f"Skill: {skill_name}")
    print("="*60)
    
    request = {
        "jsonrpc": "2.0",
        "method": "message/stream",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"text": f"test {skill_name}"}],
                "metadata": metadata
            }
        },
        "id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(
            BASE_URL + "/",
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
            message_found = False
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data: ') and 'message' in decoded:
                        try:
                            data = json.loads(decoded[6:])
                            result = data.get('result', {})
                            if result.get('kind') == 'message':
                                message_found = True
                                text = result['parts'][0]['text'] if result.get('parts') else ""
                                
                                # Check for native skill markers
                                if any(marker in text for marker in ["📋", "✅", "🔍", "❌"]):
                                    print("✅ NATIVE SKILL EXECUTED")
                                else:
                                    print("🔄 FALLBACK TO ADK")
                                
                                print(f"\n📄 Response preview:")
                                print(text[:300] + "..." if len(text) > 300 else text)
                                break
                        except:
                            pass
            
            if not message_found:
                print("⚠️ No message in response")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    time.sleep(2)  # Delay between tests

def main():
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║           Testing All NAI A2A Native Skills           ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    # Generate unique user ID for tests
    test_user_id = f"test_all_{uuid.uuid4().hex[:8]}"
    print(f"Test User ID: {test_user_id}")
    
    # Test 1: Save Profile (to have data for other tests)
    test_skill(
        "save_user_profile",
        {
            "skill": "save_user_profile",
            "user_id": test_user_id,
            "profile_data": {
                "firstName": "Test",
                "lastName": "User",
                "email": f"test.{uuid.uuid4().hex[:8]}@example.com",
                "city": "São Paulo",
                "state": "SP",
                "hardSkills": ["Python", "Java", "SQL"],
                "softSkills": ["Liderança", "Comunicação"]
            }
        },
        "Save User Profile"
    )
    
    # Test 2: Retrieve Profile
    test_skill(
        "retrieve_user_profile",
        {
            "skill": "retrieve_user_profile",
            "user_id": test_user_id
        },
        "Retrieve User Profile"
    )
    
    # Test 3: Find Job Matches
    test_skill(
        "find_job_matches",
        {
            "skill": "find_job_matches",
            "user_id": test_user_id,
            "limit": 5
        },
        "Find Job Matches"
    )
    
    # Test 4: Retrieve Vacancy
    test_skill(
        "retrieve_vacancy",
        {
            "skill": "retrieve_vacancy",
            "user_id": test_user_id,
            "search_term": "desenvolvedor python"
        },
        "Search Vacancies"
    )
    
    # Test 5: Update State
    test_skill(
        "update_state",
        {
            "skill": "update_state",
            "user_id": test_user_id,
            "content": "Adicione que tenho experiência com Docker e Kubernetes"
        },
        "Update Profile with AI"
    )
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/.well-known/agent.json", timeout=2)
        if response.status_code == 200:
            print("✅ A2A server is running")
            main()
        else:
            print("❌ A2A server returned error")
    except:
        print("❌ A2A server is not running on port 8082")
        print("Please start the server first with: python start_servers.py")