#!/usr/bin/env python3
"""Debug test for native skills"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nai_a2a.executor import NAIAgentExecutor, NATIVE_SKILLS_AVAILABLE

print(f"🔍 NATIVE_SKILLS_AVAILABLE = {NATIVE_SKILLS_AVAILABLE}")

# Test skill extraction
from a2a.types import Message, Role
from nai_a2a.executor import RequestContext

async def test_skill_extraction():
    from nai.agent import root_agent
    executor = NAIAgentExecutor()  # Initialize properly
    
    # Create a test message with skill metadata
    message = Message(
        messageId="test-123",
        role=Role.user,
        parts=[{"text": "show profile"}],
        metadata={
            "skill": "retrieve_user_profile",
            "user_id": "test_user"
        }
    )
    
    context = RequestContext(
        message=message,
        task_id="task-123",
        context_id="context-123"
    )
    
    # Test skill extraction
    skill_name = executor._extract_skill_name(context)
    print(f"\n📋 Extracted skill name: {skill_name}")
    
    # Check if conditions for native skill execution are met
    print(f"\n🔍 Checking conditions:")
    print(f"   skill_name = {skill_name}")
    print(f"   NATIVE_SKILLS_AVAILABLE = {NATIVE_SKILLS_AVAILABLE}")
    print(f"   Would execute native skill? {bool(skill_name and NATIVE_SKILLS_AVAILABLE)}")

if __name__ == "__main__":
    asyncio.run(test_skill_extraction())