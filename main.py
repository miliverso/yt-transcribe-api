from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import os

app = FastAPI()

class VideoRequest(BaseModel):
    url: str

def descargar_audio(url_video):
    # Definimos las opciones incluyendo el user_agent para evitar detecciones básicas de bot
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url_video, download=True)
        filename = f"/tmp/{info['id']}.mp3"
    return filename

@app.post("/transcribir")
async def transcribir(request: VideoRequest):
    try:
        # Aquí llamarías a tu lógica de faster-whisper después de descargar
        archivo_audio = descargar_audio(request.url)
        
        # PROCESAMIENTO DE TRANSCRIPCIÓN AQUÍ
        # ... (aquí iría tu llamada a la librería de transcripción)
        
        return {"status": "success", "file": archivo_audio}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
