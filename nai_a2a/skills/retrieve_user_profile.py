"""
Native A2A skill for retrieving user profile.

This skill provides direct access to the user profile API without
going through the ADK agent, improving performance and control.
"""

import os
import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from dotenv import load_dotenv

from nai_a2a.exceptions import (
    UserNotFoundException,
    ExternalAPIError,
    DatabaseConnectionError
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class RetrieveUserProfileSkill:
    """
    A2A skill for retrieving user profile information.
    
    This skill directly calls the SETASC API to fetch user profile data,
    providing faster response times and better error handling.
    """
    
    def __init__(self):
        """Initialize the skill with required configuration"""
        self.base_url = os.getenv("USER_PROFILE_URL")
        if not self.base_url:
            raise ValueError("USER_PROFILE_URL not configured in environment")
        
        # Check if we need authentication for the API
        self.use_auth = os.getenv("USE_GOOGLE_AUTH", "false").lower() == "true"
        
        logger.info(f"RetrieveUserProfileSkill initialized with URL: {self.base_url}")
    
    def get_identity_token(self, audience: str) -> str:
        """Generate a Google Identity Token for authentication in Cloud Functions"""
        try:
            return id_token.fetch_id_token(Request(), audience)
        except Exception as e:
            logger.error(f"Failed to fetch identity token: {e}")
            raise ExternalAPIError("Google Auth", response_text=str(e))
    
    async def execute(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Retrieve user profile from the SETASC API.
        
        Args:
            user_id: The user ID to fetch profile for
            **kwargs: Additional parameters (for future extensibility)
            
        Returns:
            Dict containing the user profile data
            
        Raises:
            UserNotFoundException: If user profile not found
            ExternalAPIError: If API call fails
        """
        logger.info(f"Retrieving profile for user: {user_id}")
        
        if not user_id:
            raise ValueError("user_id is required")
        
        # Construct the API URL
        url = f"{self.base_url}?user_id={user_id}"
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        
        # Add authentication if required
        if self.use_auth:
            try:
                token = self.get_identity_token(self.base_url)
                headers["Authorization"] = f"Bearer {token}"
            except Exception as e:
                logger.error(f"Authentication failed: {e}")
                raise
        
        # Make the API request
        try:
            logger.debug(f"Making request to: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            
            # Log response details for debugging
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            # Handle different response codes
            if response.status_code == 404:
                raise UserNotFoundException(user_id)
            
            if response.status_code != 200:
                raise ExternalAPIError(
                    "User Profile API",
                    status_code=response.status_code,
                    response_text=response.text
                )
            
            # Parse response
            try:
                data = response.json()
                logger.debug(f"Parsed data type: {type(data)}")
                logger.debug(f"Data keys: {list(data.keys())[:10] if isinstance(data, dict) else 'Not a dict'}")
                logger.debug(f"Data preview: {str(data)[:200]}...")
            except ValueError as e:
                logger.error(f"Failed to parse API response: {response.text[:500]}")
                raise ExternalAPIError(
                    "User Profile API",
                    response_text=f"Invalid JSON response: {str(e)}"
                )
            
            # Validate response structure
            if not isinstance(data, dict):
                raise ExternalAPIError(
                    "User Profile API",
                    response_text=f"Expected dict response, got {type(data)}"
                )
            
            # Check if profile exists
            # The API returns user data directly at the root level
            if data.get("user_id") and data.get("name"):
                # Profile exists, return the full data
                logger.info(f"Profile found for user {user_id}: {data.get('name')}")
                data["_metadata"] = {
                    "retrieved_at": datetime.utcnow().isoformat(),
                    "source": "a2a_skill",
                    "user_id": user_id,
                    "is_empty": False
                }
                logger.info(f"Successfully retrieved profile for user {user_id}")
                return data
            else:
                # No user data, return empty profile
                logger.info(f"User {user_id} has no profile created yet")
                return self._create_empty_profile_response(user_id)
            
        except requests.Timeout:
            raise ExternalAPIError(
                "User Profile API",
                response_text="Request timeout after 30 seconds"
            )
        except requests.ConnectionError as e:
            raise ExternalAPIError(
                "User Profile API",
                response_text=f"Connection error: {str(e)}"
            )
        except requests.RequestException as e:
            raise ExternalAPIError(
                "User Profile API",
                response_text=f"Request failed: {str(e)}"
            )
    
    def _is_profile_created(self, perfil_profissional: Dict[str, Any]) -> bool:
        """Check if profile has been created (has any content)"""
        return any([
            bool(perfil_profissional.get("visao_atual")),
            bool(perfil_profissional.get("visao_futuro")),
            perfil_profissional.get("formacoes"),
            perfil_profissional.get("experiencias"),
            perfil_profissional.get("capacidades"),
            perfil_profissional.get("conhecimentos"),
        ])
    
    def _create_empty_profile_response(self, user_id: str) -> Dict[str, Any]:
        """Create an empty profile response structure"""
        return {
            "user_id": user_id,
            "perfilProfissional": {
                "visao_atual": "",
                "visao_futuro": "",
                "formacoes": [],
                "experiencias": [],
                "capacidades": [],
                "conhecimentos": [],
                "hardSkills": [],
                "softSkills": []
            },
            "_metadata": {
                "retrieved_at": datetime.utcnow().isoformat(),
                "source": "a2a_skill",
                "user_id": user_id,
                "is_empty": True
            }
        }
    
    def format_profile_for_display(self, profile_data: Dict[str, Any]) -> str:
        """
        Format profile data for user-friendly display.
        
        Args:
            profile_data: The raw profile data from API
            
        Returns:
            Formatted string for display to user
        """
        if profile_data.get("_metadata", {}).get("is_empty"):
            return "Você ainda não possui um perfil cadastrado. Vamos criar um agora?"
        
        # Build header with basic info
        sections = [
            "📋 **Perfil de Usuário**",
            "",
            f"👤 **Nome**: {profile_data.get('name', 'Não informado')}",
            f"📧 **Email**: {profile_data.get('email', 'Não informado')}",
            f"📱 **Telefone**: {profile_data.get('phone', 'Não informado')}",
            f"📍 **Localização**: {profile_data.get('city', '')}, {profile_data.get('state', '')}",
            ""
        ]
        
        # Summary info
        summary = profile_data.get('summary', {})
        if summary:
            sections.append(f"📊 **Resumo do Perfil**:")
            sections.append(f"  • Experiências: {summary.get('total_experiences', 0)}")
            sections.append(f"  • Habilidades técnicas: {summary.get('total_skills', 0)}")
            sections.append(f"  • Habilidades comportamentais: {summary.get('total_soft_skills', 0)}")
            sections.append(f"  • Formações: {summary.get('total_education', 0)}")
            sections.append(f"  • Certificações: {summary.get('total_certifications', 0)}")
            sections.append("")
        
        # Education
        education = profile_data.get("education", [])
        if education:
            sections.append("📚 **Formação Acadêmica**:")
            for edu in education[:3]:  # Show max 3
                sections.append(f"  • {edu.get('course', 'N/A')} - {edu.get('institution', 'N/A')} ({edu.get('status', 'N/A')})")
            if len(education) > 3:
                sections.append(f"  • ... e mais {len(education) - 3} formações")
            sections.append("")
        
        # Experience
        experiences = profile_data.get("experiences", [])
        if experiences:
            sections.append("💼 **Experiência Profissional**:")
            for exp in experiences[:3]:  # Show max 3
                sections.append(f"  • {exp.get('position', 'N/A')} na {exp.get('company', 'N/A')}")
            if len(experiences) > 3:
                sections.append(f"  • ... e mais {len(experiences) - 3} experiências")
            sections.append("")
        
        # Skills
        skills = profile_data.get("skills", [])
        if skills:
            skill_names = [s.get('skill', '') for s in skills[:10] if s.get('skill')]
            if skill_names:
                sections.append(f"🔧 **Habilidades Técnicas**: {', '.join(skill_names)}")
                if len(skills) > 10:
                    sections.append(f"  ... e mais {len(skills) - 10} habilidades")
                sections.append("")
        
        # Soft skills
        soft_skills = profile_data.get("soft_skills", [])
        if soft_skills:
            soft_skill_names = [s.get('skill', '') for s in soft_skills if s.get('skill')]
            if soft_skill_names:
                sections.append(f"🤝 **Habilidades Comportamentais**: {', '.join(soft_skill_names)}")
                sections.append("")
        
        # Certifications
        certifications = profile_data.get("certifications", [])
        if certifications:
            sections.append(f"🏆 **Certificações**: {len(certifications)} certificação(ões)")
            for cert in certifications[:3]:  # Show max 3
                sections.append(f"  • {cert.get('name', 'N/A')} - {cert.get('institution', 'N/A')}")
            if len(certifications) > 3:
                sections.append(f"  • ... e mais {len(certifications) - 3} certificações")
        
        return "\n".join(sections)