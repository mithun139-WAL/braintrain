"""
GroqTranscriptionProvider — whisper-large-v3 via Groq's OpenAI-compatible API.

Groq runs Whisper on custom LPU hardware, making it significantly faster than
OpenAI's Whisper-1 endpoint and currently free-tier friendly.

Design:
  - Identical contract to OpenAITranscriptionProvider (same protocol)
  - Downloads audio buffer from the provided URL (works with S3 presigned URLs)
  - Uses the openai SDK pointed at Groq's base_url — no extra SDK required
  - Uses asyncio.to_thread for the sync Whisper SDK call
  - Returns empty TranscriptionResult on failure (never raises) — evaluation
    continues with the candidate's typed answer_text if available
  - estimated_cost_usd is set to 0.0 (Groq does not charge per-second for Whisper)

Supported Groq Whisper models:
  whisper-large-v3         — highest accuracy (recommended default)
  whisper-large-v3-turbo   — faster, slightly lower accuracy

Audio limits: 25 MB max file size, same as OpenAI Whisper.
"""
import asyncio
import io
import logging
from pathlib import PurePosixPath
from typing import Optional
from urllib.parse import urlparse

import httpx

from app.ai.protocols import TranscriptionResult

logger = logging.getLogger(__name__)

# Groq Whisper does not charge per second — cost is effectively 0
GROQ_WHISPER_COST_USD = 0.0

MAX_AUDIO_BYTES = 25 * 1024 * 1024   # 25 MB

EXTENSION_TO_MIME: dict[str, str] = {
    "mp3":  "audio/mpeg",
    "mp4":  "audio/mp4",
    "m4a":  "audio/mp4",
    "wav":  "audio/wav",
    "webm": "audio/webm",
    "ogg":  "audio/ogg",
    "flac": "audio/flac",
    "mpeg": "audio/mpeg",
    "mpga": "audio/mpeg",
}


class GroqTranscriptionProvider:
    """
    whisper-large-v3 transcription provider via Groq's LPU-accelerated endpoint.
    Implements the AudioTranscriptionProvider protocol.
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        import openai
        # Groq is OpenAI-compatible — same SDK, different base_url + key
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def transcribe(self, audio_url: str) -> TranscriptionResult:
        try:
            audio_bytes, filename, mime_type = await self._fetch_audio(audio_url)

            if len(audio_bytes) > MAX_AUDIO_BYTES:
                size_mb = len(audio_bytes) / 1024 / 1024
                logger.warning(
                    "Audio at %s exceeds 25MB (%.1fMB) — skipping Groq transcription",
                    audio_url,
                    size_mb,
                )
                return self._empty_result(f"{self._model}-skipped-too-large")

            result = await asyncio.to_thread(
                self._call_whisper, audio_bytes, filename, mime_type
            )
            return result

        except Exception as exc:
            logger.error("Groq transcription failed for %s: %s", audio_url, exc)
            return self._empty_result(f"{self._model}-error")

    def _call_whisper(
        self, audio_bytes: bytes, filename: str, mime_type: str
    ) -> TranscriptionResult:
        audio_file = (filename, io.BytesIO(audio_bytes), mime_type)

        response = self._client.audio.transcriptions.create(
            model=self._model,
            file=audio_file,
            response_format="verbose_json",
        )

        text = getattr(response, "text", "") or ""
        duration_seconds: Optional[float] = getattr(response, "duration", None)

        logger.info(
            "Groq transcribed | model=%s | duration=%.1fs | words=%d",
            self._model,
            duration_seconds or 0,
            len(text.split()),
        )

        return TranscriptionResult(
            text=text,
            duration_seconds=duration_seconds,
            model_used=self._model,
            is_stub=False,
            estimated_cost_usd=GROQ_WHISPER_COST_USD,
        )

    async def _fetch_audio(self, audio_url: str) -> tuple[bytes, str, str]:
        """Download audio from a URL and return (bytes, filename, mime_type)."""
        parsed = urlparse(audio_url)
        raw_path = parsed.path.split("?")[0]
        basename = PurePosixPath(raw_path).name
        ext = PurePosixPath(basename).suffix.lstrip(".").lower()
        mime_type = EXTENSION_TO_MIME.get(ext, "audio/mpeg")
        filename = basename or f"audio.{ext or 'mp3'}"

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(audio_url)
            response.raise_for_status()
            return response.content, filename, mime_type

    def _empty_result(self, model_used: str) -> TranscriptionResult:
        return TranscriptionResult(
            text="",
            duration_seconds=None,
            model_used=model_used,
            is_stub=False,
            estimated_cost_usd=None,
        )
