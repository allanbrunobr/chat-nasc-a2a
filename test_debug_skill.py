#!/usr/bin/env python3
"""Debug the retrieve_user_profile skill directly"""

import asyncio
import os
import logging
from dotenv import load_dotenv

# Set up logging to see all debug messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

load_dotenv()

# Import the skill
from nai_a2a.skills.retrieve_user_profile import RetrieveUserProfileSkill

async def test_skill():
    """Test the skill directly"""
    user_id = "dd060639-cb4c-46a2-aac9-764a979b2d50"
    
    print(f"🔍 Testing RetrieveUserProfileSkill directly")
    print(f"User ID: {user_id}")
    print("="*60)
    
    try:
        # Create skill instance
        skill = RetrieveUserProfileSkill()
        
        # Execute skill
        print("\n📤 Executing skill...")
        result = await skill.execute(user_id)
        
        print("\n📄 Raw result:")
        print(f"Type: {type(result)}")
        print(f"Keys: {list(result.keys())[:10] if isinstance(result, dict) else 'Not a dict'}")
        
        # Check metadata
        metadata = result.get("_metadata", {})
        print(f"\n📊 Metadata:")
        print(f"  is_empty: {metadata.get('is_empty')}")
        print(f"  source: {metadata.get('source')}")
        
        # Check main data
        print(f"\n👤 Profile data:")
        print(f"  user_id: {result.get('user_id')}")
        print(f"  name: {result.get('name')}")
        print(f"  email: {result.get('email')}")
        
        # Format for display
        print("\n📋 Formatted display:")
        formatted = skill.format_profile_for_display(result)
        print(formatted[:500] + "..." if len(formatted) > 500 else formatted)
        
        # Final analysis
        print("\n" + "="*60)
        print("🔍 Analysis:")
        if metadata.get("is_empty"):
            print("❌ FAILURE! Skill thinks profile is empty")
        else:
            print("✅ SUCCESS! Skill correctly identified profile")
            if "Allan Bruno" in formatted:
                print("✅ Profile data is correctly formatted")
            else:
                print("⚠️  Profile data exists but formatting might be wrong")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_skill())