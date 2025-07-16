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
        
        # Executar agente
        response_text = ""
        session_id = request.session_id or f"{request.user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
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
        
        logger.info(f"Resposta enviada: {response_text[:100]}...")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        return ChatResponse(
            response=f"Erro ao processar mensagem: {str(e)}",
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