"""
API Principal do NASC-E - Chat Empresarial
"""

import os
import logging
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai.types import Content, Part
from nasc_e.agent import empresa_agent
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="NASC-E API",
    description="API do Assistente Empresarial do SETASC",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar banco de dados para sessões
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "setasc_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configurar serviço de sessão
session_service = DatabaseSessionService(db_url=DB_URL)

# Criar runner do agente
runner = Runner(
    app_name="NASC-E",
    agent=empresa_agent,
    session_service=session_service
)

# Models Pydantic
class ChatRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

# Endpoints
@app.get("/health")
async def health_check():
    """Verificar status do serviço"""
    return {
        "status": "healthy",
        "service": "NASC-E",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/run", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal do chat empresarial
    """
    try:
        logger.info(f"Mensagem recebida do usuário {request.user_id}: {request.message[:50]}...")
        
        # Criar conteúdo da mensagem
        user_content = Content(parts=[Part(text=request.message)])
        
        response_text = ""
        session_id = request.session_id or f"{request.user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Garante que a sessão existe antes de rodar o runner
        try:
            existing_session = session_service.get_session(session_id)
            logger.info(f"Usando sessão existente: {session_id}")
        except Exception as e:
            logger.info(f"Sessão não encontrada ({str(e)}). Criando nova sessão: {session_id}")
            try:
                await session_service.create_session(session_id=session_id, user_id=request.user_id, app_name="NASC-E")
                logger.info(f"Nova sessão criada com sucesso: {session_id}")
            except Exception as create_error:
                if "duplicate key" in str(create_error):
                    logger.warning(f"Sessão já existe (race condition): {session_id}")
                    # Se já existe, continuar normalmente
                else:
                    logger.error(f"Erro ao criar sessão: {str(create_error)}")
                    raise
        
        try:
            async for event in runner.run_async(
                session_id=session_id,
                user_id=request.user_id,
                new_message=user_content
            ):
                # Processar eventos do agente
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text
        except Exception as e:
            # Tratamento especial para erro de sessão não encontrada
            if "Session not found" in str(e):
                logger.warning(f"Sessão não encontrada: {session_id}. Criando nova sessão.")
                # Cria nova sessão e tenta novamente
                session_id = f"{request.user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                response_text = ""
                try:
                    await session_service.create_session(
                        session_id=session_id, 
                        user_id=request.user_id, 
                        app_name="NASC-E",
                    )
                    logger.info(f"Nova sessão criada após erro: {session_id}")
                except Exception as e_create:
                    if "duplicate key" in str(e_create):
                        logger.warning(f"Sessão já existe, continuando: {session_id}")
                    else:
                        logger.error(f"Erro ao criar nova sessão no banco: {str(e_create)}")
                        return ChatResponse(
                            response=f"Erro ao criar nova sessão: {str(e_create)}",
                            session_id=session_id
                        )
                try:
                    async for event in runner.run_async(
                        session_id=session_id,
                        user_id=request.user_id,
                        new_message=user_content
                    ):
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                if part.text:
                                    response_text += part.text
                except Exception as e2:
                    logger.error(f"Erro ao processar mensagem após recriar sessão: {str(e2)}")
                    return ChatResponse(
                        response=f"Erro ao processar mensagem após recriar sessão: {str(e2)}",
                        session_id=session_id
                    )
                return ChatResponse(
                    response="Sua sessão anterior expirou ou não foi encontrada. Iniciando uma nova sessão.\n" + response_text,
                    session_id=session_id
                )
            else:
                logger.error(f"Erro ao processar mensagem: {str(e)}")
                return ChatResponse(
                    response=f"Erro ao processar mensagem: {str(e)}",
                    session_id=request.session_id or "error"
                )
        
        logger.info(f"Resposta enviada: {response_text[:100]}...")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Erro inesperado ao processar mensagem: {str(e)}")
        return ChatResponse(
            response=f"Erro inesperado ao processar mensagem: {str(e)}",
            session_id=request.session_id or "error"
        )


# Inicializar aplicação
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("EMPRESA_API_PORT", "8081"))
    
    logger.info(f"Iniciando NASC-E API na porta {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=True
    )