from dataclasses import dataclass, field
from app.ai.voice.decisions.action import InterviewAction

@dataclass
class ConversationDecision:
    action: InterviewAction
    reason: str
    confidence: float
    metadata: dict = field(default_factory=dict)
