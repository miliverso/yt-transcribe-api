import os
import logging
import yt_dlp
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from faster_whisper import WhisperModel

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class VideoRequest(BaseModel):
    url: str
    custom_headers: Optional[Dict[str, str]] = None

def get_ydl_opts(output_path, user_headers=None):
    # Gestión de Cookies
    cookies_content = os.getenv("YT_COOKIES_CONTENT")
    cookie_path = "/tmp/cookies.txt"
    
    if cookies_content:
        with open(cookie_path, "w") as f:
            f.write(cookies_content)
        logger.info("Archivo de cookies creado.")
    
    # Debug: Verificar si la clave del proxy existe
    proxy_key = os.getenv("SCRAPERAPI_KEY")
    key_exists = "YES" if proxy_key else "NO"
    logger.info(f"DEBUG: SCRAPERAPI_KEY encontrada en entorno: {key_exists}")

    final_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Referer': 'https://www.youtube.com/',
        'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    if user_headers:
        final_headers.update(user_headers)

    opts = {
        'format': 'best/bestaudio',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False,
        'noplaylist': True,
        'http_headers': final_headers,
    }
    
    if os.path.exists(cookie_path):
        opts['cookiefile'] = cookie_path
        
    if proxy_key:
        # Usamos render=true para asegurar que ScraperAPI simule un navegador humano
        opts['proxy'] = f"http://scraperapi:{proxy_key}@proxy-server.scraperapi.com:8001/?render=true"
        logger.info("Proxy con renderizado configurado.")
        
    return opts

def transcribir_video(url_video, user_headers=None):
    output_filename = '/tmp/audio_temp.mp3'
    ydl_opts = get_ydl_opts('/tmp/audio_temp', user_headers)

    # 1. Descarga
    try:
        logger.info(f"Iniciando descarga: {url_video}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url_video])
    except Exception as e:
        logger.error(f"Error en descarga: {str(e)}")
        raise Exception(f"Fallo en descarga: {str(e)}")

    # 2. Transcripción
    try:
        logger.info("Cargando Whisper (CPU mode)...")
        model = WhisperModel("small", device="cpu", compute_type="int8") 
        logger.info("Transcribiendo...")
        segments, info = model.transcribe(output_filename, beam_size=5, language="es")
        
        texto_completo = [segment.text for segment in segments]
        
        if os.path.exists(output_filename):
            os.remove(output_filename)
            
        return " ".join(texto_completo)
    except Exception as e:
        logger.error(f"Error en transcripción: {str(e)}")
        raise Exception(f"Fallo en transcripción: {str(e)}")

@app.post("/transcribir")
async def transcribir(request: VideoRequest):
    try:
        resultado = transcribir_video(request.url, request.custom_headers)
        return {"status": "success", "transcription": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
