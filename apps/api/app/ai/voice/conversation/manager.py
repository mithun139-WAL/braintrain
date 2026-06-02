import logging
from datetime import datetime
from typing import Optional
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.conversation.memory import ConversationMemory
from app.ai.voice.conversation.fact_extractor import FactExtractor

logger = logging.getLogger("conversation_manager")

class ConversationManager:
    def __init__(self, state: InterviewState, memory: ConversationMemory):
        self.state = state
        self.memory = memory
        self.fact_extractor: Optional[FactExtractor] = None

    def set_fact_extractor(self, extractor: FactExtractor) -> None:
        self.fact_extractor = extractor

    def record_user_turn(self, text: str, speaker: str = "Candidate", metadata: dict = None) -> None:
        self.memory.add_user_message(content=text, speaker=speaker, metadata=metadata)

        self.state.conversation.messages = self.memory.get_messages()
        self.state.conversation.turn_count = len(self.state.conversation.messages)
        self.state.conversation.current_speaker = speaker
        self.state.conversation.updated_at = datetime.utcnow()

        self.state.candidate.last_response_at = datetime.utcnow()

        if self.fact_extractor:
            extracted = self.fact_extractor.extract_from_turn(text)
            if extracted:
                logger.info("fact_extraction | extracted %d claims from turn", len(extracted))

        logger.info("conversation_updated | role: user | speaker: %s | turn_count: %d", speaker, self.state.conversation.turn_count)

    def record_agent_turn(self, text: str, speaker: str = "Interviewer", metadata: dict = None) -> None:
        self.memory.add_agent_message(content=text, speaker=speaker, metadata=metadata)

        self.state.conversation.messages = self.memory.get_messages()
        self.state.conversation.turn_count = len(self.state.conversation.messages)
        self.state.conversation.current_speaker = speaker
        self.state.conversation.current_question_text = text
        self.state.conversation.updated_at = datetime.utcnow()

        logger.info("conversation_updated | role: assistant | speaker: %s | turn_count: %d", speaker, self.state.conversation.turn_count)

    def get_context(self) -> list:
        return self.memory.get_messages()

    def reset(self) -> None:
        self.memory.clear()
        self.state.conversation.messages = []
        self.state.conversation.turn_count = 0
        self.state.conversation.current_question_text = None
        self.state.conversation.current_question_id = None
        self.state.conversation.current_speaker = None
        self.state.conversation.updated_at = datetime.utcnow()
        logger.info("conversation_reset")
