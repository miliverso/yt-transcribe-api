from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import os
import random

app = FastAPI()

class VideoRequest(BaseModel):
    url: str

def obtener_proxy_valido():
    # Importación diferida para no bloquear el inicio del contenedor
    from free_proxy_list import get_proxy_list
    try:
        proxies = get_proxy_list()
        # Filtramos proxies HTTP para mayor compatibilidad
        http_proxies = [f"http://{p['ip']}:{p['port']}" for p in proxies if p['type'] == 'http']
        return random.choice(http_proxies) if http_proxies else None
    except Exception:
        return None

def descargar_audio(url_video):
    proxy = obtener_proxy_valido()
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'proxy': proxy,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_video, download=True)
            return f"/tmp/{info['id']}.mp3"
    except Exception as e:
        raise Exception(f"Fallo en descarga con proxy {proxy}: {str(e)}")

@app.post("/transcribir")
async def transcribir(request: VideoRequest):
    try:
        archivo_audio = descargar_audio(request.url)
        # Aquí llamarás a faster-whisper en el siguiente paso
        return {"status": "success", "file": archivo_audio}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
