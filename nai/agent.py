import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
import logging

logger = logging.getLogger(__name__)
from .prompt import ROOT_AGENT_INSTR

from .tools import (
    retrieve_user_info_tool,
    save_user_profile_tool,
    update_state_tool,
    retrieve_vacancy_tool,
    retrieve_match_tool,
)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

logger.debug("Inicializando agente NASC (root) com modelo gemini-2.0-flash")

root_agent = LlmAgent(
    name="NASC",
    model="gemini-2.0-flash",
    description="Agente principal responsável por toda a orquestração de currículo, vagas e match.",
    instruction=ROOT_AGENT_INSTR,
    tools=[
        retrieve_user_info_tool,
        save_user_profile_tool,
        update_state_tool,
        retrieve_vacancy_tool,
        retrieve_match_tool
    ],
    include_contents="default"
)

logger.info("Agente NASC carregado apenas com as ferramentas principais do SETASC.")
