"""
Ferramenta para buscar candidatos compatíveis com vagas
"""

import os
import logging
import requests
from typing import Optional, Dict, Any
from google.adk.tools import FunctionTool, ToolContext

logger = logging.getLogger(__name__)

def retrieve_matches(
    vacancy_id: int,
    min_score: Optional[int] = 70,
    limit: Optional[int] = 20,
    filters: Optional[Dict[str, Any]] = None,
    tool_context: ToolContext = None
) -> dict:
    """
    Busca candidatos compatíveis com uma vaga específica.
    
    Args:
        vacancy_id: ID da vaga para buscar matches
        min_score: Score mínimo de compatibilidade (0-100)
        limit: Número máximo de candidatos a retornar
        filters: Filtros adicionais (localização, experiência, etc)
        tool_context: Contexto da ferramenta
        
    Returns:
        dict: Lista de candidatos compatíveis com scores
    """
    try:
        # Validar empresa
        company_id = tool_context.state.get("company_id")
        if not company_id:
            return {
                "status": "error",
                "message": "Empresa não identificada. Execute retrieve_company_info primeiro."
            }
            
        # URL da API
        base_url = os.getenv("MATCH_API_URL", "http://localhost:3030/api/matches")
        user_id = tool_context._invocation_context.session.user_id
        
        headers = {
            "accept": "application/json",
            "x-user-id": user_id,
            "x-company-id": company_id
        }
        
        # Parâmetros da busca
        params = {
            "vacancy_id": vacancy_id,
            "min_score": min_score,
            "limit": limit
        }
        
        # Adicionar filtros se fornecidos
        if filters:
            if filters.get("location"):
                params["location"] = filters["location"]
            if filters.get("min_experience"):
                params["min_experience"] = filters["min_experience"]
            if filters.get("skills"):
                params["skills"] = ",".join(filters["skills"]) if isinstance(filters["skills"], list) else filters["skills"]
        
        logger.info(f"Buscando matches para vaga {vacancy_id} com score mínimo {min_score}%")
        
        # Fazer requisição
        response = requests.get(
            f"{base_url}/vacancy/{vacancy_id}",
            headers=headers,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get("matches", [])
            
            logger.info(f"Encontrados {len(matches)} candidatos compatíveis")
            
            # Processar e enriquecer dados dos matches
            processed_matches = []
            for match in matches:
                processed_match = {
                    "candidate_id": match.get("userId"),
                    "name": match.get("fullName", "Nome não disponível"),
                    "score": match.get("matchPercentage", 0),
                    "location": match.get("location", "Não informado"),
                    "experience_years": match.get("experienceYears", 0),
                    "main_skills": match.get("mainSkills", []),
                    "education": match.get("education", "Não informado"),
                    "salary_expectation": match.get("salaryExpectation"),
                    "available": match.get("available", True),
                    "ats_score": match.get("atsScore", 0),
                    "match_reasons": match.get("matchReasons", [])
                }
                
                # Adicionar alertas se houver
                if processed_match["ats_score"] < 70:
                    processed_match["ats_warning"] = "Perfil pode precisar de otimização para ATS"
                    
                processed_matches.append(processed_match)
            
            # Ordenar por score
            processed_matches.sort(key=lambda x: x["score"], reverse=True)
            
            # Estatísticas
            stats = {
                "total_found": len(processed_matches),
                "avg_score": sum(m["score"] for m in processed_matches) / len(processed_matches) if processed_matches else 0,
                "with_high_ats": len([m for m in processed_matches if m.get("ats_score", 0) >= 80]),
                "ready_to_hire": len([m for m in processed_matches if m["available"]])
            }
            
            return {
                "status": "success",
                "vacancy_id": vacancy_id,
                "matches": processed_matches,
                "stats": stats,
                "message": f"Encontrados {len(processed_matches)} candidatos com compatibilidade acima de {min_score}%"
            }
            
        elif response.status_code == 404:
            return {
                "status": "error",
                "message": "Vaga não encontrada ou não pertence à sua empresa"
            }
            
        elif response.status_code == 403:
            return {
                "status": "error",
                "message": "Sem permissão para acessar esta vaga"
            }
            
        else:
            error_msg = response.json().get("message", "Erro desconhecido")
            return {
                "status": "error",
                "message": f"Erro ao buscar candidatos: {error_msg}"
            }
            
    except requests.exceptions.Timeout:
        logger.error("Timeout ao buscar matches")
        return {
            "status": "error",
            "message": "Tempo esgotado ao buscar candidatos. Tente novamente."
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar matches: {str(e)}")
        return {
            "status": "error",
            "message": f"Erro ao processar busca: {str(e)}"
        }


def search_candidates_by_skills(
    skills: list,
    location: Optional[str] = None,
    min_experience: Optional[int] = None,
    tool_context: ToolContext = None
) -> dict:
    """
    Busca candidatos por competências específicas (sem vaga específica).
    
    Args:
        skills: Lista de competências desejadas
        location: Localização preferida
        min_experience: Anos mínimos de experiência
        tool_context: Contexto da ferramenta
        
    Returns:
        dict: Lista de candidatos que possuem as competências
    """
    try:
        company_id = tool_context.state.get("company_id")
        if not company_id:
            return {
                "status": "error",
                "message": "Empresa não identificada. Execute retrieve_company_info primeiro."
            }
            
        base_url = os.getenv("MATCH_API_URL", "http://localhost:3030/api/matches")
        user_id = tool_context._invocation_context.session.user_id
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-user-id": user_id,
            "x-company-id": company_id
        }
        
        # Payload da busca
        payload = {
            "skills": skills,
            "location": location,
            "min_experience": min_experience,
            "company_id": company_id
        }
        
        logger.info(f"Buscando candidatos com skills: {', '.join(skills)}")
        
        response = requests.post(
            f"{base_url}/search-candidates",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            
            return {
                "status": "success",
                "candidates": candidates,
                "total": len(candidates),
                "message": f"Encontrados {len(candidates)} candidatos com as competências solicitadas"
            }
        else:
            return {
                "status": "error",
                "message": "Erro ao buscar candidatos por competências"
            }
            
    except Exception as e:
        logger.error(f"Erro na busca por skills: {str(e)}")
        return {
            "status": "error",
            "message": f"Erro ao processar busca: {str(e)}"
        }


# Registrar a ferramenta principal
retrieve_matches_tool = FunctionTool(
    func=retrieve_matches,
    name="retrieve_matches",
    description="""Busca candidatos compatíveis com uma vaga específica.
    Retorna lista ordenada por score de compatibilidade, incluindo:
    - Informações do candidato
    - Score de match (0-100%)
    - Score ATS
    - Razões da compatibilidade
    - Disponibilidade
    
    Parâmetros:
    - vacancy_id: ID da vaga (obrigatório)
    - min_score: Score mínimo de compatibilidade (padrão: 70)
    - limit: Número máximo de resultados (padrão: 20)
    - filters: Filtros adicionais (location, skills, experience)
    """
)