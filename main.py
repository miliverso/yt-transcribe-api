from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import os
import random

app = FastAPI()

# Lista de proxies gratuitos para rotar y evitar bloqueos por IP
# Nota: Si fallan, puedes buscar "free proxy list" y actualizar esta lista
PROXIES = [
    "http://190.61.88.147:8080",
    "http://103.152.112.186:80",
    "http://185.162.228.187:80",
]

class VideoRequest(BaseModel):
    url: str

def descargar_audio(url_video):
    # Seleccionamos un proxy aleatorio para cada petición
    proxy_seleccionado = random.choice(PROXIES)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        # Configuración para simular comportamiento humano
        'proxy': proxy_seleccionado,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/',
        },
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_video, download=True)
            filename = f"/tmp/{info['id']}.mp3"
        return filename
    except Exception as e:
        # Si falla, relanzamos el error para que FastAPI lo capture
        raise Exception(f"Error descargando con proxy {proxy_seleccionado}: {str(e)}")

@app.post("/transcribir")
async def transcribir(request: VideoRequest):
    try:
        archivo_audio = descargar_audio(request.url)
        
        # AQUÍ: Agregarás tu lógica de transcripción con faster-whisper
        # ...
        
        return {"status": "success", "file": archivo_audio}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Puerto necesario para Google Cloud Run
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
