"""
OpenAITranscriptionProvider — Whisper-1 integration via the OpenAI SDK.

Design:
  - Downloads audio buffer from the provided URL (works with S3 presigned URLs)
  - Uses asyncio.to_thread for sync Whisper API call
  - Returns empty string on failure (never raises) — evaluation still runs
    using the candidate's typed answer_text if available
  - Extracts duration from Whisper's verbose_json response for cost tracking
  - Whisper is language-agnostic by default (auto-detects)

Whisper-1 pricing: $0.006 per minute → $0.0001 per second of audio.

Matches NestJS: apps/backend/src/modules/ai/providers/openai-transcription.provider.ts
"""
import asyncio
import logging
import os
from pathlib import PurePosixPath
from typing import Optional
from urllib.parse import urlparse

import httpx

from app.ai.protocols import AudioTranscriptionProvider, TranscriptionResult

logger = logging.getLogger(__name__)

# Whisper-1 pricing
WHISPER_COST_PER_SECOND_USD = 0.0001  # $0.006/min ≈ $0.0001/sec

# Whisper's max file size (25 MB) — reject before attempting API call
MAX_AUDIO_BYTES = 25 * 1024 * 1024

# Supported audio MIME types by Whisper API
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


class OpenAITranscriptionProvider:
    """
    Whisper-1 transcription provider.
    Implements the AudioTranscriptionProvider protocol.
    """

    def __init__(self, api_key: str) -> None:
        import openai
        self._client = openai.OpenAI(api_key=api_key)

    async def transcribe(self, audio_url: str) -> TranscriptionResult:
        try:
            # 1. Download audio bytes async
            audio_bytes, filename, mime_type = await self._fetch_audio(audio_url)

            # 2. Reject oversized files before calling Whisper
            if len(audio_bytes) > MAX_AUDIO_BYTES:
                size_mb = len(audio_bytes) / 1024 / 1024
                logger.warning(
                    "Audio at %s exceeds 25MB (%.1fMB) — skipping transcription",
                    audio_url,
                    size_mb,
                )
                return self._empty_result("whisper-1-skipped-too-large")

            # 3. Call Whisper in a thread (sync SDK)
            result = await asyncio.to_thread(
                self._call_whisper, audio_bytes, filename, mime_type
            )
            return result

        except Exception as exc:
            logger.error("Transcription failed for %s: %s", audio_url, exc)
            # Graceful degradation — evaluation continues with answer_text only
            return self._empty_result("whisper-1-error")

    def _call_whisper(
        self, audio_bytes: bytes, filename: str, mime_type: str
    ) -> TranscriptionResult:
        import io
        from openai import NotGiven

        audio_file = (filename, io.BytesIO(audio_bytes), mime_type)

        response = self._client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
        )

        text = getattr(response, "text", "") or ""
        duration_seconds: Optional[float] = getattr(response, "duration", None)
        estimated_cost = (
            round(duration_seconds * WHISPER_COST_PER_SECOND_USD, 6)
            if duration_seconds is not None
            else None
        )

        logger.info(
            "Transcribed | duration=%.1fs | words=%d | ~$%s",
            duration_seconds or 0,
            len(text.split()),
            f"{estimated_cost:.6f}" if estimated_cost is not None else "?",
        )

        return TranscriptionResult(
            text=text,
            duration_seconds=duration_seconds,
            model_used="whisper-1",
            is_stub=False,
            estimated_cost_usd=estimated_cost,
        )

    async def _fetch_audio(self, audio_url: str) -> tuple[bytes, str, str]:
        """Download audio from a URL and return (bytes, filename, mime_type)."""
        parsed = urlparse(audio_url)
        raw_path = parsed.path.split("?")[0]   # strip query params
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
