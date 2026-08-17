from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.ai.voice.planning.plan import InterviewPlan

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
    # Interview plan (topic coverage + depth/time budgets). None for legacy
    # sessions where plan generation failed — TurnPolicy falls back to the
    # flat topic_followup_count cap in that case. See app/ai/voice/planning/.
    plan: Optional["InterviewPlan"] = None
