import logging
from app.ai.voice.events.event import Event

logger = logging.getLogger("logging_handler")

class LoggingHandler:
    def __init__(self):
        pass

    def handle_event(self, event: Event) -> None:
        """Logs event metrics and metadata for debugging and performance auditing."""
        payload_keys = list(event.payload.keys())
        metadata_keys = list(event.metadata.keys())
        
        logger.info(
            "logging_handler | event_received | type: %s | session_id: %s | timestamp: %s | payload_keys: %s | metadata: %s",
            event.type.name,
            event.session_id,
            event.timestamp.isoformat(),
            payload_keys,
            event.metadata,
        )
