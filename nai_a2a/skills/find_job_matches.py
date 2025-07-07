"""
Find Job Matches Skill for A2A

This skill searches for job opportunities that match the user's profile.
"""

import os
import logging
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from nai_a2a.exceptions import (
    ExternalAPIError,
    UserNotFoundException,
    ProfileIncompleteError
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FindJobMatchesSkill:
    """Native A2A skill for finding job matches"""
    
    def __init__(self):
        # Try improved URL first, fallback to old one
        self.match_url = os.getenv("RETRIEVE_MATCH_IMPROVED_URL") or os.getenv("RETRIEVE_MATCH_URL")
        if not self.match_url:
            logger.error("No match URL configured")
            raise ValueError("Match service URL not configured")
        
        self.is_improved_api = "setasc-search-improved" in self.match_url
        logger.info(f"FindJobMatchesSkill initialized with URL: {self.match_url}")
        logger.info(f"Using {'improved' if self.is_improved_api else 'legacy'} API")
    
    async def execute(self, user_id: str, limit: Optional[int] = 10, **kwargs) -> Dict[str, Any]:
        """
        Find job matches for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of matches to return (default: 10)
            **kwargs: Additional parameters (unused)
            
        Returns:
            Dict with matches and formatted message
        """
        logger.info(f"Finding job matches for user: {user_id}")
        
        try:
            if self.is_improved_api:
                # New API uses POST
                response = requests.post(
                    self.match_url,
                    json={"user_id": user_id, "limit": limit},
                    timeout=30
                )
            else:
                # Legacy API uses GET
                response = requests.get(
                    self.match_url,
                    params={"userId": user_id},
                    timeout=10
                )
            
            logger.info(f"Match service response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Process matches based on API version
                if self.is_improved_api:
                    matches = self._process_improved_matches(data)
                    search_terms = data.get("search_terms_used", [])
                else:
                    matches = data.get("matches", [])
                    search_terms = []
                
                if not matches:
                    return {
                        "status": "no_matches",
                        "message": self._format_no_matches_message(),
                        "matches": []
                    }
                
                # Format response
                return {
                    "status": "success",
                    "message": self._format_matches_message(matches, search_terms),
                    "matches": matches[:limit],  # Limit results
                    "total_found": len(matches),
                    "search_terms": search_terms
                }
                
            elif response.status_code == 404:
                raise UserNotFoundException(user_id)
            else:
                raise ExternalAPIError(
                    service="match service",
                    status_code=response.status_code,
                    response_text=response.text
                )
                
        except requests.exceptions.Timeout:
            logger.error("Timeout finding matches")
            raise ExternalAPIError("match service", error_type="timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise ExternalAPIError("match service", response_text=str(e))
    
    def _process_improved_matches(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process matches from improved API"""
        matches = []
        
        for match in data.get("matches", []):
            processed_match = {
                "vacancy_id": match.get("vacancy_id"),
                "vacancy_title": match.get("title"),
                "company_name": match.get("company_name", f"Empresa {match.get('company_id', 'N/A')}"),
                "location": match.get("location", ""),
                "match_percentage": int(match.get("final_score", 0) * 100),
                "matched_terms": match.get("matched_terms", []),
                "match_diversity": match.get("match_diversity", 0),
                "salary_range": match.get("salary_range", ""),
                "contract_type": match.get("contract_type", ""),
                "requirements": match.get("requirements", []),
                "benefits": match.get("benefits", [])
            }
            matches.append(processed_match)
        
        # Sort by match percentage
        matches.sort(key=lambda x: x["match_percentage"], reverse=True)
        
        return matches
    
    def _format_matches_message(self, matches: List[Dict[str, Any]], search_terms: List[str]) -> str:
        """Format a message with job matches"""
        total = len(matches)
        
        message = f"🎯 Encontrei {total} oportunidade{'s' if total > 1 else ''} que combina{'m' if total > 1 else ''} com seu perfil!\n\n"
        
        # Show search terms if available
        if search_terms:
            # Handle both string and dict formats for search terms
            if isinstance(search_terms[0], dict):
                # Extract term strings from dict format
                term_strings = []
                for term in search_terms[:5]:
                    if isinstance(term, dict) and 'term' in term:
                        term_strings.append(term['term'])
                    elif isinstance(term, str):
                        term_strings.append(term)
                if term_strings:
                    message += f"🔍 Termos de busca utilizados: {', '.join(term_strings)}\n\n"
            else:
                # Already strings
                message += f"🔍 Termos de busca utilizados: {', '.join(search_terms[:5])}\n\n"
        
        # Show top matches
        message += "📋 Melhores oportunidades:\n\n"
        
        for i, match in enumerate(matches[:5], 1):
            title = match.get("vacancy_title", "Vaga sem título")
            company = match.get("company_name", "Empresa não informada")
            location = match.get("location", "")
            percentage = match.get("match_percentage", 0)
            
            message += f"{i}. **{title}**\n"
            message += f"   🏢 {company}\n"
            if location:
                message += f"   📍 {location}\n"
            message += f"   ✅ Compatibilidade: {percentage}%\n"
            
            # Show matched terms if available
            matched_terms = match.get("matched_terms", [])
            if matched_terms:
                message += f"   🎯 Pontos em comum: {', '.join(matched_terms[:3])}\n"
            
            message += "\n"
        
        if total > 5:
            message += f"... e mais {total - 5} oportunidades disponíveis!\n\n"
        
        message += "💡 Gostaria de ver mais detalhes sobre alguma vaga específica?"
        
        return message
    
    def _format_no_matches_message(self) -> str:
        """Format message when no matches are found"""
        return (
            "😔 Não encontrei oportunidades que correspondam ao seu perfil no momento.\n\n"
            "Mas não desanime! Aqui estão algumas sugestões:\n\n"
            "1. 📝 Atualize seu perfil com mais habilidades e experiências\n"
            "2. 🎯 Considere expandir sua área de interesse\n"
            "3. 📚 Busque cursos para desenvolver novas competências\n"
            "4. 🔄 Tente novamente em alguns dias - novas vagas são cadastradas frequentemente\n\n"
            "Posso ajudar você a identificar áreas de desenvolvimento ou buscar cursos?"
        )