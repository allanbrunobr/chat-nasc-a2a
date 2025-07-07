import os
import tempfile
import time
import logging
from google import genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

def get_extension_from_mime(mime_type: str) -> str:
    mapping = {
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        # Áudio - mapeamento completo
        "audio/x-aac": ".aac",
        "audio/aac": ".aac",
        "audio/flac": ".flac",
        "audio/mp3": ".mp3",
        "audio/m4a": ".m4a",
        "audio/x-m4a": ".m4a",
        "audio/mpeg": ".mp3",
        "audio/mpga": ".mp3",
        "audio/mp4": ".mp4",
        "audio/opus": ".opus",
        "audio/ogg": ".ogg",
        "audio/pcm": ".pcm",
        "audio/wav": ".wav",
        "audio/wave": ".wav",
        "audio/x-wav": ".wav",
        "audio/webm": ".webm",
        # Formatos adicionais de áudio
        "audio/x-mpeg": ".mp3",
        "audio/x-mp3": ".mp3",
        "audio/mpeg3": ".mp3",
        "audio/x-mpeg-3": ".mp3",
        # Vídeo
        "video/x-flv": ".flv",
        "video/quicktime": ".mov",
        "video/mpeg": ".mpeg",
        "video/mpegs": ".mpeg",
        "video/mpg": ".mpg",
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "video/wmv": ".wmv",
        "video/3gpp": ".3gp",
        # Imagem
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        # Texto
        "text/plain": ".txt",
        "application/json": ".json",
        "application/xml": ".xml",
        "application/x-www-form-urlencoded": ".txt"
    }
    
    # Log do mapeamento
    result = mapping.get(mime_type, "")
    if not result and mime_type:
        logger.warning(f"⚠️ Tipo MIME não mapeado: {mime_type}")
    
    return result

def gemini_extract_text_from_file(file_bytes: bytes, mime_type: str, prompt: str = None) -> str:
    """
    Recebe um arquivo em bytes, faz upload no Gemini e retorna o texto transcrito ou sumarizado.
    """
    logger.info("=== INÍCIO gemini_extract_text_from_file ===")
    logger.info(f"Tipo MIME recebido: {mime_type}")
    logger.info(f"Tamanho do arquivo: {len(file_bytes)} bytes ({len(file_bytes)/1024:.2f} KB)")
    
    # Formatos de áudio problemáticos
    problematic_audio_formats = ["audio/webm"]
    
    if mime_type in problematic_audio_formats:
        logger.warning(f"⚠️ Formato {mime_type} não suportado")
        logger.info("=== FIM gemini_extract_text_from_file (formato não suportado) ===")
        return (
            f"Desculpe, o formato {mime_type} não é suportado no momento. "
            "Por favor, tente gravar o áudio novamente (o navegador tentará usar um formato diferente) "
            "ou digite o conteúdo em texto."
        )
    
    extension = get_extension_from_mime(mime_type)
    logger.info(f"Extensão mapeada: {extension}")
    
    # Criar arquivo temporário
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
            logger.info(f"Arquivo temporário criado: {tmp_path}")

        logger.info(f"Iniciando upload para Gemini API...")
        logger.info(f"Arquivo: {tmp_path} ({mime_type}, {len(file_bytes)} bytes)")
        
        # Log dos formatos de áudio suportados
        if mime_type.startswith("audio/"):
            supported_audio = ["audio/mp3", "audio/mpeg", "audio/mp4", "audio/m4a", "audio/wav", 
                             "audio/flac", "audio/opus", "audio/aac", "audio/x-aac"]
            if mime_type in supported_audio:
                logger.info(f"✅ Formato de áudio suportado: {mime_type}")
            else:
                logger.warning(f"⚠️ Formato de áudio pode não ser suportado: {mime_type}")
                logger.info(f"Formatos suportados: {', '.join(supported_audio)}")
        
        # Upload do arquivo
        try:
            gemini_file = client.files.upload(file=tmp_path)
            logger.info(f"Upload concluído. Nome do arquivo no Gemini: {gemini_file.name}")
        except Exception as upload_error:
            logger.error(f"❌ Erro no upload: {type(upload_error).__name__}: {upload_error}")
            return (
                "Desculpe, ocorreu um erro ao fazer upload do arquivo. "
                "Por favor, tente novamente ou envie o conteúdo em texto."
            )
        
        # Aguardar processamento
        logger.info("Aguardando processamento do arquivo...")
        if mime_type.startswith("audio/") or mime_type.startswith("video/"):
            wait_time = 10
            logger.info(f"Arquivo de mídia detectado, aguardando {wait_time} segundos...")
        else:
            wait_time = 5
        time.sleep(wait_time)
        
        # Verificar estado do arquivo antes de processar
        try:
            logger.info("Verificando estado do arquivo antes de processar...")
            max_attempts = 3
            for attempt in range(max_attempts):
                file_info = client.files.get(name=gemini_file.name)
                if hasattr(file_info, 'state'):
                    state_name = getattr(file_info.state, 'name', 'UNKNOWN')
                    logger.info(f"Tentativa {attempt + 1}: Estado do arquivo: {state_name}")
                    if state_name == "ACTIVE":
                        break
                    elif state_name == "FAILED":
                        logger.error(f"❌ Upload do arquivo falhou no servidor Gemini")
                        return "Desculpe, o upload do arquivo falhou. Por favor, tente novamente."
                
                if attempt < max_attempts - 1:
                    time.sleep(5)
        except Exception as e:
            logger.warning(f"Não foi possível verificar estado do arquivo: {e}")
        
        # Tentar processar com Gemini
        default_prompt = (
            "Transcreva na íntegra todo o conteúdo deste arquivo de forma organizada, "
            "incluindo texto, tópicos principais e, se for áudio/vídeo, transcreva todas as falas."
        )
        effective_prompt = prompt or default_prompt

        logger.info("Enviando arquivo para processamento com Gemini...")
        logger.info(f"Modelo: gemini-2.0-flash-001")
        # logger.info(f"Prompt: {effective_prompt[:100]}...")
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=[effective_prompt, gemini_file],
                config=genai.types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2048
                )
            )
            result = response.text.strip()
            logger.info(f"✅ Processamento concluído com sucesso!")
            logger.info(f"Tamanho da resposta: {len(result)} caracteres")
            logger.info(f"Primeiros 200 caracteres da transcrição: {result[:200]}...")
            logger.info("=== FIM gemini_extract_text_from_file ===")
            return result
        except Exception as process_error:
            logger.error(f"❌ Erro ao processar com Gemini: {type(process_error).__name__}: {process_error}")
            if "not in an ACTIVE state" in str(process_error):
                return (
                    "Desculpe, o arquivo de áudio não pôde ser processado. "
                    "Por favor, tente gravar novamente ou digite o conteúdo em texto."
                )
            raise
        
    except Exception as e:
        logger.error(f"❌ ERRO ao processar arquivo com Gemini: {type(e).__name__}: {e}")
        logger.error(f"Detalhes do erro: {str(e)}")
        logger.info("=== FIM gemini_extract_text_from_file (com erro) ===")
        # Retornar uma mensagem de erro amigável
        return (
            f"Desculpe, não foi possível processar o arquivo {mime_type}. "
            f"Por favor, tente enviar em outro formato ou digite o conteúdo em texto."
        )
    finally:
        # Garantir que o arquivo temporário seja removido
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.info(f"Arquivo temporário removido: {tmp_path}")
            except Exception as e:
                logger.warning(f"Erro ao remover arquivo temporário: {e}")
