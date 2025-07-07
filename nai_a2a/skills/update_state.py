"""
Native A2A skill for updating user profile state using AI.

This skill uses Google Gemini AI to intelligently parse and update
user profile information based on natural language input.
"""

import os
import json
import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

from google import genai
from google.genai import types

from nai_a2a.exceptions import (
    ExternalAPIError,
    ValidationError
)

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize Gemini client
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not configured in environment")

client = genai.Client(api_key=api_key)


class UpdateStateSkill:
    """Skill for updating user profile using AI to parse natural language input."""
    
    def __init__(self):
        """Initialize the update state skill."""
        logger.info("UpdateStateSkill initialized with Gemini AI")
        self.client = client
    
    async def execute(self, user_id: str, content: str, 
                     current_profile: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Update user profile state using AI to parse content.
        
        Args:
            user_id: The user ID
            content: Natural language content to parse (resume, user input, etc.)
            current_profile: Current profile data to merge with (optional)
            **kwargs: Additional parameters
            
        Returns:
            Dict containing updated profile with metadata
            
        Raises:
            ValidationError: If content is empty
            ExternalAPIError: If AI processing fails
        """
        # Validate input
        if not content or not content.strip():
            raise ValidationError(
                "Content is required for profile update",
                {"field": "content", "value": content}
            )
        
        logger.info(f"Updating profile for user {user_id} with content length: {len(content)}")
        
        # Use provided profile or create empty one
        if current_profile is None:
            current_profile = self._create_empty_profile()
        
        try:
            # Prepare the prompt
            prompt = self._build_prompt(current_profile, content)
            
            # Call Gemini AI
            logger.debug("Calling Gemini AI for profile parsing")
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=8096
                )
            )
            
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response.text)
            if not json_match:
                logger.error("Gemini did not return valid JSON")
                raise ExternalAPIError(
                    service="Gemini AI",
                    status_code=0,
                    detail="AI did not return valid JSON format"
                )
            
            # Parse the JSON
            updated_profile = json.loads(json_match.group(0))
            
            # Add metadata
            result = {
                "profile": updated_profile,
                "_metadata": {
                    "updated_at": datetime.utcnow().isoformat(),
                    "source": "a2a_skill", 
                    "user_id": user_id,
                    "ai_model": "gemini-2.0-flash-001",
                    "content_length": len(content)
                }
            }
            
            logger.info(f"Successfully updated profile for user {user_id}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from AI response: {e}")
            raise ExternalAPIError(
                service="Gemini AI",
                status_code=0,
                detail=f"Invalid JSON in AI response: {str(e)}"
            )
            
        except Exception as e:
            logger.exception(f"Unexpected error during profile update: {e}")
            raise ExternalAPIError(
                service="Gemini AI",
                status_code=0,
                detail=f"Unexpected error: {str(e)}"
            )
    
    def _create_empty_profile(self) -> Dict[str, Any]:
        """Create an empty profile structure."""
        return {
            "firstName": None,
            "lastName": None,
            "email": None,
            "phone": None,
            "city": None,
            "state": None,
            "country": None,
            "birthDate": None,
            "gender": None,
            "zipcode": None,
            "address": None,
            "latitude": None,
            "longitude": None,
            "nacionality": None,
            "social_name": None,
            "attended_government_course_mt": None,
            "benefit_type": None,
            "complemente": None,
            "course_areas": None,
            "courses_taken": None,
            "disability_type": None,
            "has_disability": None,
            "interested_in_professional_training": None,
            "neighborhood": None,
            "participates_ser_familia_mulher": None,
            "race_color": None,
            "receives_government_benefit": None,
            "residence_number": None,
            "courses_interested_in": None,
            "hardSkills": [],
            "softSkills": [],
            "experiences": [],
            "education": [],
            "languages": []
        }
    
    def _build_prompt(self, current_profile: Dict[str, Any], content: str) -> str:
        """Build the prompt for Gemini AI."""
        schema_exemplo = {
            "firstName": "Allan Bruno",
            "lastName": "Oliveira Silva",
            "email": "abruno.oliveiras@gmail.com",
            "phone": "(81) 99887744",
            "city": "Recife",
            "state": "PE",
            "country": "Brasil",
            "birthDate": "1990-01-01",
            "gender": "Masculino",
            "zipcode": "50000-000",
            "address": "Rua Exemplo, 123",
            "latitude": -8.0476,
            "longitude": -34.877,
            "nacionality": "Brasileiro",
            "social_name": None,
            "attended_government_course_mt": None,
            "benefit_type": None,
            "complemente": None,
            "course_areas": None,
            "courses_taken": None,
            "disability_type": None,
            "has_disability": None,
            "interested_in_professional_training": None,
            "neighborhood": None,
            "participates_ser_familia_mulher": None,
            "race_color": None,
            "receives_government_benefit": None,
            "residence_number": None,
            "courses_interested_in": None,
            "hardSkills": ["Python", "SQL"],
            "softSkills": ["Comunicação", "Trabalho em equipe"],
            "experiences": [
                {
                    "company": "Empresa X",
                    "position": "Desenvolvedor",
                    "activity": "Desenvolvimento de sistemas",
                    "startDate": "2020-01-01",
                    "endDate": "2021-01-01",
                    "employmentRelationship": "EMPLOYEE",
                    "workFormat": "REMOTE",
                    "workLocation": "Recife",
                }
            ],
            "education": [
                {
                    "institution": "Universidade de Pernambuco",
                    "course": "Engenharia da Computação",
                    "fieldOfStudy": "",
                    "startDate": "2000-01-01",
                    "endDate": "2004-11-07",
                    "status": "Concluído",
                    "courseType": "Graduação"
                }
            ],
            "languages": ["Português", "Inglês"]
        }
        
        prompt = (
            "Você é um assistente de RH e deve completar/atualizar o perfil profissional do usuário. "
            "Aqui está o JSON atual do perfil do usuário, seguido de novas informações dele (texto/currículo, resposta, etc). "
            "Siga estritamente o schema abaixo na sua resposta final. Preencha apenas os campos que conseguir inferir a partir das novas informações. "
            "Infira a visão atual com base nas experiências que ele passou, Ex: Engenheiro de software com x Anos de experiência, etc... "
            "NUNCA apague, sobrescreva para null ou limpe campos que já estiverem preenchidos, a menos que o usuário peça explicitamente para REMOVER algo. "
            "Exemplo: Se o perfil tiver 'hardSkills': ['Python', 'React'] e o usuário disser 'quero remover React', o JSON final deve ser 'hardSkills': ['Python']. "
            "hardSkills são habilidades técnicas e softSkills são habilidades comportamentais, SEMPRE separe hardSkills e softSkills da melhor forma possível. "
            "Quando o usuário cita habilidades técnicas e comportamentais, ele está citando hardSkills e softSkills. "
            "Se o usuário pedir para REMOVER alguma skill, experiência ou formação, remova EXATAMENTE esse item do JSON final, mantendo os demais intactos. "
            "Habilidades técnicas são hardSkills e habilidades comportamentais são softSkills. "
            "Sempre atualize a visão atual após remover uma experiência ou outro campo, refletindo a nova realidade do perfil. "
            "IMPORTANTE - MAPEAMENTOS OBRIGATÓRIOS: "
            "Para employmentRelationship: CLT → EMPLOYEE, PJ/Pessoa Jurídica → CONTRACTOR, Freelancer/Autônomo → FREELANCER, Estágio/Estagiário → INTERN, Trainee → TRAINEE, Voluntário → VOLUNTEER. "
            "Para workFormat: Presencial → PRESENTIAL, Remoto/Home Office → REMOTE, Híbrido → HYBRID. "
            "Para status de educação: Concluído/Completo → COMPLETED, Em andamento/Cursando → IN_PROGRESS, Abandonado → DROPPED, Pausado/Trancado → PAUSED. "
            "Para courseType: Ensino Fundamental → ELEMENTARY, Ensino Médio → HIGH_SCHOOL, Técnico → TECHNICIAN, Graduação/Superior → UNDERGRADUATE, Pós-graduação/Especialização → POSTGRADUATE, Mestrado → MASTER, Doutorado → DOCTORATE. "
            "Para level de idiomas: Nativo → NATIVE, Bilíngue → BILINGUAL, Fluente → FLUENT, Avançado → ADVANCED, Intermediário → INTERMEDIATE, Básico/Iniciante → BEGINNER. "
            "Para gender: Masculino → MASCULINO, Feminino → FEMININO, Não-binário → NAO_BINARIO, Prefiro não informar → PREFIRO_NAO_INFORMAR. "
            "Para maritalStatus: Solteiro → SINGLE, Casado → MARRIED, Divorciado → DIVORCED. "
            "A visão atual deve conter um resumo de 4 a 5 linhas baseadas em todo o perfil do usuário. "
            "Caso o usuário diga algo sobre o futuro, atualiza a visao_futuro com base no que o usuário disse, infira o que for possível e criar de 4 a 5 linhas sempre que possível. "
            "Todas as datas devem estar no formato ISO YYYY-MM-DD "
            "Caso o usuário envie novas informações, faça o merge com o que já existe, sempre complementando."
            "Se não conseguir preencher um campo novo, coloque como null. Use sempre o seguinte schema de exemplo, inclusive com objetos para experiências e formações:\n\n"
            f"{json.dumps(schema_exemplo, ensure_ascii=False, indent=2)}\n\n"
            "Perfil profissional atual:\n"
            f"{json.dumps(current_profile, ensure_ascii=False, indent=2)}\n\n"
            "Novas informações do usuário ou solicitação:\n"
            f"{content}\n\n"
            "Sempre faça o que o usuário solicitou. \n"
            "A resposta deve ser apenas o JSON atualizado seguindo fielmente o schema acima, sem comentários."
        )
        
        return prompt
    
    def format_update_result(self, result: Dict[str, Any]) -> str:
        """
        Format update result for user display.
        
        Args:
            result: The result from execute() method
            
        Returns:
            Formatted string for display
        """
        profile = result.get("profile", {})
        
        lines = [
            "✅ **Perfil Atualizado com Sucesso**",
            "",
            "Suas informações foram processadas e seu perfil foi atualizado.",
            "",
            "**Resumo das informações atualizadas:**"
        ]
        
        # Show key updated fields
        if profile.get("firstName") and profile.get("lastName"):
            lines.append(f"• **Nome:** {profile['firstName']} {profile['lastName']}")
        
        if profile.get("email"):
            lines.append(f"• **Email:** {profile['email']}")
        
        if profile.get("city") and profile.get("state"):
            lines.append(f"• **Localização:** {profile['city']}, {profile['state']}")
        
        if profile.get("hardSkills"):
            skills = ", ".join(profile["hardSkills"][:5])
            if len(profile["hardSkills"]) > 5:
                skills += f" e mais {len(profile['hardSkills']) - 5}"
            lines.append(f"• **Habilidades Técnicas:** {skills}")
        
        if profile.get("softSkills"):
            skills = ", ".join(profile["softSkills"][:3])
            if len(profile["softSkills"]) > 3:
                skills += f" e mais {len(profile['softSkills']) - 3}"
            lines.append(f"• **Habilidades Comportamentais:** {skills}")
        
        if profile.get("experiences"):
            lines.append(f"• **Experiências:** {len(profile['experiences'])} registrada(s)")
        
        if profile.get("education"):
            lines.append(f"• **Formação:** {len(profile['education'])} registrada(s)")
        
        lines.extend([
            "",
            "💡 **Próximos passos:**",
            "• Digite 'mostrar perfil' para ver seu perfil completo",
            "• Digite 'buscar vagas' para encontrar oportunidades",
            "• Continue adicionando informações para melhorar seu perfil"
        ])
        
        return "\n".join(lines)