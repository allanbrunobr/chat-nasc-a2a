#!/usr/bin/env python3
"""
Exemplos de como usar metadata com skills no A2A
"""

import json

# Exemplo 1: Recuperar perfil de usuário
retrieve_profile_example = {
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
        "message": {
            "messageId": "msg-123",
            "role": "user",
            "parts": [{"text": "show profile"}],  # Texto é ignorado quando tem skill
            "metadata": {
                "skill": "retrieve_user_profile",  # Skill específica a executar
                "user_id": "usuario123"           # Parâmetros da skill
            }
        }
    }
}

print("1️⃣ EXEMPLO - Recuperar Perfil:")
print(json.dumps(retrieve_profile_example, indent=2))
print("\n" + "="*60 + "\n")

# Exemplo 2: Salvar perfil de usuário
save_profile_example = {
    "jsonrpc": "2.0", 
    "method": "message/stream",
    "params": {
        "message": {
            "messageId": "msg-456",
            "role": "user",
            "parts": [{"text": "save my profile"}],  # Texto ignorado
            "metadata": {
                "skill": "save_user_profile",      # Skill específica
                "user_id": "usuario123",           # ID do usuário
                "profile_data": {                  # Dados do perfil
                    "firstName": "João",
                    "lastName": "Silva",
                    "email": "joao@example.com",
                    "city": "São Paulo",
                    "hardSkills": ["Python", "Java"],
                    "softSkills": ["Liderança"]
                }
            }
        }
    }
}

print("2️⃣ EXEMPLO - Salvar Perfil:")
print(json.dumps(save_profile_example, indent=2))
print("\n" + "="*60 + "\n")

# Exemplo 3: Buscar vagas
find_jobs_example = {
    "jsonrpc": "2.0",
    "method": "message/stream", 
    "params": {
        "message": {
            "messageId": "msg-789",
            "role": "user",
            "parts": [{"text": "find jobs"}],
            "metadata": {
                "skill": "find_job_matches",    # Skill de busca
                "user_id": "usuario123",        # Usuário
                "limit": 10,                    # Limite de resultados
                "location": "São Paulo",        # Filtros opcionais
                "remote": True
            }
        }
    }
}

print("3️⃣ EXEMPLO - Buscar Vagas:")
print(json.dumps(find_jobs_example, indent=2))
print("\n" + "="*60 + "\n")

# Comparação: SEM metadata (usa LLM para interpretar)
without_metadata_example = {
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
        "message": {
            "messageId": "msg-999",
            "role": "user",
            "parts": [{"text": "mostre meu perfil"}]
            # SEM metadata - o LLM vai interpretar o texto
        }
    }
}

print("4️⃣ EXEMPLO - SEM Metadata (usa LLM):")
print(json.dumps(without_metadata_example, indent=2))
print("""
Diferenças:
- COM metadata: Executa a skill diretamente, mais rápido e preciso
- SEM metadata: LLM interpreta o texto e decide qual ação tomar
""")