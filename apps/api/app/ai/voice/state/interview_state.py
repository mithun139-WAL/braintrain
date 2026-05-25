from dataclasses import dataclass
from typing import Optional, Any
from app.ai.voice.state.conversation_state import ConversationState
from app.ai.voice.state.candidate_state import CandidateState

@dataclass
class InterviewState:
    session_id: str
    conversation: ConversationState
    candidate: CandidateState
    mode: str
    difficulty: str
    adaptive_enabled: bool
    panel_mode: bool
    completed: bool
    pressure_level: str = "NORMAL"
    behavioral_signals: Optional[Any] = None
    target_duration_minutes: int = 15
