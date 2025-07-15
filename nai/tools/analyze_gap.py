"""
Tool for analyzing gaps between candidate profile and job vacancy
"""
from google.adk.tools import FunctionTool, ToolContext
import requests
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def analyze_gap(tool_context: ToolContext, vacancy_id: str) -> dict:
    """
    Analyzes gaps between user profile and a specific job vacancy
    
    Args:
        tool_context: ADK tool context containing session info
        vacancy_id: ID of the job vacancy to analyze
    
    Returns:
        Dict containing gap analysis results
    """
    try:
        # Get user ID from session
        user_id = tool_context.session.get("user_id")
        if not user_id:
            logger.error("No user_id found in session")
            return {
                "status": "error",
                "message": "Usuário não identificado. Por favor, faça login novamente."
            }
        
        # Get Cloud Function URL from environment
        cloud_function_url = os.getenv(
            "GAP_ANALYSIS_FUNCTION_URL",
            "https://YOUR_REGION-YOUR_PROJECT.cloudfunctions.net/analyzeCandidateGaps"
        )
        
        logger.info(f"Calling gap analysis for user {user_id} and vacancy {vacancy_id}")
        
        # Call the Cloud Function
        response = requests.post(
            cloud_function_url,
            json={
                "userId": user_id,
                "vacancyId": vacancy_id
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('SERVICE_ACCOUNT_TOKEN', '')}"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Gap analysis completed. Compatibility: {result.get('currentCompatibility')}%")
            
            # Format the response for the chat
            return {
                "status": "success",
                "vacancy": result.get("vacancy", {}),
                "currentCompatibility": result.get("currentCompatibility", 0),
                "gaps": result.get("gaps", []),
                "matches": result.get("matches", []),
                "suggestions": result.get("suggestions", []),
                "improvementPotential": result.get("improvementPotential", 0),
                "actionPlan": result.get("actionPlan", {})
            }
        
        elif response.status_code == 404:
            error_data = response.json()
            if "Perfil do usuário" in error_data.get("error", ""):
                return {
                    "status": "error",
                    "message": "Seu perfil não foi encontrado. Por favor, complete seu cadastro primeiro."
                }
            elif "Vaga não encontrada" in error_data.get("error", ""):
                return {
                    "status": "error",
                    "message": f"A vaga {vacancy_id} não foi encontrada."
                }
        
        else:
            logger.error(f"Gap analysis failed with status {response.status_code}: {response.text}")
            return {
                "status": "error",
                "message": "Não foi possível analisar os gaps no momento. Tente novamente mais tarde."
            }
            
    except requests.exceptions.Timeout:
        logger.error("Gap analysis timed out")
        return {
            "status": "error",
            "message": "A análise está demorando mais que o esperado. Por favor, tente novamente."
        }
    except Exception as e:
        logger.error(f"Error in gap analysis: {str(e)}")
        return {
            "status": "error",
            "message": "Ocorreu um erro ao analisar os gaps. Por favor, tente novamente."
        }

# Create the tool instance
analyze_gap_tool = FunctionTool(func=analyze_gap)