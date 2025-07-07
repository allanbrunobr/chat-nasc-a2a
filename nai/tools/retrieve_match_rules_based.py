from google.adk.tools import FunctionTool, ToolContext
import os
import requests
import logging

logger = logging.getLogger(__name__)

def retrieve_match_rules_based(_: str, tool_context: ToolContext) -> dict:
    """
    Call the calculate-match-rules-based cloud function to get job matches.
    Uses rule-based algorithm for more accurate matching.
    """
    # Get user_id from context
    user_id = None
    if tool_context and hasattr(tool_context, "_invocation_context"):
        user_id = getattr(tool_context._invocation_context.session, "user_id", None)
        logger.debug(f"user_id obtido do contexto: {user_id}")
    
    if not user_id:
        user_id = os.getenv("USER_ID")  # fallback for testing
        logger.debug(f"user_id obtido do .env: {user_id}")
        if not user_id:
            logger.error("user_id não encontrado no contexto da sessão nem no .env")
            return {"status": "error", "message": "user_id não encontrado no contexto da sessão nem no .env"}
    
    # Get the cloud function URL from environment
    match_url = os.getenv('RETRIEVE_MATCH_RULES_URL', 
                         'https://southamerica-east1-setasc-central-emp-dev.cloudfunctions.net/calculate-match-rules-based')
    
    try:
        logger.info(f"Chamando cloud function: {match_url}")
        response = requests.get(
            match_url,
            params={'userId': user_id},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Cloud function retornou {len(data.get('matches', []))} matches")
            return {
                "status": "success",
                **data
            }
        else:
            logger.error(f"Erro {response.status_code}: {response.text}")
            return {"status": "error", "message": f"Erro {response.status_code}: {response.text}"}
            
    except requests.exceptions.Timeout:
        logger.error("Timeout ao chamar cloud function")
        return {
            "status": "error",
            "message": "A busca de vagas demorou muito tempo. Por favor, tente novamente."
        }
    except Exception as e:
        logger.exception("Erro ao chamar cloud function")
        return {
            "status": "error",
            "message": f"Erro ao buscar matches: {str(e)}"
        }

# Create the tool instance
retrieve_match_rules_based_tool = FunctionTool(func=retrieve_match_rules_based)