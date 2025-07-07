"""
AgentCard definition for NAI - SENAI's Intelligent Assistant

Defines the A2A capabilities and skills available through the NAI agent.
"""

from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from typing import List
import os

def create_nai_agent_card() -> AgentCard:
    """Create the AgentCard for NAI with all available skills"""
    
    # Define the skills based on existing ADK tools
    skills = [
        AgentSkill(
            id="retrieve_user_profile",
            name="Buscar Perfil do Usuário",
            description="Recupera o perfil completo do usuário incluindo dados pessoais, educação, experiências e habilidades",
            inputModes=["text/plain"],
            outputModes=["text/plain"],
            tags=["profile", "user", "data"]
        ),
        AgentSkill(
            id="save_user_profile",
            name="Salvar Perfil do Usuário",
            description="Salva ou atualiza o perfil do usuário com novos dados fornecidos",
            inputModes=["text/plain", "application/json"],
            outputModes=["text/plain"],
            tags=["profile", "save", "update"]
        ),
        AgentSkill(
            id="find_job_matches",
            name="Encontrar Vagas Compatíveis",
            description="Busca vagas de emprego compatíveis com o perfil do usuário",
            inputModes=["text/plain"],
            outputModes=["text/plain"],
            tags=["job", "vacancy", "match", "career"]
        ),
        AgentSkill(
            id="retrieve_vacancy",
            name="Buscar Vagas",
            description="Busca vagas de emprego por palavras-chave ou termos de pesquisa",
            inputModes=["text/plain", "application/json"],
            outputModes=["text/plain"],
            tags=["jobs", "vacancy", "search", "employment"]
        ),
        AgentSkill(
            id="update_state",
            name="Atualizar Perfil com IA",
            description="Atualiza o perfil do usuário usando IA para processar texto natural, currículos ou informações desestruturadas",
            inputModes=["text/plain", "application/json"],
            outputModes=["text/plain"],
            tags=["profile", "update", "ai", "parsing", "resume"]
        ),
        AgentSkill(
            id="analyze_skill_gaps",
            name="Analisar Lacunas de Habilidades",
            description="Identifica lacunas de habilidades entre o perfil atual e uma carreira desejada",
            inputModes=["text/plain"],
            outputModes=["text/plain"],
            tags=["skills", "gap", "analysis", "career"]
        ),
        AgentSkill(
            id="recommend_courses",
            name="Recomendar Cursos",
            description="Recomenda cursos e treinamentos baseados nas necessidades do usuário",
            inputModes=["text/plain"],
            outputModes=["text/plain"],
            tags=["courses", "training", "education", "recommendation"]
        ),
        AgentSkill(
            id="chat",
            name="Conversar com Assistente",
            description="Conversa geral com o assistente NAI para orientação profissional e suporte",
            inputModes=["text/plain", "application/json"],
            outputModes=["text/plain"],
            tags=["chat", "conversation", "assistant", "guidance"]
        )
    ]
    
    # Define agent capabilities
    capabilities = AgentCapabilities(
        streaming=True,  # Support Server-Sent Events
        pushNotifications=False,  # Not implemented yet
        stateTransitionHistory=True  # Track task state changes
    )
    
    # Get base URL from environment or use default
    base_url = os.getenv("A2A_BASE_URL", "http://localhost:8081")
    
    # Create the AgentCard
    agent_card = AgentCard(
        name="NAI - Assistente Inteligente do SENAI",
        description=(
            "NAI é o assistente virtual do SENAI que ajuda usuários com desenvolvimento "
            "profissional através de criação de perfil, matching de vagas, análise de "
            "lacunas de habilidades e recomendações de cursos."
        ),
        version="1.0.0",
        url=base_url,
        skills=skills,
        defaultInputModes=["text/plain", "application/json"],
        defaultOutputModes=["text/plain"],
        capabilities=capabilities,
        protocolVersion="0.2.5"  # A2A protocol version
    )
    
    return agent_card

# Export the agent card instance
NAI_AGENT_CARD = create_nai_agent_card()