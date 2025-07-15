import os
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai.types import Content, Part
from dotenv import load_dotenv
from nai.agent import root_agent
from .utils.gemini import gemini_extract_text_from_file
from .utils.gemini_update_profile import gemini_enrich_profile
import logging

# Conditional imports for Phoenix observability
PHOENIX_ENABLED = os.getenv('PHOENIX_ENABLED', 'false').lower() == 'true'

if PHOENIX_ENABLED:
    try:
        from nai.phoenix_docker import setup_phoenix_docker
        from nai.log_filters import apply_log_filters
        import nest_asyncio
        # Apply nest_asyncio for ADK compatibility
        nest_asyncio.apply()
    except ImportError:
        PHOENIX_ENABLED = False
        logging.warning("Phoenix dependencies not installed. Running without observability.")

# Configurar logging com mais detalhes
log_level = os.getenv('LOG_LEVEL', 'DEBUG').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.DEBUG),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configurar verbosidade dos loggers
verbose_mode = os.getenv('VERBOSE_LOGS', 'false').lower() == 'true'

if verbose_mode:
    # Modo verbose - mostra todos os logs
    logging.getLogger("google_adk").setLevel(logging.DEBUG)
    logging.getLogger("nai").setLevel(logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.DEBUG)
    logger.info("🔍 Modo VERBOSE ativado - todos os logs serão exibidos")
else:
    # Modo normal - reduz verbosidade
    logging.getLogger("google_adk.google.adk.models.google_llm").setLevel(logging.WARNING)
    logging.getLogger("google_adk").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

# Reduzir verbosidade do OpenTelemetry apenas se Phoenix estiver habilitado
if PHOENIX_ENABLED:
    logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)  # Silencia erros de contexto
    logging.getLogger("opentelemetry.sdk.trace.export").setLevel(logging.WARNING)
    logging.getLogger("openinference.instrumentation.google_adk").setLevel(logging.WARNING)

load_dotenv()

# Setup Phoenix telemetry if enabled
if PHOENIX_ENABLED:
    # Apply custom log filters
    apply_log_filters()
    
    # Setup Phoenix telemetry before creating FastAPI app
    # Now with async context fixes!
    try:
        setup_phoenix_docker()
        logger.info("Phoenix telemetry is active - view traces at http://localhost:6006")
    except Exception as e:
        logger.warning(f"Phoenix telemetry setup failed (non-critical): {e}")
        logger.warning("The application will continue without telemetry")
else:
    logger.info("Phoenix telemetry is disabled")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para log de requisições (apenas em modo verbose)
if verbose_mode:
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        import time
        start_time = time.time()
        
        # Log da requisição
        logger.info(f"📥 Request: {request.method} {request.url}")
        logger.debug(f"   Headers: {dict(request.headers)}")
        
        # Processa a requisição
        response = await call_next(request)
        
        # Log da resposta
        process_time = time.time() - start_time
        logger.info(f"📤 Response: {response.status_code} - {process_time:.3f}s")
        
        return response

db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

session_service = DatabaseSessionService(db_url=db_url)

runner = Runner(
    agent=root_agent,
    app_name="nai_app",
    session_service=session_service
)

def is_text_mime(mime_type: str) -> bool:
    return mime_type in [
        "text/plain",
        "application/json",
        "application/xml",
        "application/x-www-form-urlencoded"
    ]

def describe_file_type(mime_type: str) -> str:
    if mime_type == "application/pdf":
        return "um arquivo PDF"
    if mime_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    ):
        return "um documento do Word"
    if mime_type in (
        "audio/x-aac", "audio/flac", "audio/mp3", "audio/m4a", "audio/mpeg", "audio/mpga",
        "audio/mp4", "audio/opus", "audio/pcm", "audio/wav", "audio/webm"
    ):
        return "um áudio"
    if mime_type in (
        "video/x-flv", "video/quicktime", "video/mpeg", "video/mpegs", "video/mpg",
        "video/mp4", "video/webm", "video/wmv", "video/3gpp"
    ):
        return "um vídeo"
    if mime_type in ("image/png", "image/jpeg", "image/webp"):
        return "uma imagem"
    if mime_type == "text/plain":
        return "um texto"
    return f"um arquivo ({mime_type})"


@app.post("/run")
async def run_agent(request: Request):
    logger.debug("=== INICIANDO REQUISIÇÃO /run ===")
    logger.debug(f"Headers: {dict(request.headers)}")
    content_type = request.headers.get("content-type", "")
    logger.debug(f"Content-Type: {content_type}")
    logger.debug(f"Origin: {request.headers.get('origin', 'N/A')}")
    logger.debug(f"Referer: {request.headers.get('referer', 'N/A')}")

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        user_id = form.get("user_id", "default_user")
        session_id = form.get("session_id", "default_session")
        message_text = form.get("message", "")
        file: UploadFile = form.get("file")

        if file:
            contents = await file.read()
            mime_type = file.content_type
            logger.info("----- Iniciando processamento de arquivo -----")
            logger.info(f"Tipo MIME: {mime_type}")
            logger.info(f"Tamanho: {len(contents)} bytes ({len(contents)/1024:.2f} KB / {len(contents)/1024/1024:.2f} MB)")
            logger.info(f"Nome: {file.filename}")
            
            # Logs específicos para áudio
            if mime_type.startswith("audio/"):
                logger.info(f"🎵 ARQUIVO DE ÁUDIO DETECTADO")
                logger.info(f"Formato de áudio: {mime_type}")
                logger.info(f"Extensão esperada: {file.filename.split('.')[-1] if '.' in file.filename else 'sem extensão'}")
                
                # Verificar primeiros bytes para identificar formato real
                if len(contents) >= 4:
                    header = contents[:4]
                    logger.debug(f"Primeiros 4 bytes (hex): {header.hex()}")
                    
                    # Identificar formato pelo header
                    if header[:3] == b'ID3':
                        logger.info("Header indica: MP3 com tags ID3")
                    elif header == b'fLaC':
                        logger.info("Header indica: FLAC")
                    elif header[:4] == b'OggS':
                        logger.info("Header indica: OGG")
                    elif header[:2] == b'\xff\xfb' or header[:2] == b'\xff\xfa':
                        logger.info("Header indica: MP3 sem tags")
                    elif contents[4:8] == b'ftyp':
                        logger.info("Header indica: MP4/M4A")
                    else:
                        logger.info(f"Header desconhecido: {header}")
            
            logger.info("----- Chamando gemini_extract_text_from_file -----")

            if is_text_mime(mime_type):
                part = Part.from_bytes(data=contents, mime_type=mime_type)
                message = Content(role="user", parts=[part])
            else:
                resumo = gemini_extract_text_from_file(contents, mime_type)
                tipo_arquivo = describe_file_type(mime_type)
                resumo_formatado = (
                    f"O usuário enviou {tipo_arquivo} com o seguinte conteúdo:\n\n{resumo}"
                )
                part = Part(text=resumo_formatado)
                message = Content(role="user", parts=[part])

            logger.info("----- Fim do processamento de arquivo -----")
        elif message_text:
            part = Part(text=message_text)
            message = Content(role="user", parts=[part])
        else:
            return {"response": "Envie uma mensagem ou um arquivo."}
    else:
        data = await request.json()
        logger.debug(f"JSON recebido: {data}")
        user_id = data.get("user_id", "default_user")
        session_id = data.get("session_id", "default_session")
        message_text = data.get("message", "")
        logger.debug(f"User ID: {user_id}, Session ID: {session_id}, Message: {message_text}")
        logger.debug(f"Message length: {len(message_text)}")
        logger.debug(f"Message repr: {repr(message_text)}")  # Mostra caracteres especiais
        logger.debug(f"Session ID length: {len(session_id)}")
        message = Content(role="user", parts=[Part(text=message_text)])

    logger.debug("Verificando sessão...")
    logger.debug(f"Buscando sessão para app_name='nai_app', user_id='{user_id}', session_id='{session_id}'")
    session = await session_service.get_session(app_name="nai_app", user_id=user_id, session_id=session_id)
    if session is None:
        logger.debug("Criando nova sessão...")
        await session_service.create_session(app_name="nai_app", user_id=user_id, session_id=session_id)

    logger.debug("Executando runner.run_async...")
    logger.debug(f"Message content sendo enviado: {message}")
    
    # Verificar estado da sessão antes de processar
    if session:
        logger.debug(f"Session state antes de processar: {getattr(session, 'state', 'N/A')}")
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message
    ):
        logger.debug(f"Evento recebido: {type(event).__name__}")
        
        # Log de eventos específicos
        if hasattr(event, 'content'):
            logger.debug(f"Event content: {getattr(event, 'content', 'N/A')}")
        
        if event.is_final_response():
            logger.debug(f"Final response event: {event}")
            if event.content and getattr(event.content, 'parts', None) and len(event.content.parts) > 0:
                response_text = event.content.parts[0].text
                logger.debug(f"Resposta final completa: {response_text}")
                logger.debug(f"Resposta final (primeiros 200 chars): {response_text[:200]}...")
                return {"response": response_text}
            else:
                logger.error(f"Resposta final sem conteúdo válido: {event}")
                return {"response": "Ocorreu um erro interno ao processar sua solicitação. Por favor, tente novamente ou entre em contato com o suporte."}

    return {"response": "Ocorreu um problema ao processar a resposta."}

@app.post("/enrich-profile")
async def enrich_profile(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        return {"error": "user_id é obrigatório"}

    try:
        updated_profile = gemini_enrich_profile(user_id)
        return {"updated_profile": updated_profile}
    except Exception as e:
        return {"error": str(e)}
