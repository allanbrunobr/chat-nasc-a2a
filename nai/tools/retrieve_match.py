# tools/retrieve_match.py

from google.adk.tools import FunctionTool, ToolContext
import os
import requests
import logging
from dotenv import load_dotenv
from pathlib import Path

# Carrega o .env da raiz do projeto
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(env_path)
logger = logging.getLogger(__name__)

# Usando a nova função melhorada ao invés da antiga
RETRIEVE_MATCH_IMPROVED_URL = os.getenv("RETRIEVE_MATCH_IMPROVED_URL")
RETRIEVE_MATCH_URL_OLD = os.getenv("RETRIEVE_MATCH_URL")
RETRIEVE_MATCH_URL = RETRIEVE_MATCH_IMPROVED_URL or RETRIEVE_MATCH_URL_OLD

logger.info(f"Carregando .env de: {env_path}")
logger.info(f"RETRIEVE_MATCH_IMPROVED_URL: {RETRIEVE_MATCH_IMPROVED_URL}")
logger.info(f"RETRIEVE_MATCH_URL (antiga): {RETRIEVE_MATCH_URL_OLD}")
logger.info(f"RETRIEVE_MATCH_URL final: {RETRIEVE_MATCH_URL}")

def retrieve_match(_: str, tool_context: ToolContext) -> dict:
    """
    Busca os melhores matches de vagas para o usuário usando busca semântica inteligente.
    Usa a nova implementação que extrai termos do perfil ao invés de embeddings.
    """
    user_id = None
    if tool_context and hasattr(tool_context, "_invocation_context"):
        user_id = getattr(tool_context._invocation_context.session, "user_id", None)

    if not user_id:
        return {"status": "error", "message": "user_id não encontrado no contexto da sessão."}

    # Detecta qual API usar baseado na URL
    logger.info(f"Chamando retrieve_match para user {user_id} usando URL: {RETRIEVE_MATCH_URL}")
    try:
        if "setasc-search-improved" in RETRIEVE_MATCH_URL:
            # Nova API usa POST com body
            resp = requests.post(
                RETRIEVE_MATCH_URL, 
                json={"user_id": user_id, "limit": 50},
                timeout=30  # Aumentado pois faz múltiplas buscas
            )
        else:
            # API antiga usa GET com params
            resp = requests.get(
                RETRIEVE_MATCH_URL, 
                params={"userId": user_id},
                timeout=10
            )
        if resp.status_code == 200:
            data = resp.json()
            
            # Se for a nova API, adapta o formato
            if "setasc-search-improved" in RETRIEVE_MATCH_URL:
                matches = []
                for match in data.get("matches", []):
                    matches.append({
                        "vacancy_id": match.get("vacancy_id"),
                        "vacancy_title": match.get("title"),
                        "company_name": f"Company {match.get('company_id')}",  # Temporário até termos o nome
                        "matchPercentage": int(match.get("final_score", 0) * 100),
                        "matched_terms": match.get("matched_terms", []),
                        "match_diversity": match.get("match_diversity", 0)
                    })
                
                logger.info(f"Busca melhorada retornou {len(matches)} matches para user {user_id}")
                return {
                    "status": "success",
                    "matches": matches,
                    "user_profile": data.get("user_profile", {}),
                    "search_terms_used": data.get("search_terms_used", [])
                }
            else:
                # API antiga já retorna no formato correto
                return {
                    "status": "success",
                    "matches": data.get("matches", [])
                }
        else:
            logger.error(f"Erro {resp.status_code}: {resp.text}")
            return {"status": "error", "message": f"Erro {resp.status_code}: {resp.text}"}
    except Exception as e:
        logger.exception("Falha ao buscar matches.")
        return {"status": "error", "message": f"Erro na requisição: {str(e)}"}

retrieve_match_tool = FunctionTool(func=retrieve_match)
