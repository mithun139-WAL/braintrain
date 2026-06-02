from dataclasses import dataclass, field
from datetime import datetime
from app.ai.voice.events.event_types import EventType

@dataclass(frozen=True)
class Event:
    type: EventType
    session_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    payload: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
