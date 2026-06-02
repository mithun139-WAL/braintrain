import logging
from app.ai.voice.events.event import Event

logger = logging.getLogger("transcript_subscriber")

class TranscriptSubscriber:
    def __init__(self):
        pass

    async def on_transcript_received(self, event: Event) -> None:
        """Hook for external/observability transcript notification handling."""
        text = event.payload.get("text", "")
        logger.info("transcript_subscriber | Candidate transcription parsed (length: %d chars)", len(text))
