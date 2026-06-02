from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ConversationState:
    messages: list
    current_question_id: Optional[str]
    current_question_text: Optional[str]
    current_topic: Optional[str]
    current_speaker: Optional[str]
    turn_count: int
    topic_followup_count: int
    started_at: datetime
    updated_at: datetime
