import os
import yt_dlp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class VideoRequest(BaseModel):
    url: str

def get_ydl_opts(output_path):
    # Cargar cookies desde variable de entorno (Secret Manager)
    cookies_content = os.getenv("YT_COOKIES_CONTENT")
    cookie_file = "/tmp/cookies.txt"
    
    if cookies_content:
        with open(cookie_file, "w") as f:
            f.write(cookies_content)
    
    opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        },
    }
    
    # Solo añadimos el archivo de cookies si existe
    if os.path.exists(cookie_file):
        opts['cookiefile'] = cookie_file
        
    return opts

def descargar_audio(url_video):
    output_template = '/tmp/%(id)s.%(ext)s'
    ydl_opts = get_ydl_opts(output_template)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_video, download=True)
            return f"/tmp/{info['id']}.mp3"
    except Exception as e:
        raise Exception(f"Error en descarga: {str(e)}")

@app.post("/transcribir")
async def transcribir(request: VideoRequest):
    try:
        archivo_audio = descargar_audio(request.url)
        # Aquí llamarás a faster-whisper más adelante
        return {"status": "success", "file": archivo_audio}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Cloud Run usa el puerto definido en la variable PORT
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
