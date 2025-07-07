#!/usr/bin/env python3
"""Check if native skills can be imported"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Checking native skills imports...")

try:
    from nai_a2a.skills.retrieve_user_profile import RetrieveUserProfileSkill
    print("✅ RetrieveUserProfileSkill imported successfully")
except ImportError as e:
    print(f"❌ Failed to import RetrieveUserProfileSkill: {e}")

try:
    from nai_a2a.skills.save_user_profile import SaveUserProfileSkill
    print("✅ SaveUserProfileSkill imported successfully")
except ImportError as e:
    print(f"❌ Failed to import SaveUserProfileSkill: {e}")

try:
    from nai_a2a.skills.find_job_matches import FindJobMatchesSkill
    print("✅ FindJobMatchesSkill imported successfully")
except ImportError as e:
    print(f"❌ Failed to import FindJobMatchesSkill: {e}")

print("\n📂 Checking directory structure:")
skills_dir = os.path.join(os.path.dirname(__file__), "nai_a2a", "skills")
if os.path.exists(skills_dir):
    print(f"Skills directory exists: {skills_dir}")
    print("Files:", os.listdir(skills_dir))
else:
    print(f"❌ Skills directory not found: {skills_dir}")