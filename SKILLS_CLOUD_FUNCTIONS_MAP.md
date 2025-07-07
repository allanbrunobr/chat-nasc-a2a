# Mapeamento: Skills A2A → Cloud Functions

## 🎯 Skills Nativas A2A Implementadas

### 1. 📋 retrieve_user_profile
```
Skill A2A: retrieve_user_profile
    ↓
Cloud Function: get-user-profile-parallelism
URL: https://southamerica-east1-setasc-central-emp-dev.cloudfunctions.net/get-user-profile-parallelism
Método: GET
O que faz: Busca o perfil completo do candidato
```

### 2. 💾 save_user_profile  
```
Skill A2A: save_user_profile
    ↓
Cloud Function: persist-user-profile-complete
URL: https://southamerica-east1-setasc-central-emp-dev.cloudfunctions.net/persist-user-profile-complete
Método: POST
O que faz: Salva/atualiza o perfil do candidato
```

### 3. 🔍 find_job_matches
```
Skill A2A: find_job_matches
    ↓
Cloud Function: get-user-matches (ou setasc-search-improved)
URL Principal: https://setasc-search-improved-52a7xwbczq-rj.a.run.app
URL Fallback: https://southamerica-east1-setasc-central-emp-dev.cloudfunctions.net/get-user-matches
Método: POST (improved) ou GET (legacy)
O que faz: Encontra vagas compatíveis com o perfil
```

## 🔧 Tools ADK (ainda não migradas para A2A nativo)

### 4. 🔎 retrieve_vacancy
```
ADK Tool: retrieve_vacancy
    ↓
Cloud Function: setasc-search-vacancy
URL: https://setasc-search-vacancy-363270572699.southamerica-east1.run.app
Método: GET
O que faz: Busca vagas por palavras-chave
```

### 5. 🤖 update_state
```
ADK Tool: update_state
    ↓
API: Google Gemini (não é Cloud Function)
O que faz: Usa IA para processar e estruturar dados do perfil
```

## 📊 Status de Implementação

| Funcionalidade | ADK Tool | A2A Skill | Cloud Function |
|----------------|----------|-----------|----------------|
| Buscar Perfil | ✅ retrieve_user_info | ✅ retrieve_user_profile | get-user-profile-parallelism |
| Salvar Perfil | ✅ save_user_profile | ✅ save_user_profile | persist-user-profile-complete |
| Match de Vagas | ✅ retrieve_match | ✅ find_job_matches | get-user-matches / search-improved |
| Buscar Vagas | ✅ retrieve_vacancy | ❌ Não implementado | setasc-search-vacancy |
| Atualizar com IA | ✅ update_state | ❌ Não implementado | Gemini API |

## 🚀 Próximas Skills para Implementar

Segundo a documentação, existem mais funcionalidades planejadas:
- `retrieve_gap` - Análise de lacunas de competências
- `retrieve_courses` - Recomendação de cursos
- `retrieve_capacity` - Serviço de capacidades/habilidades

## 💡 Como Funciona

1. **Cliente A2A** envia mensagem com metadata:
```json
{
  "metadata": {
    "skill": "retrieve_user_profile",
    "user_id": "123"
  }
}
```

2. **NAI A2A** identifica a skill e executa

3. **Skill A2A** chama a Cloud Function correspondente

4. **Cloud Function** retorna os dados

5. **NAI A2A** formata e retorna ao cliente