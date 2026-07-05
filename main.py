import os
import uuid
import shutil
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel, HttpUrl
import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yt-audio-api")

app = FastAPI(title="YouTube Audio Downloader", version="1.0.0")

BASE_DOWNLOAD_DIR = Path("/app/downloads")
BASE_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


class DownloadRequest(BaseModel):
    url: HttpUrl


def cleanup(path: str):
    try:
        folder = os.path.dirname(path)
        if os.path.isdir(folder):
            shutil.rmtree(folder, ignore_errors=True)
            logger.info(f"Carpeta temporal eliminada: {folder}")
    except Exception as e:
        logger.warning(f"No se pudo limpiar {path}: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/download-audio")
def download_audio(payload: DownloadRequest):
    video_url = str(payload.url)

    job_id = str(uuid.uuid4())
    job_dir = BASE_DOWNLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(job_dir / "audio")

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "64",
        }],
        "postprocessor_args": ["-ar", "16000", "-ac", "1"],
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
    }

    logger.info(f"Descargando audio de: {video_url}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            title = info.get("title", "audio")
    except Exception as e:
        shutil.rmtree(job_dir, ignore_errors=True)
        logger.error(f"Error descargando: {e}")
        raise HTTPException(status_code=400, detail=f"No se pudo descargar el audio: {e}")

    mp3_path = job_dir / "audio.mp3"

    if not mp3_path.exists():
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail="El archivo de audio no se genero correctamente.")

    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip()[:80]
    filename = f"{safe_title or 'audio'}.mp3"

    return FileResponse(
        path=str(mp3_path),
        media_type="audio/mpeg",
        filename=filename,
        background=BackgroundTask(cleanup, str(mp3_path)),
    )
