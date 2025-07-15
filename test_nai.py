#!/usr/bin/env python3
"""Test script for NAI ADK API (without A2A)"""

import requests
import json

# Base URL for ADK API
BASE_URL = "http://localhost:8080"

def test_nai():
    """Test basic NAI functionality"""
    
    # Test user ID
    user_id = "test_user_123"
    
    # Test cases
    test_messages = [
        "Olá",
        "Quero criar meu perfil",
        "Meu nome é João Silva, tenho 25 anos, sou formado em Engenharia",
        "Mostre meu perfil",
        "Quero ver carreiras compatíveis",
        "Analise meu ATS score"
    ]
    
    print("🤖 Testing NAI ADK API...")
    print(f"📍 URL: {BASE_URL}/run")
    print(f"👤 User ID: {user_id}\n")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {message}")
        print('='*60)
        
        payload = {
            "user_id": user_id,
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/run",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                print(f"Response: {result['messages'][-1]['content'][:200]}...")
                if 'state' in result:
                    print(f"State updated: {json.dumps(result['state'], indent=2)}")
            else:
                print(f"❌ Error: Status {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            
        input("\nPress Enter for next test...")

if __name__ == "__main__":
    print("🚀 NAI ADK API Test Script")
    print("⚠️  Make sure the ADK server is running on port 8080")
    print("   Run with: uvicorn api.main:app --reload --port 8080\n")
    
    input("Press Enter to start tests...")
    test_nai()