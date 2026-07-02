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
    # Configuración de Cookies
    cookies_content = os.getenv("YT_COOKIES_CONTENT")
    cookie_path = "/tmp/cookies.txt"
    if cookies_content:
        with open(cookie_path, "w") as f:
            f.write(cookies_content)
    
    # Headers basados en tu script de Colab
    final_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Referer': 'https://www.youtube.com/',
        'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    if user_headers:
        final_headers.update(user_headers)

    # Opciones probadas y funcionales
    opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path, # Esto guardará como /tmp/ID.mp3
        'quiet': False,
        'no_warnings': False,
        'noplaylist': True,
        'http_headers': final_headers,
    }
    
    if os.path.exists(cookie_path):
        opts['cookiefile'] = cookie_path
        
    proxy_key = os.getenv("SCRAPERAPI_KEY")
    if proxy_key:
        opts['proxy'] = f"http://scraperapi:{proxy_key}@proxy-server.scraperapi.com:8001/?render=true"
        
    return opts

def transcribir_video(url_video, user_headers=None):
    output_filename = '/tmp/audio_temp.mp3'
    ydl_opts = get_ydl_opts('/tmp/audio_temp', user_headers)

    # 1. Descarga
    try:
        logger.info(f"Iniciando descarga con yt-dlp: {url_video}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url_video])
    except Exception as e:
        logger.error(f"Error en descarga: {str(e)}")
        raise Exception(f"Fallo en descarga: {str(e)}")

    # 2. Transcripción (Optimizada para CPU en Cloud Run)
    try:
        logger.info("Cargando Whisper (CPU mode)...")
        # Cambiamos a device="cpu" y compute_type="int8" para que no pete en Cloud Run
        model = WhisperModel("small", device="cpu", compute_type="int8") 
        
        logger.info("Transcribiendo...")
        segments, info = model.transcribe(output_filename, beam_size=5, language="es")
        
        texto_completo = []
        for segment in segments:
            texto_completo.append(segment.text)
        
        # Limpieza
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
