import os
import logging
import yt_dlp
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from faster_whisper import WhisperModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


class VideoRequest(BaseModel):
    url: str
    custom_headers: Optional[Dict[str, str]] = None


def get_ydl_opts(output_path, user_headers=None):
    # --- Cookies -------------------------------------------------------------
    cookies_content = os.getenv("YT_COOKIES_CONTENT")
    cookie_path = "/tmp/cookies.txt"

    if cookies_content:
        with open(cookie_path, "w") as f:
            f.write(cookies_content)
        # Validate: length + Netscape header so we KNOW it is usable
        logger.info(f"DEBUG: cookies length = {len(cookies_content)} chars")
        if "# Netscape HTTP Cookie File" not in cookies_content \
           and "# HTTP Cookie File" not in cookies_content:
            logger.warning(
                "Cookies do NOT look like Netscape format. yt-dlp will ignore "
                "them. Re-export using a 'Get cookies.txt' extension."
            )
        else:
            logger.info("Cookie file created (Netscape format OK).")
    else:
        logger.warning("DEBUG: YT_COOKIES_CONTENT is EMPTY / not set.")

    # --- Proxy ---------------------------------------------------------------
    proxy_key = os.getenv("SCRAPERAPI_KEY")
    logger.info(f"DEBUG: SCRAPERAPI_KEY present: {'YES' if proxy_key else 'NO'}")

    # --- Headers -------------------------------------------------------------
    final_headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/126.0.0.0 Safari/537.36'),
        'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    if user_headers:
        final_headers.update(user_headers)

    opts = {
        # audio only: never download the full video through a metered proxy
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
        # helps against bot detection without needing browser rendering
        'extractor_args': {'youtube': {'player_client': ['android']}},
    }

    if os.path.exists(cookie_path):
        opts['cookiefile'] = cookie_path

    if proxy_key:
        # CORRECT proxy URL: scheme://user:pass@host:port  (NO path, NO query).
        # The old "/?render=true" was invalid and silently bypassed the proxy.
        # render is NOT wanted for yt-dlp media downloads anyway.
        opts['proxy'] = (
            f"http://scraperapi:{proxy_key}@proxy-server.scraperapi.com:8001"
        )
        logger.info("Proxy configured (plain mode, no render).")

    return opts


def transcribir_video(url_video, user_headers=None):
    output_filename = '/tmp/audio_temp.mp3'
    ydl_opts = get_ydl_opts('/tmp/audio_temp', user_headers)

    # 1. Download
    try:
        logger.info(f"Starting download: {url_video}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url_video])
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise Exception(f"Download failed: {str(e)}")

    # 2. Transcription
    try:
        logger.info("Loading Whisper (CPU mode)...")
        model = WhisperModel("small", device="cpu", compute_type="int8")
        logger.info("Transcribing...")
        segments, info = model.transcribe(output_filename, beam_size=5, language="es")

        texto_completo = [segment.text for segment in segments]

        if os.path.exists(output_filename):
            os.remove(output_filename)

        return " ".join(texto_completo)
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise Exception(f"Transcription failed: {str(e)}")


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
