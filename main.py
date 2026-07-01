from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import os
from faster_whisper import WhisperModel

app = FastAPI()

# Modelo pequeño para que no crashee la RAM gratuita de Render
# Si tienes más RAM, cambia a "small" o "medium"
MODEL_SIZE = "tiny" 
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

class VideoRequest(BaseModel):
    url: str

@app.post("/transcribir")
async def transcribir_video(request: VideoRequest):
    audio_file = "temp_audio.mp3"
    
    # 1. Descargar
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '64'}],
        'outtmpl': 'temp_audio',
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])
        
        # 2. Transcribir
        segments, info = model.transcribe(audio_file, beam_size=1)
        
        full_text = []
        for segment in segments:
            full_text.append(segment.text)
            
        # 3. Limpieza
        if os.path.exists(audio_file):
            os.remove(audio_file)
            
        return {"transcription": " ".join(full_text)}
        
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
