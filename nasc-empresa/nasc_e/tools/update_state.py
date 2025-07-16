"""
Ferramenta para atualizar o perfil da empresa no state
"""

import os
import json
import re
import logging
from dotenv import load_dotenv
from google.adk.tools import FunctionTool, ToolContext
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

def update_state(content: str, tool_context: ToolContext) -> dict:
    """
    Atualiza o perfil da empresa no state, recebendo no content a solicitação do usuário,
    preenchendo os campos a partir de uma nova resposta do usuário, utilizando o Gemini
    para retornar o JSON do perfil atualizado, SEMPRE obedecendo ao schema empresarial.
    """
    logger.info("=== INÍCIO update_state (empresa) ===")

    if not content:
        logger.error("Texto vazio fornecido")
        return {"status": "error", "message": "Texto vazio fornecido."}

    perfil_atual = tool_context.state.get("company_info", {
        "companyName": None,
        "cnpj": None,
        "address": None,
        "city": None,
        "state": None,
        "country": None,
        "zipcode": None,
        "sector": None,
        "companySize": None,
        "foundationDate": None,
        "website": None,
        "email": None,
        "phone": None,
        "description": None
    })

    schema_exemplo = {
        "companyName": "Exemplo S.A.",
        "cnpj": "12.345.678/0001-99",
        "address": "Rua Exemplo, 123",
        "city": "Cuiabá",
        "state": "MT",
        "country": "Brasil",
        "zipcode": "78000-000",
        "sector": "Tecnologia da Informação",
        "companySize": "Médio porte",
        "foundationDate": "2005-08-15",
        "website": "https://exemplo.com.br",
        "email": "contato@exemplo.com.br",
        "phone": "(65) 99999-8888",
        "description": "Empresa de tecnologia focada em soluções inovadoras para o mercado público e privado."
    }

    prompt = (
        "Você é um assistente de RH empresarial e deve completar/atualizar o perfil da empresa. "
        "Aqui está o JSON atual do perfil da empresa, seguido de novas informações fornecidas pelo usuário (texto, resposta, etc). "
        "Siga estritamente o schema abaixo na sua resposta final. Preencha apenas os campos que conseguir inferir a partir das novas informações. "
        "NUNCA apague, sobrescreva para null ou limpe campos que já estiverem preenchidos, a menos que o usuário peça explicitamente para REMOVER algo. "
        "Exemplo: Se o perfil tiver 'sector': 'Tecnologia' e o usuário disser 'quero remover Tecnologia', o JSON final deve ser 'sector': null. "
        "Sempre que possível, normalize os dados (ex: CNPJ no formato 00.000.000/0000-00, datas em YYYY-MM-DD, etc). "
        "Se o usuário pedir para REMOVER algum campo, remova EXATAMENTE esse item do JSON final, mantendo os demais intactos. "
        "Se não conseguir preencher um campo novo, coloque como null. Use sempre o seguinte schema de exemplo:\n\n"
        f"{json.dumps(schema_exemplo, ensure_ascii=False, indent=2)}\n\n"
        "Perfil empresarial atual:\n"
        f"{json.dumps(perfil_atual, ensure_ascii=False, indent=2)}\n\n"
        "Novas informações do usuário ou solicitação:\n"
        f"{content}\n\n"
        "Sempre faça o que o usuário solicitou. \n"
        "A resposta deve ser apenas o JSON atualizado seguindo fielmente o schema acima, sem comentários."
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=4096
        )
    )

    json_match = re.search(r'\{[\s\S]*\}', response.text)
    if not json_match:
        return {"status": "error", "message": "Gemini não retornou JSON válido."}

    perfil_json = json.loads(json_match.group(0))

    if tool_context is not None:
        tool_context.state["company_info"] = perfil_json
    return {
        "status": "success",
        "company_info": perfil_json
    }

# Registrar a ferramenta
update_state_tool = FunctionTool(update_state) 