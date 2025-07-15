"""
Configuração do agente NASC-E (Empresarial)
"""

import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
import logging

logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Importar prompt
from .prompt import EMPRESA_AGENT_INSTR

# Importar ferramentas
from .tools import (
    retrieve_company_info_tool,
    manage_vacancy_tool,
    retrieve_matches_tool,
    retrieve_applicants_tool
)

# Verificar API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY não encontrada nas variáveis de ambiente")

logger.debug("Inicializando agente NASC-E (Empresarial) com modelo gemini-2.0-flash")

# Criar agente empresarial
empresa_agent = LlmAgent(
    name="NASC-E",
    model="gemini-2.0-flash",
    description="Assistente empresarial do SETASC para gestão de vagas e recrutamento",
    instruction=EMPRESA_AGENT_INSTR,
    tools=[
        retrieve_company_info_tool,
        manage_vacancy_tool,
        retrieve_matches_tool,
        retrieve_applicants_tool
    ],
    include_contents="default"
)

logger.info("Agente NASC-E carregado com ferramentas empresariais do SETASC.")