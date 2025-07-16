#!/usr/bin/env python3
"""
Script de teste para o NASC-E (Chat Empresarial)
"""

import requests
import json
import time
from datetime import datetime

# Configurações
BASE_URL = "http://localhost:8081"
HEADERS = {
    "Content-Type": "application/json"
}

def print_header(text):
    """Imprimir cabeçalho formatado"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def test_health():
    """Testar endpoint de health"""
    print_header("Teste: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_chat(message, session_id=None):
    """Testar chat principal"""
    print_header(f"Teste: Chat - '{message[:50]}...'")
    
    payload = {
        "user_id": "empresa_test_user",
        "message": message
    }
    
    if session_id:
        payload["session_id"] = session_id
    
    try:
        response = requests.post(
            f"{BASE_URL}/run",
            headers=HEADERS,
            json=payload
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Session ID: {data.get('session_id')}")
            print(f"\nResposta da NASC-E:\n{data.get('response')}")
            return data.get('session_id')
        else:
            print(f"❌ Erro: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


def run_conversation_tests():
    """Executar testes de conversação"""
    print("\n" + "="*60)
    print("  TESTES DE CONVERSAÇÃO NASC-E")
    print("="*60)
    
    # Sequência de testes
    test_messages = [
        "Olá, sou da empresa XYZ",
        "Quero cadastrar uma nova vaga",
        "O cargo é Analista de Dados Junior",
        "Mostre candidatos para minha vaga de analista",
        "Quais candidatos se aplicaram às minhas vagas?",
        "Atualize o status do candidato João Silva para 'em análise'"
    ]
    
    session_id = None
    
    for message in test_messages:
        session_id = test_chat(message, session_id)
        time.sleep(2)  # Aguardar entre mensagens
        
        if not session_id:
            print("❌ Falha no teste, interrompendo...")
            break

def main():
    """Executar todos os testes"""
    print("""
    ╔══════════════════════════════════════╗
    ║    NASC-E - Testes do Sistema       ║
    ╚══════════════════════════════════════╝
    """)
    
    # Verificar se o servidor está rodando
    if not test_health():
        print("\n❌ Servidor não está respondendo. Verifique se está rodando na porta 8081")
        return
    
    print("\n✅ Servidor está rodando!")
    
    # Menu de opções
    while True:
        print("\n" + "-"*40)
        print("Escolha uma opção:")
        print("1. Testar conversação completa")
        print("2. Testar mensagem específica")
        print("0. Sair")
        
        choice = input("\nOpção: ").strip()
        
        if choice == "1":
            run_conversation_tests()
        elif choice == "2":
            message = input("Digite a mensagem: ")
            test_chat(message)
        elif choice == "0":
            print("\n👋 Encerrando testes...")
            break
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main()