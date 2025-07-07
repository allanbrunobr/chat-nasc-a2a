from google.adk.tools import FunctionTool, ToolContext
import requests
import os
import logging
import json
from typing import Optional
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

load_dotenv()

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

def is_perfil_criado(perfil_profissional):
    return any([
        bool(perfil_profissional.get("visao_atual")),
        bool(perfil_profissional.get("visao_futuro")),
        perfil_profissional.get("formacoes"),
        perfil_profissional.get("experiencias"),
        perfil_profissional.get("capacidades"),
        perfil_profissional.get("conhecimentos"),
    ])

def get_identity_token(audience: str) -> str:
    """Gera um Google Identity Token para autenticação em Cloud Functions"""
    return id_token.fetch_id_token(Request(), audience)

def retrieve_user_info(tool_context: ToolContext) -> dict:
    """
    Recupera o perfil público do usuário via API SETASC usando o endpoint da variável de ambiente.
    O user_id é recuperado do contexto da sessão ADK ou do .env para testes offline.
    Returns:
        dict: Dados completos do perfil ou mensagem de erro.
    """
    with tracer.start_as_current_span("retrieve_user_info") as span:
        span.set_attribute("tool.name", "retrieve_user_info")
        
        logger.info("=== INÍCIO retrieve_user_info ===")
        
        # Obter user_id com span dedicado
        with tracer.start_as_current_span("get_user_id") as user_span:
            user_id = None
            if tool_context and hasattr(tool_context, "_invocation_context"):
                user_id = getattr(tool_context._invocation_context.session, "user_id", None)
                user_span.set_attribute("user_id.source", "context")
                logger.debug(f"user_id obtido do contexto: {user_id}")
            if not user_id:
                user_id = os.getenv("USER_ID")  # fallback para o valor fixo do .env
                user_span.set_attribute("user_id.source", "env")
                logger.debug(f"user_id obtido do .env: {user_id}")
                if not user_id:
                    logger.error("user_id não encontrado no contexto da sessão nem no .env")
                    span.set_status(Status(StatusCode.ERROR, "user_id not found"))
                    span.add_event("user_id_missing")
                    return {"status": "error", "message": "user_id não encontrado no contexto da sessão nem no .env"}
            
            span.set_attribute("user.id", user_id)

        # Configurar URL
        with tracer.start_as_current_span("setup_request") as setup_span:
            base_url = os.getenv("USER_PROFILE_URL")
            if not base_url:
                logger.error("A variável USER_PROFILE_URL não está definida no .env")
                span.set_status(Status(StatusCode.ERROR, "USER_PROFILE_URL not configured"))
                return {"status": "error", "message": "URL da função de recuperação de usuário não configurada."}

            # Remover barra final se houver
            if base_url.endswith("/"):
                base_url = base_url[:-1]

            url = f"{base_url}?user_id={user_id}"
            setup_span.set_attribute("http.url", url)
            logger.info(f"URL chamada: {url}")
            headers = {"accept": "application/json"}

        try:
            # Fazer requisição HTTP
            with tracer.start_as_current_span("http_request") as http_span:
                http_span.set_attribute("http.method", "GET")
                http_span.set_attribute("http.url", url)
                
                logger.debug("Fazendo requisição GET...")
                response = requests.get(url, headers=headers, timeout=10)
                
                http_span.set_attribute("http.status_code", response.status_code)
                http_span.set_attribute("http.response_size", len(response.content))
                
                logger.debug(f"Status code: {response.status_code}")
                
                if response.status_code == 200:
                    # Processar resposta bem-sucedida
                    with tracer.start_as_current_span("process_response") as process_span:
                        data = response.json()
                        logger.debug(f"Dados recebidos: {json.dumps(data, indent=2)[:500]}...")
                        
                        # Adicionar eventos sobre os dados recebidos
                        if data.get("name"):
                            process_span.add_event("profile_found", {
                                "user.name": data.get("name"),
                                "profile.has_skills": bool(data.get("skills")),
                                "profile.has_experiences": bool(data.get("experiences"))
                            })
                        
                        if tool_context is not None:
                            # Atualizar state
                            with tracer.start_as_current_span("update_state") as state_span:
                                state = tool_context.state
                                logger.debug("Processando dados para o state...")
                                
                                # Extrair dados do usuário
                                user_data = data.get("raw_data", {}).get("user", {}) if data.get("raw_data") else {}
                                
                                # Processar skills
                                with tracer.start_as_current_span("process_skills") as skills_span:
                                    skills_list = data.get("skills", [])
                                    hard_skills = []
                                    soft_skills = []
                                    
                                    # Por enquanto, vamos colocar todas como hard skills
                                    for skill in skills_list:
                                        if isinstance(skill, dict):
                                            hard_skills.append(skill.get("skill", ""))
                                        elif isinstance(skill, str):
                                            hard_skills.append(skill)
                                    
                                    skills_span.set_attribute("skills.hard_count", len(hard_skills))
                                    skills_span.set_attribute("skills.soft_count", len(soft_skills))
                                
                                # Mapear perfil para o formato esperado pelo update_state
                                perfil_profissional = {
                                    # Dados pessoais
                                    "firstName": user_data.get("firstName", "") or data.get("name", "").split()[0] if data.get("name") else "",
                                    "lastName": user_data.get("lastName", "") or " ".join(data.get("name", "").split()[1:]) if data.get("name") and len(data.get("name", "").split()) > 1 else "",
                                    "email": data.get("email", "") or user_data.get("email", ""),
                                    "phone": data.get("phone", "") or user_data.get("phone", ""),
                                    "city": data.get("city", "") or user_data.get("city", ""),
                                    "state": data.get("state", "") or user_data.get("state", ""),
                                    "country": user_data.get("country", "Brasil"),
                                    "birthDate": user_data.get("birthDate", ""),
                                    "gender": user_data.get("gender", ""),
                                    "zipcode": user_data.get("zipcode", ""),
                                    "address": user_data.get("address", ""),
                                    "latitude": user_data.get("latitude", ""),
                                    "longitude": user_data.get("longitude", ""),
                                    "nacionality": user_data.get("nacionality", ""),
                                    "social_name": user_data.get("socialName", ""),
                                    "attended_government_course_mt": user_data.get("attendedGovernmentCourseMT", None),
                                    "benefit_type": user_data.get("benefitType", ""),
                                    "complemente": user_data.get("complemente", ""),
                                    "course_areas": user_data.get("courseAreas", ""),
                                    "courses_taken": user_data.get("coursesTaken", ""),
                                    "disability_type": user_data.get("disabilityType", ""),
                                    "has_disability": user_data.get("hasDisability", None),
                                    "interested_in_professional_training": user_data.get("interestedInProfessionalTraining", None),
                                    "neighborhood": user_data.get("neighborhood", ""),
                                    "participates_ser_familia_mulher": user_data.get("participatesSerFamiliaMulher", None),
                                    "race_color": user_data.get("raceColor", ""),
                                    "receives_government_benefit": user_data.get("receivesGovernmentBenefit", None),
                                    "residence_number": user_data.get("residenceNumber", ""),
                                    "courses_interested_in": user_data.get("coursesInterestedIn", ""),
                                    
                                    # Skills separadas - usando camelCase para compatibilidade
                                    "hardSkills": hard_skills,
                                    "softSkills": soft_skills,
                                    
                                    # Experiências e educação
                                    "experiences": data.get("experiences", []),
                                    "education": data.get("education", []),
                                    "languages": []  # TODO: Extrair idiomas se disponível
                                }
                                
                                state["perfil_profissional"] = perfil_profissional
                                state["perfil_criado"] = True if data.get("name") else False
                                
                                state_span.set_attribute("state.profile_created", state["perfil_criado"])
                                state_span.add_event("state_updated")
                                
                                logger.debug(f"State atualizado com perfil_profissional: {json.dumps(perfil_profissional, indent=2)[:300]}...")
                        
                        logger.info("=== FIM retrieve_user_info (sucesso) ===")
                        span.set_status(Status(StatusCode.OK))
                        return {"status": "success", "perfil": data}
                
                elif response.status_code == 404:
                    span.add_event("profile_not_found", {"user.id": user_id})
                    span.set_status(Status(StatusCode.OK))  # 404 não é erro da aplicação
                    return {"status": "not_found", "message": "Perfil não encontrado para este usuário."}
                
                else:
                    logger.error(f"Erro {response.status_code}: {response.text}")
                    span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                    return {"status": "error", "message": f"Erro {response.status_code}: {response.text}"}
                    
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            logger.exception("Falha ao consultar a API de perfil do usuário.")
            return {"status": "error", "message": f"Exceção: {str(e)}"}

retrieve_user_info_tool = FunctionTool(
    func=retrieve_user_info,
)