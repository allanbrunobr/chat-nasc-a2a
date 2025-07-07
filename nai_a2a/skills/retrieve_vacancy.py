"""
Native A2A skill for searching job vacancies.

This skill searches for job vacancies based on search terms using
the SETASC semantic search API.
"""

import os
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

from nai_a2a.exceptions import (
    ExternalAPIError,
    ValidationError
)

load_dotenv()
logger = logging.getLogger(__name__)

# Get vacancy search URL from environment
SEARCH_VACANCY_URL = os.getenv("SEARCH_VACANCY_URL")
logger.info(f"SEARCH_VACANCY_URL: {SEARCH_VACANCY_URL}")


class RetrieveVacancySkill:
    """Skill for searching job vacancies based on search terms."""
    
    def __init__(self):
        """Initialize the vacancy search skill."""
        self.search_url = SEARCH_VACANCY_URL
        if not self.search_url:
            raise ValueError("SEARCH_VACANCY_URL not configured in environment")
        
        logger.info(f"RetrieveVacancySkill initialized with URL: {self.search_url}")
    
    async def execute(self, search_term: str, **kwargs) -> Dict[str, Any]:
        """
        Search for job vacancies based on the provided search term.
        
        Args:
            search_term: The search term to find vacancies
            **kwargs: Additional parameters (for future extensions)
            
        Returns:
            Dict containing search results with metadata
            
        Raises:
            ValidationError: If search_term is empty
            ExternalAPIError: If the API call fails
        """
        # Validate input
        if not search_term or not search_term.strip():
            raise ValidationError(
                "Search term is required",
                {"field": "search_term", "value": search_term}
            )
        
        search_term = search_term.strip()
        logger.info(f"Searching vacancies with term: '{search_term}'")
        
        try:
            # Make API request
            headers = {"accept": "application/json"}
            params = {"text": search_term}
            
            logger.debug(f"Sending request to {self.search_url} with params: {params}")
            
            response = requests.get(
                self.search_url,
                params=params,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Vacancy search response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                vacancies = data.get("message", [])
                
                # Add metadata to response
                result = {
                    "vacancies": vacancies,
                    "count": len(vacancies),
                    "_metadata": {
                        "searched_at": datetime.utcnow().isoformat(),
                        "source": "a2a_skill",
                        "search_term": search_term,
                        "total_found": len(vacancies)
                    }
                }
                
                logger.info(f"Found {len(vacancies)} vacancies for term '{search_term}'")
                return result
                
            else:
                logger.error(f"Vacancy search failed with status {response.status_code}: {response.text}")
                raise ExternalAPIError(
                    service="vacancy search",
                    status_code=response.status_code,
                    detail=response.text
                )
                
        except requests.exceptions.Timeout:
            logger.error("Vacancy search request timed out")
            raise ExternalAPIError(
                service="vacancy search",
                status_code=0,
                detail="Request timed out after 30 seconds"
            )
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during vacancy search: {e}")
            raise ExternalAPIError(
                service="vacancy search", 
                status_code=0,
                detail=f"Connection error: {str(e)}"
            )
            
        except Exception as e:
            logger.exception(f"Unexpected error during vacancy search: {e}")
            raise ExternalAPIError(
                service="vacancy search",
                status_code=0,
                detail=f"Unexpected error: {str(e)}"
            )
    
    def format_vacancies_for_display(self, result: Dict[str, Any]) -> str:
        """
        Format vacancy search results for user display.
        
        Args:
            result: The result from execute() method
            
        Returns:
            Formatted string for display
        """
        vacancies = result.get("vacancies", [])
        count = result.get("count", 0)
        search_term = result.get("_metadata", {}).get("search_term", "")
        
        if count == 0:
            return f"🔍 Nenhuma vaga encontrada para o termo: **{search_term}**\n\nTente usar outros termos de busca ou seja mais específico."
        
        # Format header
        lines = [
            f"🔍 **Vagas Encontradas**",
            f"Termo de busca: **{search_term}**",
            f"Total de vagas: **{count}**",
            "",
            "---",
            ""
        ]
        
        # Format each vacancy
        for i, vacancy in enumerate(vacancies[:10], 1):  # Show max 10 vacancies
            lines.append(f"### {i}. {vacancy.get('title', 'Vaga sem título')}")
            
            if vacancy.get('company'):
                lines.append(f"**Empresa:** {vacancy['company']}")
            
            if vacancy.get('location'):
                lines.append(f"**Local:** {vacancy['location']}")
            
            if vacancy.get('description'):
                desc = vacancy['description']
                # Truncate long descriptions
                if len(desc) > 200:
                    desc = desc[:200] + "..."
                lines.append(f"**Descrição:** {desc}")
            
            if vacancy.get('requirements'):
                lines.append(f"**Requisitos:** {vacancy['requirements']}")
            
            if vacancy.get('salary'):
                lines.append(f"**Salário:** {vacancy['salary']}")
            
            if vacancy.get('link'):
                lines.append(f"**Link:** {vacancy['link']}")
            
            lines.append("")  # Empty line between vacancies
        
        if count > 10:
            lines.append(f"\n*Mostrando 10 de {count} vagas encontradas*")
        
        return "\n".join(lines)