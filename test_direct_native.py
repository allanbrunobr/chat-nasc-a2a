#!/usr/bin/env python3
"""Test native skill directly"""

import asyncio
import sys
import os

# Add path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_native_skill():
    try:
        print("🧪 Testing native skill directly...")
        
        # Import and test
        from nai_a2a.skills.retrieve_user_profile import RetrieveUserProfileSkill
        
        skill = RetrieveUserProfileSkill()
        print(f"✅ Skill initialized")
        print(f"   URL: {skill.base_url}")
        
        # Test with known user
        user_id = "dd060639-cb4c-46a2-aac9-764a979b2d50"
        print(f"\n📋 Testing with user: {user_id}")
        
        result = await skill.execute(user_id)
        
        print(f"\n📄 Result:")
        print(f"   Type: {type(result)}")
        
        if result.get("_metadata", {}).get("is_empty"):
            print("   ❌ Profile is empty (not found)")
        else:
            print("   ✅ Profile found!")
            print(f"   Name: {result.get('firstName')} {result.get('lastName')}")
            print(f"   Email: {result.get('email')}")
            
        # Test formatting
        formatted = skill.format_profile_for_display(result)
        print(f"\n📄 Formatted output preview:")
        print(formatted[:200] + "..." if len(formatted) > 200 else formatted)
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_native_skill())