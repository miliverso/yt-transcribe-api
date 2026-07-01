from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import os

app = FastAPI()

class VideoRequest(BaseModel):
    url: str

def descargar_audio(url_video):
    # Configuramos el User-Agent y los Headers para simular un navegador real
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        # Aquí inyectamos la identidad de navegador
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/',
        },
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Intentamos extraer la información del video
        info = ydl.extract_info(url_video, download=True)
        filename = f"/tmp/{info['id']}.mp3"
        
    return filename

@app.post("/transcribir")
async def transcribir(request: VideoRequest):
    try:
        archivo_audio = descargar_audio(request.url)
        
        # Aquí iría tu lógica de faster-whisper después de confirmar que la descarga funciona
        # ...
        
        return {"status": "success", "file": archivo_audio}
    
    except Exception as e:
        # Si sigue fallando, este error te dará la pista final
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
