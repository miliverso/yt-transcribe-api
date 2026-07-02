import os
import logging
import yt_dlp
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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
        logger.info("Archivo de cookies creado correctamente.")
    
    # Headers por defecto
    final_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Referer': 'https://www.youtube.com/',
        'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    if user_headers:
        final_headers.update(user_headers)
        logger.info(f"Headers personalizados aplicados: {user_headers}")

    opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False,
        'noplaylist': True,
        'http_headers': final_headers,
    }
    
    if os.path.exists(cookie_path):
        opts['cookiefile'] = cookie_path
        
    # Configuración de Proxy (ScraperAPI)
    proxy_key = os.getenv("SCRAPERAPI_KEY")
    if proxy_key:
        opts['proxy'] = f"http://scraperapi:{proxy_key}@proxy-server.scraperapi.com:8001"
        logger.info("Proxy configurado exitosamente mediante ScraperAPI.")
        
    return opts

def descargar_audio(url_video, user_headers=None):
    output_template = '/tmp/%(id)s.%(ext)s'
    ydl_opts = get_ydl_opts(output_template, user_headers)

    try:
        logger.info(f"Iniciando descarga de: {url_video}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_video, download=True)
            return f"/tmp/{info['id']}.mp3"
    except Exception as e:
        logger.error(f"Error crítico en yt-dlp: {str(e)}")
        raise Exception(f"Fallo en descarga: {str(e)}")

@app.post("/transcribir")
async def transcribir(request: VideoRequest):
    try:
        archivo_audio = descargar_audio(request.url, request.custom_headers)
        return {"status": "success", "file": archivo_audio}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
