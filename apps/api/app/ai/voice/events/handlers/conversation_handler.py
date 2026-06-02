import logging
from app.ai.voice.events.event import Event
from app.ai.voice.events.event_types import EventType
from app.ai.voice.conversation.manager import ConversationManager
from app.ai.voice.audio.livekit_transport import LiveKitTransport

logger = logging.getLogger("conversation_handler")

class ConversationHandler:
    def __init__(self, conversation_manager: ConversationManager, transport: LiveKitTransport):
        self.conversation_manager = conversation_manager
        self.transport = transport

    async def on_transcript_received(self, event: Event) -> None:
        """Handles Candidate speech transcription."""
        text = event.payload.get("text")
        if not text:
            return
        
        # 1. Update session state/memory
        self.conversation_manager.record_user_turn(text, speaker="Candidate")

        # 2. Broadcast transcript to client
        try:
            await self.transport.broadcast_transcript("Candidate", text)
            logger.info("conversation_handler | broadcasted Candidate transcript: %s", text[:80])
        except Exception as exc:
            logger.error("conversation_handler | failed to broadcast Candidate transcript: %s", exc)

    async def on_response_generated(self, event: Event) -> None:
        """Handles Interviewer response generation turns."""
        raw_text = event.payload.get("raw_text")
        clean_text = event.payload.get("clean_text")
        speaker_name = event.payload.get("speaker_name", "Interviewer")
        
        if not raw_text or not clean_text:
            return
            
        # 1. Update session state/memory
        self.conversation_manager.record_agent_turn(raw_text, speaker=speaker_name)

        # 2. Broadcast transcript to client
        try:
            await self.transport.broadcast_transcript(speaker_name, clean_text)
            logger.info("conversation_handler | broadcasted Agent transcript for [%s]: %s", speaker_name, clean_text[:80])
        except Exception as exc:
            logger.error("conversation_handler | failed to broadcast Agent transcript: %s", exc)
