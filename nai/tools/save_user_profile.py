from google.adk.tools import FunctionTool, ToolContext
import requests
import os
import json
import logging
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

def save_user_profile(tool_context: ToolContext) -> dict:
    """
    Salva (cria ou atualiza) o perfil profissional do usuário via POST para a Cloud Function de persistência completa.
    O objeto do perfil deve estar completo no estado.
    Returns:
        dict: Status da operação e mensagem.
    """
    logger.info("=== INÍCIO save_user_profile ===")
    
    perfil = tool_context.state.get("perfil_profissional")
    user_id = getattr(tool_context._invocation_context.session, "user_id", None)
    
    logger.info(f"user_id: {user_id}")
    logger.info(f"Perfil presente no estado: {'Sim' if perfil else 'Não'}")
    
    if perfil:
        logger.debug(f"Habilidades técnicas a salvar: {perfil.get('hardSkills', [])}")
        logger.debug(f"Habilidades comportamentais a salvar: {perfil.get('softSkills', [])}")

    if not perfil:
        logger.error("Perfil do usuário não encontrado no estado para salvar.")
        return {"status": "error", "message": "Perfil do usuário não encontrado no estado para salvar."}

    persist_url = os.getenv("PERSIST_USER_PROFILE_COMPLETE_URL")
    if not persist_url:
        logger.error("A variável PERSIST_USER_PROFILE_COMPLETE_URL não está definida no .env")
        return {"status": "error", "message": "URL da função de persistência de perfil não configurada."}

    url = persist_url
    headers = {"accept": "application/json", "Content-Type": "application/json"}

    payload = {
        "user_id": user_id,
        "perfil_completo": perfil
    }

    try:
        logger.info(f"Enviando POST para: {url}")
        logger.debug(f"Payload enviado: {json.dumps(payload, indent=2, ensure_ascii=False)[:500]}...")
        
        response = requests.post(url, json=payload, headers=headers, timeout=600)
        logger.info(f"Status code recebido: {response.status_code}")
        
        if response.status_code in (200, 201):
            logger.info("✅ Perfil salvo com sucesso!")
            logger.info("=== FIM save_user_profile (sucesso) ===")
            return {"status": "success", "message": "Perfil salvo com sucesso!"}
        else:
            logger.error(f"❌ Erro {response.status_code}: {response.text}")
            logger.info("=== FIM save_user_profile (erro) ===")
            return {"status": "error", "message": f"Erro {response.status_code}: {response.text}"}
    except Exception as e:
        logger.exception("❌ Falha ao salvar perfil do usuário.")
        logger.info("=== FIM save_user_profile (exceção) ===")
        return {"status": "error", "message": f"Exceção: {str(e)}"}

save_user_profile_tool = FunctionTool(
    func=save_user_profile,
)
