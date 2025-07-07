#!/usr/bin/env python3
"""
Script para inicializar os servidores híbridos do NAI
- ADK API na porta 8080
- A2A API na porta 8082

Este script permite executar ambos os servidores simultaneamente
para suportar tanto o protocolo ADK quanto o protocolo A2A.
"""

import subprocess
import sys
import time
import signal
import os
from multiprocessing import Process
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def start_adk_server():
    """Inicia o servidor ADK na porta 8080"""
    print("🚀 Iniciando servidor ADK na porta 8080...")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api.main:app", 
            "--host", "0.0.0.0",
            "--port", "8080",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("🛑 Servidor ADK interrompido")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor ADK: {e}")

def start_a2a_server():
    """Inicia o servidor A2A na porta configurada (padrão 8082)"""
    a2a_port = os.getenv("A2A_PORT", "8082")
    print(f"🚀 Iniciando servidor A2A na porta {a2a_port}...")
    try:
        subprocess.run([
            sys.executable, "nai_a2a/server.py"
        ], check=True)
    except KeyboardInterrupt:
        print("🛑 Servidor A2A interrompido")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor A2A: {e}")

def main():
    """Função principal para iniciar ambos os servidores"""
    print("=" * 60)
    print("🔥 NAI - Inicializando Servidores Híbridos")
    print("=" * 60)
    print("📋 Configuração:")
    print(f"   • ADK API: http://localhost:8080")
    print(f"   • A2A API: http://localhost:{os.getenv('A2A_PORT', '8082')}")
    print("=" * 60)
    
    # Verifica se as variáveis de ambiente estão configuradas
    required_vars = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Variáveis de ambiente obrigatórias não configuradas: {', '.join(missing_vars)}")
        print("   Configure o arquivo .env antes de continuar.")
        sys.exit(1)
    
    # Cria processos para cada servidor
    adk_process = Process(target=start_adk_server)
    a2a_process = Process(target=start_a2a_server)
    
    try:
        # Inicia os servidores
        print("🔄 Iniciando processos...")
        adk_process.start()
        time.sleep(2)  # Aguarda um pouco antes de iniciar o segundo servidor
        a2a_process.start()
        
        print("✅ Servidores iniciados com sucesso!")
        print("📊 Endpoints disponíveis:")
        print("   • ADK API: http://localhost:8080/run")
        print("   • A2A Agent Card: http://localhost:8082/.well-known/agent.json")
        print("   • A2A Execute: http://localhost:8082/execute")
        print("   • Health Check: http://localhost:8082/api/health")
        print("\n⚠️  Pressione Ctrl+C para parar ambos os servidores")
        
        # Aguarda os processos terminarem
        adk_process.join()
        a2a_process.join()
        
    except KeyboardInterrupt:
        print("\n🛑 Parando servidores...")
        
        # Termina os processos graciosamente
        if adk_process.is_alive():
            adk_process.terminate()
            adk_process.join(timeout=5)
            if adk_process.is_alive():
                adk_process.kill()
        
        if a2a_process.is_alive():
            a2a_process.terminate()
            a2a_process.join(timeout=5)
            if a2a_process.is_alive():
                a2a_process.kill()
        
        print("✅ Servidores parados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
