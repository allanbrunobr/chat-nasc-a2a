#!/usr/bin/env python3
"""
Script para iniciar o servidor NASC-E
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def main():
    """Iniciar servidor NASC-E"""
    
    # Configurações
    host = "0.0.0.0"
    port = int(os.getenv("EMPRESA_API_PORT", "8081"))
    reload = os.getenv("ENV", "development") == "development"
    
    print(f"""
    ╔══════════════════════════════════════╗
    ║       NASC-E - Chat Empresarial      ║
    ║         SETASC MT - v1.0.0          ║
    ╚══════════════════════════════════════╝
    
    🚀 Iniciando servidor na porta {port}...
    📍 URL: http://localhost:{port}
    📚 Docs: http://localhost:{port}/docs
    """)
    
    # Verificar dependências críticas
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERRO: GOOGLE_API_KEY não configurada no .env")
        sys.exit(1)
    
    # Iniciar servidor
    try:
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=os.getenv("LOG_LEVEL", "info").lower()
        )
    except KeyboardInterrupt:
        print("\n👋 Servidor encerrado")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()