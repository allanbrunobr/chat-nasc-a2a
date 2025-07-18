"""
Ferramenta para recuperar informações da empresa
"""

import os
import logging
import requests
from google.adk.tools import FunctionTool, ToolContext

logger = logging.getLogger(__name__)

# Definir nível de log para DEBUG temporariamente
logger.setLevel(logging.DEBUG)

def retrieve_company_info(tool_context: ToolContext) -> dict:
    logger.info("==================== INICIANDO retrieve_company_info ====================")
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
        # Debug do contexto
        logger.debug(f"tool_context type: {type(tool_context)}")
        logger.debug(f"Has _invocation_context: {hasattr(tool_context, '_invocation_context')}")
        
        if hasattr(tool_context, '_invocation_context'):
            logger.debug(f"_invocation_context type: {type(tool_context._invocation_context)}")
            logger.debug(f"Has session: {hasattr(tool_context._invocation_context, 'session')}")
            
            if hasattr(tool_context._invocation_context, 'session'):
                session = tool_context._invocation_context.session
                logger.debug(f"session type: {type(session)}")
                logger.debug(f"session attributes: {dir(session)}")
                logger.debug(f"Has user_id: {hasattr(session, 'user_id')}")
        
        # Obter user_id da sessão
        user_id = tool_context._invocation_context.session.user_id
        logger.info(f"Recuperando informações da empresa para user_id: {user_id}")
        
        # Log detalhado do contexto
        logger.debug(f"Session metadata: {getattr(tool_context._invocation_context.session, 'metadata', {})}")  
        logger.debug(f"Tool context state: {tool_context.state}")
        
        # Nota: Sempre usaremos user_id para buscar a empresa
        # A cloud function fará o lookup correto baseado no user_id
        
        # URL da Cloud Function para dados completos da empresa
        cloud_function_url = os.getenv("EMPRESA_PROFILE_GET_INFO")
        logger.info(f"Cloud function URL: {cloud_function_url}")
        
        if cloud_function_url:
            # SEMPRE usar user_id com a Cloud Function
            # A cloud function fará o lookup do company_id correto
            logger.info(f"Usando Cloud Function com user_id: {user_id}")
            params = {"user_id": user_id}
            url = cloud_function_url
        else:
            # Fallback para API tradicional
            logger.info("Cloud Function não configurada, usando API tradicional")
            url = os.getenv("COMPANY_API_URL", "http://localhost:3030/api/companies")
            params = None
        
        # Headers incluindo o user_id para autenticação
        headers = {
            "accept": "application/json",
            "x-user-id": user_id
        }
        
        # Fazer requisição
        if params:
            # Cloud Function - passar parameters como query param
            logger.info(f"Fazendo requisição GET para: {url}")
            logger.info(f"Parâmetros: {params}")
            logger.info(f"Headers: {headers}")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            logger.info(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            if response.status_code != 200:
                logger.error(f"Response body: {response.text}")
        else:
            # API tradicional - endpoint my-company
            response = requests.get(f"{url}/my-company", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Resposta recebida com sucesso. Keys: {list(data.keys())[:10]}")
            
            # Verificar se é resposta da Cloud Function ou API tradicional
            if "company_name" in data:
                # Resposta da Cloud Function - já vem formatada
                logger.info(f"Empresa encontrada (Cloud Function): {data.get('company_name', 'N/A')}")
                
                # Extrair dados principais
                company_data = {
                    "id": data.get("company_id"),
                    "companyName": data.get("company_name"),
                    "businessName": data.get("business_name"),
                    "documentNumber": data.get("document_number"),
                    "phoneNumber": data.get("contact", {}).get("phone"),
                    "email": data.get("contact", {}).get("email"),
                    "city": data.get("location", {}).get("city"),
                    "state": data.get("location", {}).get("state"),
                    "address": data.get("location", {}).get("address"),
                    "companySize": data.get("company_info", {}).get("size"),
                    "companyType": data.get("company_info", {}).get("type"),
                    "nature": data.get("company_info", {}).get("nature"),
                    "companyDescription": data.get("company_info", {}).get("description"),
                    "active": data.get("company_info", {}).get("active", True)
                }
                
                # Incluir dados enriquecidos se disponíveis
                if "ai_analysis" in data:
                    company_data["ai_analysis"] = data["ai_analysis"]
                if "summary" in data:
                    company_data["metrics"] = data["summary"]
                if "job_vacancies" in data:
                    company_data["recent_vacancies"] = data["job_vacancies"][:5]
                    
            else:
                # Resposta da API tradicional
                company_data = data
                logger.info(f"Empresa encontrada (API tradicional): {company_data.get('companyName', 'N/A')}")
            
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
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erro de conexão: {str(e)}")
        return {
            "status": "error",
            "message": "Erro ao conectar com o serviço de dados da empresa",
            "error_code": "CONNECTION_ERROR"
        }
        
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        logger.error(f"Tipo de erro: {type(e).__name__}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return {
            "status": "error",
            "message": f"Erro ao processar sua solicitação: {str(e)}",
            "error_code": "UNKNOWN_ERROR"
        }

# Registrar a ferramenta
retrieve_company_info_tool = FunctionTool(retrieve_company_info)