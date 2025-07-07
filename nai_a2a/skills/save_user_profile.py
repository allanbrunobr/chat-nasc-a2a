"""
Save User Profile Skill for A2A

This skill persists user profile data to the SETASC backend.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from nai_a2a.exceptions import (
    ExternalAPIError,
    ValidationError,
    ProfileIncompleteError
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SaveUserProfileSkill:
    """Native A2A skill for saving user profiles"""
    
    def __init__(self):
        self.persist_url = os.getenv("PERSIST_USER_PROFILE_COMPLETE_URL")
        if not self.persist_url:
            logger.error("PERSIST_USER_PROFILE_COMPLETE_URL not configured")
            raise ValueError("Profile persistence URL not configured")
        
        logger.info(f"SaveUserProfileSkill initialized with URL: {self.persist_url}")
    
    async def execute(self, user_id: str, profile_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Save user profile to backend
        
        Args:
            user_id: User identifier
            profile_data: Complete profile data to save
            **kwargs: Additional parameters (unused)
            
        Returns:
            Dict with status and formatted message
        """
        logger.info(f"Saving profile for user: {user_id}")
        
        # Validate required fields
        if not profile_data:
            raise ValidationError("Profile data is required", {"field": "profile_data"})
        
        # Check for minimal required fields
        required_fields = ["firstName", "lastName", "email"]
        missing_fields = [field for field in required_fields if not profile_data.get(field)]
        
        if missing_fields:
            raise ProfileIncompleteError(
                user_id=user_id,
                operation="save_profile",
                missing_fields=missing_fields
            )
        
        # Prepare request
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "user_id": user_id,
            "perfil_completo": profile_data
        }
        
        try:
            logger.debug(f"Sending profile data: {json.dumps(payload, indent=2)[:500]}...")
            
            response = requests.post(
                self.persist_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Backend response status: {response.status_code}")
            
            if response.status_code in (200, 201):
                logger.info(f"✅ Profile saved successfully for user {user_id}")
                return {
                    "status": "success",
                    "message": self._format_success_message(profile_data),
                    "profile_saved": True
                }
            else:
                logger.error(f"Backend error {response.status_code}: {response.text}")
                raise ExternalAPIError(
                    service="profile persistence",
                    status_code=response.status_code,
                    response_text=response.text
                )
                
        except requests.exceptions.Timeout:
            logger.error("Timeout saving profile")
            raise ExternalAPIError("profile persistence", error_type="timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise ExternalAPIError("profile persistence", response_text=str(e))
    
    def _format_success_message(self, profile_data: Dict[str, Any]) -> str:
        """Format a success message for the user"""
        name = profile_data.get("firstName", "")
        
        # Build profile summary
        summary_parts = []
        
        # Personal info
        if profile_data.get("firstName") and profile_data.get("lastName"):
            summary_parts.append(f"👤 Nome: {profile_data['firstName']} {profile_data['lastName']}")
        
        # Location
        if profile_data.get("city") and profile_data.get("state"):
            summary_parts.append(f"📍 Localização: {profile_data['city']}/{profile_data['state']}")
        
        # Skills
        hard_skills = profile_data.get("hardSkills", [])
        soft_skills = profile_data.get("softSkills", [])
        if hard_skills:
            summary_parts.append(f"💻 Habilidades técnicas: {len(hard_skills)} cadastradas")
        if soft_skills:
            summary_parts.append(f"🤝 Habilidades comportamentais: {len(soft_skills)} cadastradas")
        
        # Experience
        experiences = profile_data.get("experiences", [])
        if experiences:
            summary_parts.append(f"💼 Experiências: {len(experiences)} registradas")
        
        # Education
        education = profile_data.get("education", [])
        if education:
            summary_parts.append(f"🎓 Formação: {len(education)} registradas")
        
        # Build final message
        message = f"✅ Perfil salvo com sucesso{f', {name}' if name else ''}!\n\n"
        if summary_parts:
            message += "📋 Resumo do perfil:\n" + "\n".join(summary_parts)
        
        message += "\n\nAgora posso ajudar você a encontrar oportunidades de carreira que combinem com seu perfil!"
        
        return message