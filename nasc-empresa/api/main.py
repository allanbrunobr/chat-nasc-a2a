"""
API Principal do NASC-E - Chat Empresarial
"""

import os
import logging
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai.types import Content, Part
from nasc_e.agent import empresa_agent
import jwt
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
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
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
session_service = DatabaseSessionService(url=DB_URL)

# Criar runner do agente
runner = Runner(agent=empresa_agent, session_service=session_service)

# Models Pydantic
class ChatRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

class VacancyCreateRequest(BaseModel):
    title: str
    position: str
    description: str
    location: str
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    salary_range: Optional[str] = None
    work_format: Optional[str] = "PRESENTIAL"
    contract_type: Optional[str] = "CLT"
    vacancies: Optional[int] = 1

# Dependência para validar autenticação
async def validate_company_user(authorization: str = Header(None)):
    """
    Valida que o usuário tem role=EMPRESA
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    token = authorization.split(" ")[1]
    
    try:
        # Decodificar token JWT
        payload = jwt.decode(
            token, 
            os.getenv("JWT_SECRET", "secret"), 
            algorithms=["HS256"]
        )
        
        # Verificar role
        if payload.get("role") != "EMPRESA":
            raise HTTPException(
                status_code=403, 
                detail="Acesso negado. Este chat é exclusivo para empresas."
            )
            
        return {
            "user_id": payload.get("sub"),
            "company_id": payload.get("company_id"),
            "email": payload.get("email")
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

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
async def chat(request: ChatRequest, user_data: dict = Depends(validate_company_user)):
    """
    Endpoint principal do chat empresarial
    """
    try:
        logger.info(f"Mensagem recebida da empresa {user_data['company_id']}: {request.message[:50]}...")
        
        # Criar conteúdo da mensagem
        user_content = Content(parts=[Part(text=request.message)])
        
        # Executar agente
        result = await runner.run(
            session_id=request.session_id or f"{user_data['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=user_data['user_id'],
            turns=[user_content]
        )
        
        # Extrair resposta
        response_text = ""
        if result and result.content and result.content.parts:
            response_text = result.content.parts[0].text
            
        logger.info(f"Resposta enviada: {response_text[:100]}...")
        
        return ChatResponse(
            response=response_text,
            session_id=result.session_id
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vacancy/create")
async def create_vacancy_direct(
    vacancy: VacancyCreateRequest,
    user_data: dict = Depends(validate_company_user)
):
    """
    Criar vaga diretamente via formulário (sem usar o chat)
    """
    try:
        # Construir mensagem para o agente processar
        message = f"""Criar uma nova vaga com as seguintes informações:
        Título: {vacancy.title}
        Cargo: {vacancy.position}
        Descrição: {vacancy.description}
        Localização: {vacancy.location}
        Requisitos: {vacancy.requirements or 'Não especificado'}
        Benefícios: {vacancy.benefits or 'Não especificado'}
        Salário: {vacancy.salary_range or 'A combinar'}
        Formato: {vacancy.work_format}
        Tipo de contrato: {vacancy.contract_type}
        Número de vagas: {vacancy.vacancies}
        """
        
        # Processar via agente
        user_content = Content(parts=[Part(text=message)])
        
        result = await runner.run(
            session_id=f"create_vacancy_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=user_data['user_id'],
            turns=[user_content]
        )
        
        # Retornar resultado
        return {
            "status": "success",
            "message": "Vaga criada com sucesso",
            "details": result.content.parts[0].text if result.content.parts else ""
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar vaga: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vacancy/{vacancy_id}/matches")
async def get_vacancy_matches(
    vacancy_id: int,
    min_score: int = 70,
    limit: int = 20,
    user_data: dict = Depends(validate_company_user)
):
    """
    Obter matches de candidatos para uma vaga específica
    """
    try:
        # Construir mensagem para o agente
        message = f"Mostrar candidatos compatíveis para a vaga {vacancy_id} com score mínimo de {min_score}%"
        
        # Processar via agente
        user_content = Content(parts=[Part(text=message)])
        
        result = await runner.run(
            session_id=f"matches_{vacancy_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=user_data['user_id'],
            turns=[user_content]
        )
        
        # Retornar resultado
        return {
            "vacancy_id": vacancy_id,
            "matches": result.content.parts[0].text if result.content.parts else ""
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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