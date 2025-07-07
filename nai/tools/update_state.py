# tools/update_state.py

from google.adk.tools import FunctionTool, ToolContext
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
import re
import logging

logger = logging.getLogger(__name__)
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

def is_perfil_criado(perfil_profissional: dict) -> bool:
    """
    Verifica se o perfil está criado conforme as regras de negócio.
    """
    return any([
        bool(perfil_profissional.get("visao_atual")),
        bool(perfil_profissional.get("visao_futuro")),
        perfil_profissional.get("formacoes"),
        perfil_profissional.get("experiencias"),
        perfil_profissional.get("capacidades"),
        perfil_profissional.get("conhecimentos"),
    ])

def update_state(content: str, tool_context: ToolContext) -> dict:
    """
    Atualiza o perfil profissional no state, recebendo no content a solicitação do usuário, preenchendo os campos
    a partir de uma nova resposta do usuário,
    utilizando o Gemini para retornar o JSON do perfil atualizado,
    SEMPRE obedecendo ao schema solicitado.
    """
    logger.info("=== INÍCIO update_state ===")
    # logger.debug(f"Content recebido: {content}")

    if not content:
        logger.error("Texto vazio fornecido")
        return {"status": "error", "message": "Texto vazio fornecido."}

    perfil_atual = tool_context.state.get("perfil_profissional", {
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
    })

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
            max_output_tokens=8096
        )
    )

    json_match = re.search(r'\{[\s\S]*\}', response.text)
    if not json_match:
        return {"status": "error", "message": "Gemini não retornou JSON válido."}

    perfil_json = json.loads(json_match.group(0))

    if tool_context is not None:
        tool_context.state["perfil_profissional"] = perfil_json
    return {
        "status": "success",
        "perfil_profissional": perfil_json
    }

update_state_tool = FunctionTool(func=update_state)
