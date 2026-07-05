# YouTube Audio Ingestion API

A fast, lightweight, and *stateless* microservice built with FastAPI, specifically designed to extract and optimize YouTube audio for Speech-to-Text (STT) pipelines and LLM processing.

This module acts as the media ingestion engine, delegating the heavy lifting of transcription to external services in order to maintain a container with a low CPU and RAM footprint.

## 🚀 Key Features (Updated Architecture)

* **AI-Optimized Extraction:** Audio is automatically processed to 16kHz, single-channel (mono), and 64kbps. This is the exact format required by engines like Whisper, saving massive amounts of bandwidth.
* **Safe Concurrency (Stateless):** Utilizes a job isolation system via UUIDs. It allows processing multiple simultaneous downloads without temporary files colliding with each other.
* **Automatic Cleanup (Garbage Collection):** Implements Starlette's `BackgroundTask` to safely and automatically delete audio files from the server immediately after the HTTP response is completed.
* **Optimized Docker:** Built on `python:3.11-slim`, fully leveraging Docker layer caching for fast deployments.
* **YouTube Resilience:** Uses unpinned `yt-dlp`, ensuring the microservice can always fetch the latest patches to bypass updated YouTube restrictions.

## 🛠️ Tech Stack

* **Framework:** FastAPI + Uvicorn (with `uvloop` and `httptools` for maximum concurrent performance).
* **Core:** Python 3.11
* **Media Processing:** yt-dlp + native FFmpeg.

## 📦 Docker Deployment

Build the optimized image:
```bash
docker build -t youtube-audio-api .

Run the container exposing port 8000:

Bash
docker run -d -p 8000:8000 --name yt-ingestion youtube-audio-api
📡 API Endpoints
1. Health Check
Verifies that the container and server are alive.

GET /health

Response:

JSON
{
  "status": "ok"
}
2. Download Audio
Extracts audio from a video and returns it as a physical MP3 file.

POST /download-audio

Body (JSON):

JSON
{
  "url": "[https://www.youtube.com/watch?v=EXAMPLE](https://www.youtube.com/watch?v=EXAMPLE)"
}
Response: audio/mpeg file (direct .mp3 download). The file is instantly deleted from the server after the download finishes.
