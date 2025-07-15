"""
Ferramenta para gerenciar candidatos que se aplicaram às vagas
"""

import os
import logging
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from google.adk.tools import FunctionTool, ToolContext

logger = logging.getLogger(__name__)

def retrieve_applicants(
    vacancy_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    action: str = "list",
    applicant_id: Optional[str] = None,
    new_status: Optional[str] = None,
    feedback: Optional[str] = None,
    tool_context: ToolContext = None
) -> dict:
    """
    Gerencia candidatos que se aplicaram às vagas da empresa.
    
    Args:
        vacancy_id: ID da vaga (opcional, para filtrar por vaga)
        status_filter: Filtrar por status (novo, em_analise, entrevista, aprovado, rejeitado)
        date_from: Data inicial (formato: YYYY-MM-DD)
        date_to: Data final (formato: YYYY-MM-DD)
        action: Ação a executar ('list', 'update_status', 'add_feedback', 'get_details')
        applicant_id: ID do candidato (para ações específicas)
        new_status: Novo status (para update_status)
        feedback: Feedback/observações (para add_feedback)
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
        base_url = os.getenv("APPLICANT_API_URL", "http://localhost:3030/api/applicants")
        user_id = tool_context._invocation_context.session.user_id
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-user-id": user_id,
            "x-company-id": company_id
        }
        
        # Executar ação apropriada
        if action == "list":
            return _list_applicants(base_url, headers, company_id, vacancy_id, status_filter, date_from, date_to)
            
        elif action == "update_status":
            if not applicant_id or not new_status:
                return {
                    "status": "error",
                    "message": "ID do candidato e novo status são obrigatórios"
                }
            return _update_applicant_status(base_url, headers, applicant_id, new_status)
            
        elif action == "add_feedback":
            if not applicant_id or not feedback:
                return {
                    "status": "error",
                    "message": "ID do candidato e feedback são obrigatórios"
                }
            return _add_feedback(base_url, headers, applicant_id, feedback)
            
        elif action == "get_details":
            if not applicant_id:
                return {
                    "status": "error",
                    "message": "ID do candidato é obrigatório"
                }
            return _get_applicant_details(base_url, headers, applicant_id)
            
        else:
            return {
                "status": "error",
                "message": f"Ação '{action}' não reconhecida. Use: list, update_status, add_feedback, get_details"
            }
            
    except Exception as e:
        logger.error(f"Erro ao gerenciar candidatos: {str(e)}")
        return {
            "status": "error",
            "message": f"Erro ao processar operação: {str(e)}"
        }


def _list_applicants(base_url: str, headers: dict, company_id: str, 
                    vacancy_id: Optional[int], status_filter: Optional[str],
                    date_from: Optional[str], date_to: Optional[str]) -> dict:
    """Lista candidatos aplicados com filtros"""
    
    params = {"company_id": company_id}
    
    if vacancy_id:
        params["vacancy_id"] = vacancy_id
    if status_filter:
        params["status"] = status_filter
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
        
    logger.info(f"Listando candidatos aplicados com filtros: {params}")
    
    response = requests.get(
        f"{base_url}/company/{company_id}",
        headers=headers,
        params=params,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        applicants = data.get("applicants", [])
        
        # Processar e organizar dados
        processed_applicants = []
        status_counts = {"novo": 0, "em_analise": 0, "entrevista": 0, "aprovado": 0, "rejeitado": 0}
        
        for app in applicants:
            processed = {
                "applicant_id": app.get("id"),
                "candidate_name": app.get("candidateName", "Nome não disponível"),
                "vacancy_title": app.get("vacancyTitle"),
                "vacancy_id": app.get("vacancyId"),
                "applied_date": app.get("appliedDate"),
                "status": app.get("status", "novo"),
                "match_score": app.get("matchScore", 0),
                "ats_score": app.get("atsScore", 0),
                "location": app.get("location"),
                "experience_years": app.get("experienceYears", 0),
                "last_feedback": app.get("lastFeedback"),
                "feedback_count": app.get("feedbackCount", 0)
            }
            
            # Contar por status
            status_counts[processed["status"]] += 1
            processed_applicants.append(processed)
        
        # Ordenar por data de aplicação (mais recentes primeiro)
        processed_applicants.sort(key=lambda x: x["applied_date"], reverse=True)
        
        return {
            "status": "success",
            "total": len(processed_applicants),
            "applicants": processed_applicants,
            "status_summary": status_counts,
            "message": f"Encontrados {len(processed_applicants)} candidatos aplicados"
        }
    else:
        return {
            "status": "error",
            "message": "Erro ao listar candidatos aplicados"
        }


def _update_applicant_status(base_url: str, headers: dict, applicant_id: str, new_status: str) -> dict:
    """Atualiza o status de um candidato"""
    
    # Validar status
    valid_statuses = ["novo", "em_analise", "entrevista", "aprovado", "rejeitado"]
    if new_status not in valid_statuses:
        return {
            "status": "error",
            "message": f"Status inválido. Use: {', '.join(valid_statuses)}"
        }
    
    logger.info(f"Atualizando status do candidato {applicant_id} para {new_status}")
    
    payload = {
        "status": new_status,
        "updated_at": datetime.now().isoformat()
    }
    
    response = requests.put(
        f"{base_url}/{applicant_id}/status",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        return {
            "status": "success",
            "message": f"Status do candidato atualizado para '{new_status}'",
            "applicant": result
        }
    elif response.status_code == 404:
        return {
            "status": "error",
            "message": "Candidato não encontrado"
        }
    else:
        return {
            "status": "error",
            "message": "Erro ao atualizar status do candidato"
        }


def _add_feedback(base_url: str, headers: dict, applicant_id: str, feedback: str) -> dict:
    """Adiciona feedback/observações sobre um candidato"""
    
    logger.info(f"Adicionando feedback para candidato {applicant_id}")
    
    payload = {
        "feedback": feedback,
        "created_at": datetime.now().isoformat()
    }
    
    response = requests.post(
        f"{base_url}/{applicant_id}/feedback",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code == 201:
        return {
            "status": "success",
            "message": "Feedback adicionado com sucesso"
        }
    elif response.status_code == 404:
        return {
            "status": "error",
            "message": "Candidato não encontrado"
        }
    else:
        return {
            "status": "error",
            "message": "Erro ao adicionar feedback"
        }


def _get_applicant_details(base_url: str, headers: dict, applicant_id: str) -> dict:
    """Obtém detalhes completos de um candidato aplicado"""
    
    logger.info(f"Buscando detalhes do candidato {applicant_id}")
    
    response = requests.get(
        f"{base_url}/{applicant_id}/details",
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Processar dados do candidato
        candidate_info = {
            "basic_info": {
                "name": data.get("fullName"),
                "email": data.get("email"),
                "phone": data.get("phone"),
                "location": data.get("location"),
                "birth_date": data.get("birthDate")
            },
            "professional": {
                "current_position": data.get("currentPosition"),
                "experience_years": data.get("totalExperience"),
                "salary_expectation": data.get("salaryExpectation"),
                "available": data.get("available", True)
            },
            "education": data.get("education", []),
            "experience": data.get("experience", []),
            "skills": {
                "hard_skills": data.get("hardSkills", []),
                "soft_skills": data.get("softSkills", []),
                "languages": data.get("languages", [])
            },
            "application": {
                "vacancy_title": data.get("vacancyTitle"),
                "applied_date": data.get("appliedDate"),
                "status": data.get("status"),
                "match_score": data.get("matchScore"),
                "ats_score": data.get("atsScore")
            },
            "feedback_history": data.get("feedbackHistory", [])
        }
        
        return {
            "status": "success",
            "candidate": candidate_info,
            "message": "Detalhes do candidato recuperados com sucesso"
        }
    elif response.status_code == 404:
        return {
            "status": "error",
            "message": "Candidato não encontrado"
        }
    else:
        return {
            "status": "error",
            "message": "Erro ao buscar detalhes do candidato"
        }


# Registrar a ferramenta
retrieve_applicants_tool = FunctionTool(
    func=retrieve_applicants,
    name="retrieve_applicants",
    description="""Gerencia candidatos que se aplicaram às vagas da empresa.
    
    Ações disponíveis:
    - list: Listar candidatos aplicados (com filtros opcionais)
    - update_status: Atualizar status do candidato
    - add_feedback: Adicionar feedback/observações
    - get_details: Obter perfil completo do candidato
    
    Status válidos: novo, em_analise, entrevista, aprovado, rejeitado
    
    Filtros para listagem:
    - vacancy_id: Filtrar por vaga específica
    - status_filter: Filtrar por status
    - date_from/date_to: Filtrar por período de aplicação
    """
)