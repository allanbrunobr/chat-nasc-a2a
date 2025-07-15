"""
Ferramenta para gerenciar vagas de emprego
"""

import os
import json
import logging
import requests
from typing import Optional, Dict, Any
from google.adk.tools import FunctionTool, ToolContext

logger = logging.getLogger(__name__)

def manage_vacancy(
    action: str,
    vacancy_data: Optional[Dict[str, Any]] = None,
    vacancy_id: Optional[int] = None,
    tool_context: ToolContext = None
) -> dict:
    """
    Gerencia vagas de emprego (criar, editar, ativar/desativar, listar).
    
    Args:
        action: Ação a executar ('create', 'update', 'toggle', 'list', 'get')
        vacancy_data: Dados da vaga (para create/update)
        vacancy_id: ID da vaga (para update/toggle/get)
        tool_context: Contexto da ferramenta
        
    Returns:
        dict: Resultado da operação
    """
    try:
        # Validar empresa
        company_id = tool_context.state.get("company_id")
        if not company_id:
            return {
                "status": "error",
                "message": "Empresa não identificada. Execute retrieve_company_info primeiro."
            }
            
        # URL base
        base_url = os.getenv("VACANCY_API_URL", "http://localhost:3030/api/vacancies")
        user_id = tool_context._invocation_context.session.user_id
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-user-id": user_id,
            "x-company-id": company_id
        }
        
        # Executar ação apropriada
        if action == "create":
            return _create_vacancy(base_url, headers, vacancy_data, company_id)
            
        elif action == "update":
            if not vacancy_id:
                return {"status": "error", "message": "ID da vaga é obrigatório para atualização"}
            return _update_vacancy(base_url, headers, vacancy_id, vacancy_data)
            
        elif action == "toggle":
            if not vacancy_id:
                return {"status": "error", "message": "ID da vaga é obrigatório"}
            return _toggle_vacancy(base_url, headers, vacancy_id)
            
        elif action == "list":
            return _list_vacancies(base_url, headers, company_id)
            
        elif action == "get":
            if not vacancy_id:
                return {"status": "error", "message": "ID da vaga é obrigatório"}
            return _get_vacancy(base_url, headers, vacancy_id)
            
        else:
            return {
                "status": "error",
                "message": f"Ação '{action}' não reconhecida. Use: create, update, toggle, list, get"
            }
            
    except Exception as e:
        logger.error(f"Erro ao gerenciar vaga: {str(e)}")
        return {
            "status": "error",
            "message": f"Erro ao processar operação: {str(e)}"
        }


def _create_vacancy(base_url: str, headers: dict, vacancy_data: dict, company_id: str) -> dict:
    """Cria uma nova vaga"""
    
    # Validar campos obrigatórios
    required_fields = ["title", "position", "description", "location"]
    missing_fields = [f for f in required_fields if not vacancy_data.get(f)]
    
    if missing_fields:
        return {
            "status": "error",
            "message": f"Campos obrigatórios faltando: {', '.join(missing_fields)}"
        }
    
    # Adicionar company_id aos dados
    vacancy_data["companyId"] = company_id
    
    # Definir valores padrão
    vacancy_data.setdefault("active", True)
    vacancy_data.setdefault("vacancies", 1)
    vacancy_data.setdefault("workFormat", "PRESENTIAL")
    vacancy_data.setdefault("contractType", "CLT")
    
    logger.info(f"Criando vaga: {vacancy_data.get('title')}")
    
    response = requests.post(
        f"{base_url}/create",
        headers=headers,
        json=vacancy_data,
        timeout=30
    )
    
    if response.status_code == 201:
        vacancy = response.json()
        logger.info(f"Vaga criada com ID: {vacancy.get('id')}")
        return {
            "status": "success",
            "vacancy": vacancy,
            "message": f"Vaga '{vacancy.get('title')}' criada com sucesso!"
        }
    else:
        error_msg = response.json().get("message", "Erro desconhecido")
        return {
            "status": "error",
            "message": f"Erro ao criar vaga: {error_msg}"
        }


def _update_vacancy(base_url: str, headers: dict, vacancy_id: int, vacancy_data: dict) -> dict:
    """Atualiza uma vaga existente"""
    
    logger.info(f"Atualizando vaga ID: {vacancy_id}")
    
    response = requests.put(
        f"{base_url}/{vacancy_id}",
        headers=headers,
        json=vacancy_data,
        timeout=30
    )
    
    if response.status_code == 200:
        vacancy = response.json()
        return {
            "status": "success",
            "vacancy": vacancy,
            "message": f"Vaga '{vacancy.get('title')}' atualizada com sucesso!"
        }
    else:
        error_msg = response.json().get("message", "Erro desconhecido")
        return {
            "status": "error",
            "message": f"Erro ao atualizar vaga: {error_msg}"
        }


def _toggle_vacancy(base_url: str, headers: dict, vacancy_id: int) -> dict:
    """Ativa ou desativa uma vaga"""
    
    # Primeiro buscar a vaga para saber o status atual
    get_response = requests.get(f"{base_url}/{vacancy_id}", headers=headers, timeout=30)
    
    if get_response.status_code != 200:
        return {
            "status": "error",
            "message": "Vaga não encontrada"
        }
    
    vacancy = get_response.json()
    new_status = not vacancy.get("active", True)
    
    # Atualizar apenas o status
    response = requests.put(
        f"{base_url}/{vacancy_id}",
        headers=headers,
        json={"active": new_status},
        timeout=30
    )
    
    if response.status_code == 200:
        action_text = "ativada" if new_status else "desativada"
        return {
            "status": "success",
            "message": f"Vaga '{vacancy.get('title')}' foi {action_text}!",
            "active": new_status
        }
    else:
        return {
            "status": "error",
            "message": "Erro ao alterar status da vaga"
        }


def _list_vacancies(base_url: str, headers: dict, company_id: str) -> dict:
    """Lista todas as vagas da empresa"""
    
    logger.info(f"Listando vagas da empresa: {company_id}")
    
    response = requests.get(
        f"{base_url}/company/{company_id}",
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        vacancies = response.json()
        
        # Formatar resposta
        active_vacancies = [v for v in vacancies if v.get("active", True)]
        inactive_vacancies = [v for v in vacancies if not v.get("active", True)]
        
        return {
            "status": "success",
            "total": len(vacancies),
            "active": len(active_vacancies),
            "inactive": len(inactive_vacancies),
            "vacancies": vacancies,
            "message": f"Encontradas {len(vacancies)} vagas no total"
        }
    else:
        return {
            "status": "error",
            "message": "Erro ao listar vagas"
        }


def _get_vacancy(base_url: str, headers: dict, vacancy_id: int) -> dict:
    """Obtém detalhes de uma vaga específica"""
    
    logger.info(f"Buscando vaga ID: {vacancy_id}")
    
    response = requests.get(
        f"{base_url}/{vacancy_id}",
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        vacancy = response.json()
        return {
            "status": "success",
            "vacancy": vacancy
        }
    elif response.status_code == 404:
        return {
            "status": "error",
            "message": "Vaga não encontrada"
        }
    else:
        return {
            "status": "error",
            "message": "Erro ao buscar vaga"
        }


# Registrar a ferramenta
manage_vacancy_tool = FunctionTool(
    func=manage_vacancy,
    name="manage_vacancy",
    description="""Gerencia vagas de emprego. 
    Ações disponíveis:
    - create: Criar nova vaga (requer vacancy_data)
    - update: Atualizar vaga existente (requer vacancy_id e vacancy_data)
    - toggle: Ativar/desativar vaga (requer vacancy_id)
    - list: Listar todas as vagas da empresa
    - get: Obter detalhes de uma vaga (requer vacancy_id)
    """
)