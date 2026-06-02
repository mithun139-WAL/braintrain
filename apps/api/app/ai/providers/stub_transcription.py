"""
StubTranscriptionProvider — zero-cost fallback for audio transcription.

Used when:
  - OPENAI_API_KEY is not set (offline / dev mode)
  - The real transcription provider fails and the system degrades gracefully

Returns an empty transcription so the downstream evaluation pipeline can
still operate using whatever answer_text the user submitted manually.

Matches NestJS: apps/backend/src/modules/ai/providers/stub-transcription.provider.ts
"""
import logging

from app.ai.protocols import AudioTranscriptionProvider, TranscriptionResult

logger = logging.getLogger(__name__)


class StubTranscriptionProvider:
    """
    Zero-cost fallback — returns empty transcript without any API call.
    Implements the AudioTranscriptionProvider protocol.
    """

    async def transcribe(self, audio_url: str) -> TranscriptionResult:
        logger.debug("[Stub] Skipping transcription for: %s", audio_url)
        return TranscriptionResult(
            text="",
            duration_seconds=None,
            model_used="stub",
            is_stub=True,
            estimated_cost_usd=None,
        )
