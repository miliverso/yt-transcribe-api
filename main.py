import os
import logging
import yt_dlp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configurar logging para ver qué pasa en los logs de Cloud Run
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class VideoRequest(BaseModel):
    url: str

def get_ydl_opts(output_path):
    # La variable que viene del Secret Manager
    cookies_content = os.getenv("YT_COOKIES_CONTENT")
    cookie_path = "/tmp/cookies.txt"
    
    # Intentar escribir el archivo de cookies si la variable existe
    if cookies_content:
        try:
            with open(cookie_path, "w") as f:
                f.write(cookies_content)
            logger.info(f"Éxito: Archivo de cookies creado en {cookie_path}. Tamaño: {len(cookies_content)} bytes")
        except Exception as e:
            logger.error(f"Error escribiendo el archivo de cookies: {str(e)}")
    else:
        logger.warning("Advertencia: No se encontró la variable YT_COOKIES_CONTENT. Se intentará descargar sin cookies.")

    opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
        'quiet': False, # Cambiado a False para ver errores detallados en los logs
        'no_warnings': False,
        'noplaylist': True,
        # Un User-Agent más realista puede ayudar a evitar el bloqueo
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        },
    }
    
    # Solo añadimos el archivo de cookies si existe realmente
    if os.path.exists(cookie_path):
        opts['cookiefile'] = cookie_path
        logger.info("Configuración: yt-dlp está usando el archivo de cookies.")
    else:
        logger.info("Configuración: yt-dlp NO está usando archivo de cookies.")
        
    return opts

def descargar_audio(url_video):
    output_template = '/tmp/%(id)s.%(ext)s'
    ydl_opts = get_ydl_opts(output_template)

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
        archivo_audio = descargar_audio(request.url)
        return {"status": "success", "file": archivo_audio}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
