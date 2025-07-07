# tools/analyze_ats_score.py

from google.adk.tools import FunctionTool, ToolContext
import logging
from datetime import datetime
from nai.tools.ats_optimizer import (
    calculate_ats_score,
    generate_ats_report,
    optimize_profile_for_ats,
    analyze_profile_keywords
)

logger = logging.getLogger(__name__)


def analyze_ats_score(tool_context: ToolContext) -> dict:
    """
    Analisa o perfil do usuário e retorna score ATS com recomendações.
    
    Returns:
        dict: Contém score, análise detalhada e sugestões de melhoria
    """
    logger.info("=== INÍCIO analyze_ats_score ===")
    
    # Obtém o perfil do estado
    perfil = tool_context.state.get("perfil_profissional")
    
    if not perfil:
        logger.error("Perfil não encontrado no estado")
        return {
            "status": "error",
            "message": "Perfil não encontrado. Por favor, crie ou carregue seu perfil primeiro."
        }
    
    try:
        # Calcula o score ATS
        ats_analysis = calculate_ats_score(perfil)
        
        # Gera relatório
        report = generate_ats_report(perfil)
        
        # Gera sugestões de otimização
        optimization_suggestions = optimize_profile_for_ats(perfil)
        
        # Analisa palavras-chave do perfil
        profile_keywords = analyze_profile_keywords(perfil)
        
        # Atualiza o perfil com os dados ATS
        if tool_context and tool_context.state:
            perfil["atsScore"] = ats_analysis["percentage"]
            perfil["lastATSCheck"] = datetime.now().isoformat()
            perfil["optimizationSuggestions"] = optimization_suggestions["immediate"]
            tool_context.state["perfil_profissional"] = perfil
        
        logger.info(f"Score ATS calculado: {ats_analysis['percentage']}%")
        logger.info("=== FIM analyze_ats_score ===")
        
        # Formata resposta amigável
        response_message = f"{report}\n\n"
        
        if optimization_suggestions["immediate"]:
            response_message += "**🎯 Ações Imediatas Recomendadas:**\n"
            for i, suggestion in enumerate(optimization_suggestions["immediate"], 1):
                response_message += f"{i}. {suggestion}\n"
            response_message += "\n"
        
        if optimization_suggestions["improvements"]:
            response_message += "**💡 Melhorias Sugeridas:**\n"
            for i, improvement in enumerate(optimization_suggestions["improvements"], 1):
                response_message += f"{i}. {improvement}\n"
            response_message += "\n"
        
        if optimization_suggestions["keywords_to_add"]:
            response_message += "**🔑 Palavras-chave Recomendadas:**\n"
            response_message += f"{', '.join(optimization_suggestions['keywords_to_add'][:10])}\n\n"
        
        # Adiciona dica baseada no score
        if ats_analysis["percentage"] < 70:
            response_message += (
                "💡 **Dica:** Seu currículo precisa de melhorias significativas. "
                "Recomendo focar primeiro nas ações imediatas listadas acima. "
                "Use o comando 'otimizar currículo' para aplicar melhorias automáticas."
            )
        elif ats_analysis["percentage"] < 85:
            response_message += (
                "💡 **Dica:** Seu currículo está no caminho certo! "
                "Implemente as sugestões acima para alcançar um score excelente."
            )
        else:
            response_message += (
                "🎉 **Parabéns!** Seu currículo está muito bem otimizado para ATS. "
                "Continue mantendo-o atualizado com suas novas experiências e conquistas."
            )
        
        return {
            "status": "success",
            "message": response_message,
            "data": {
                "score": ats_analysis["percentage"],
                "section_scores": ats_analysis["section_scores"],
                "issues_count": len(ats_analysis["issues"]),
                "keywords_count": len(profile_keywords.get("general", [])),
                "suggestions_count": len(optimization_suggestions["immediate"])
            }
        }
        
    except Exception as e:
        logger.exception("Erro ao analisar score ATS")
        return {
            "status": "error",
            "message": f"Erro ao analisar compatibilidade ATS: {str(e)}"
        }


# Cria a ferramenta
analyze_ats_score_tool = FunctionTool(
    func=analyze_ats_score
)