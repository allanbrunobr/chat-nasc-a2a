"""
Ferramenta para recuperar informações da empresa
"""

import os
import logging
import requests
from google.adk.tools import FunctionTool, ToolContext

logger = logging.getLogger(__name__)

def retrieve_company_info(tool_context: ToolContext) -> dict:
    """
    Recupera informações da empresa do usuário atual.
    
    Esta ferramenta deve ser sempre executada no início da conversa para:
    - Validar que o usuário tem role=EMPRESA
    - Obter dados da empresa (nome, CNPJ, etc)
    - Verificar permissões e limites
    
    Returns:
        dict: Informações da empresa ou erro
    """
    try:
        # Obter user_id da sessão
        user_id = tool_context._invocation_context.session.user_id
        logger.info(f"Recuperando informações da empresa para user_id: {user_id}")
        
        # URL da API
        url = os.getenv("COMPANY_API_URL", "http://localhost:3030/api/companies")
        
        # Headers incluindo o user_id para autenticação
        headers = {
            "accept": "application/json",
            "x-user-id": user_id
        }
        
        # Fazer requisição
        response = requests.get(f"{url}/my-company", headers=headers, timeout=30)
        
        if response.status_code == 200:
            company_data = response.json()
            logger.info(f"Empresa encontrada: {company_data.get('companyName', 'N/A')}")
            
            # Salvar no estado para uso posterior
            tool_context.state["company_info"] = company_data
            tool_context.state["company_id"] = company_data.get("id")
            tool_context.state["company_name"] = company_data.get("companyName")
            
            return {
                "status": "success",
                "company": company_data,
                "message": f"Empresa {company_data.get('companyName')} carregada com sucesso"
            }
            
        elif response.status_code == 403:
            logger.warning(f"Usuário {user_id} não tem permissão de empresa")
            return {
                "status": "error",
                "message": "Acesso negado. Este chat é exclusivo para empresas cadastradas.",
                "error_code": "NOT_COMPANY"
            }
            
        elif response.status_code == 404:
            logger.warning(f"Empresa não encontrada para user_id: {user_id}")
            return {
                "status": "error",
                "message": "Empresa não encontrada. Verifique seu cadastro.",
                "error_code": "COMPANY_NOT_FOUND"
            }
            
        else:
            logger.error(f"Erro ao recuperar empresa: {response.status_code}")
            return {
                "status": "error",
                "message": f"Erro ao recuperar informações da empresa: {response.status_code}",
                "error_code": "API_ERROR"
            }
            
    except requests.exceptions.Timeout:
        logger.error("Timeout ao recuperar informações da empresa")
        return {
            "status": "error",
            "message": "Tempo esgotado ao buscar informações. Tente novamente.",
            "error_code": "TIMEOUT"
        }
        
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return {
            "status": "error",
            "message": "Erro ao processar sua solicitação",
            "error_code": "UNKNOWN_ERROR"
        }

# Registrar a ferramenta
retrieve_company_info_tool = FunctionTool(
    func=retrieve_company_info,
    name="retrieve_company_info",
    description="Recupera informações da empresa do usuário. Deve ser sempre executada no início da conversa."
)