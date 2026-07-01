# yt-transcribe-api

Automated YouTube audio extraction and transcription service built with FastAPI and `faster-whisper`. Designed for serverless deployment on Google Cloud Run as part of the Ailyn AI ecosystem.

## Overview
This service provides an HTTP endpoint to ingest YouTube video URLs, extract audio, and return accurate, timestamped transcriptions using OpenAI's Whisper model (via `faster-whisper` for optimized performance).

## Features
* **Automated Extraction:** Handles video-to-audio conversion using `yt-dlp`.
* **High-Speed Transcription:** Uses `faster-whisper` for efficient inference.
* **Serverless Ready:** Optimized for Google Cloud Run (containerized).
* **Stateless Architecture:** Designed for high-concurrency and cost-effective execution.

## API Usage

### Endpoint: `POST /transcribir`

**Request:**
```json
{
  "url": "[https://www.youtube.com/watch?v=YOUR_VIDEO_ID](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)"
}
Response:

JSON
{
  "transcription": "Here is the full text transcription of the video content..."
}
Tech Stack
Framework: FastAPI

Audio Processing: yt-dlp, ffmpeg

Transcription: faster-whisper

Infrastructure: Docker, Google Cloud Run

Deployment
Connect this repository to Google Cloud Run.

Set the build trigger to use the included Dockerfile.

Configure the service with 1 instance limit for the "Always Free" tier.

