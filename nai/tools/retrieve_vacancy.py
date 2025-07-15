# tools/retrieve_match.py

from google.adk.tools import FunctionTool, ToolContext
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SEARCH_VACANCY_URL = os.getenv("SEARCH_VACANCY_URL")

def retrieve_vacancy(term: str, tool_context: ToolContext) -> dict:
    """
    Busca vagas semânticas com base no termo informado pelo usuário.
    """
    if not term:
        return {"status": "error", "message": "Nenhum termo de busca informado."}
    url = SEARCH_VACANCY_URL
    headers = {"accept": "application/json"}
    params = {"text": term}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            return {"status": "success", "vagas": response.json().get("message", [])}
        else:
            logger.error(f"Erro {response.status_code}: {response.text}")
            return {"status": "error", "message": response.text}
    except Exception as e:
        logger.exception("Falha ao buscar vagas semânticas.")
        return {"status": "error", "message": str(e)}

retrieve_vacancy_tool = FunctionTool(func=retrieve_vacancy)
