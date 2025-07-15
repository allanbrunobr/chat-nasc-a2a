import asyncio
import logging
import json
from dotenv import load_dotenv
import os

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()

# Testar diretamente a ferramenta update_state
async def test_update_state_direct():
    """Testa a ferramenta update_state diretamente"""
    from nai.tools.update_state import update_state
    from google.adk.tools import ToolContext
    
    # Simular contexto de ferramenta
    class MockState:
        def __init__(self):
            self.data = {
                "perfil_profissional": {
                    "firstName": "João",
                    "lastName": "Silva", 
                    "email": "joao@email.com",
                    "phone": None  # Sem telefone ainda
                }
            }
        
        def get(self, key, default=None):
            return self.data.get(key, default)
        
        def __setitem__(self, key, value):
            self.data[key] = value
    
    # Criar contexto mock
    class MockToolContext:
        def __init__(self):
            self.state = MockState()
    
    context = MockToolContext()
    
    # Testar atualização de telefone
    print("\n=== TESTE 1: Atualização de telefone ===")
    result = update_state("meu telefone é 81 99956-5656", context)
    print(f"Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
    print(f"Telefone atualizado: {context.state.data['perfil_profissional'].get('phone')}")
    
    return result

# Testar via API
async def test_via_api():
    """Testa via API completa"""
    import httpx
    
    url = "http://localhost:8080/run"
    
    # Dados do teste
    data = {
        "user_id": "test_user_123",
        "session_id": "test_session_456",
        "message": "meu telefone é 81 99956-5656"
    }
    
    print("\n=== TESTE 2: Via API ===")
    print(f"Enviando: {json.dumps(data, indent=2)}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, timeout=30.0)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        # Analisar a resposta
        if response.status_code == 200:
            response_data = response.json()
            if "response" in response_data:
                print(f"\nResposta do LLM: {response_data['response']}")
            else:
                print(f"\nERRO: Resposta sem campo 'response': {response_data}")
        else:
            print(f"\nERRO HTTP: {response.status_code}")

# Verificar formato de resposta esperado
async def test_response_format():
    """Analisa o formato de resposta esperado pelo frontend"""
    print("\n=== ANÁLISE DO FORMATO DE RESPOSTA ===")
    
    # O frontend espera:
    # { "response": "texto da resposta" }
    
    # Mas se o update_state retorna erro, pode estar retornando algo diferente
    
    # Vamos simular diferentes cenários
    scenarios = [
        {"response": "Telefone atualizado com sucesso!"},  # Formato correto
        {"status": "success", "message": "Telefone atualizado"},  # Formato errado 1
        {"error": "Algum erro ocorreu"},  # Formato errado 2
        "Apenas uma string",  # Formato errado 3
    ]
    
    for i, scenario in enumerate(scenarios):
        print(f"\nCenário {i+1}: {scenario}")
        print(f"Tipo: {type(scenario)}")
        if isinstance(scenario, dict) and "response" in scenario:
            print("✅ Formato CORRETO para o frontend")
        else:
            print("❌ Formato INCORRETO - causará erro no frontend")

async def main():
    print("=== TESTE DO PROBLEMA UPDATE_STATE ===")
    
    # Teste 1: Direto na ferramenta
    await test_update_state_direct()
    
    # Teste 2: Via API (apenas se o servidor estiver rodando)
    try:
        await test_via_api()
    except Exception as e:
        print(f"\nERRO ao testar via API (servidor não está rodando?): {e}")
    
    # Teste 3: Análise de formato
    await test_response_format()

if __name__ == "__main__":
    asyncio.run(main())