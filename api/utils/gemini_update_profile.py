import os
import json
from google import genai
from google.genai import types
import requests
import re

def parse_gemini_json(text: str) -> dict:
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        raise ValueError("Resposta do Gemini não contém JSON válido.")
    return json.loads(match.group(0))

DEFAULT_PROFILE_URL = "https://southamerica-east1-setasc-central-emp-dev.cloudfunctions.net/xertica-get-user-profile-complete"
DEFAULT_API_KEY = ""

USER_PROFILE_URL = os.getenv("USER_PROFILE_URL", DEFAULT_PROFILE_URL)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", DEFAULT_API_KEY)

print(f"USER_PROFILE_URL: {USER_PROFILE_URL}")

client = genai.Client(api_key=GOOGLE_API_KEY)

def retrieve_user_info_raw(user_id: str) -> dict:
    url = f"{USER_PROFILE_URL}/{user_id}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()

def save_user_profile_raw(perfil: dict) -> dict:
    print("--------------------------------------")
    print(f"PERFIL: {perfil}")
    print("--------------------------------------")
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    response = requests.post(USER_PROFILE_URL, json=perfil, headers=headers, timeout=20)
    response.raise_for_status()
    return response

def gemini_enrich_profile(user_id: str) -> dict:
    perfil = retrieve_user_info_raw(user_id)

    prompt = (
        "Você é um assistente de RH. Com base nos dados abaixo, infira a visão atual e futura do usuário, sempre na primeira pessoa. "
        "Use apenas os dados fornecidos para gerar a nova 'visao_atual'. Não altere os demais campos. "
        "**Retorne apenas o JSON completo e válido, sem explicações, texto ou marcação.**\n\n"
        f"Informações atuais:\n{json.dumps(perfil, ensure_ascii=False, indent=2)}"
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=8096
        )
    )

    raw_text = response.candidates[0].content.parts[0].text
    print(f"Resposta bruta: {raw_text}", flush=True)
    updated = parse_gemini_json(raw_text)

    print(f"Retorno: {updated}",flush=True)
    save_user_profile_raw(updated)
    return updated