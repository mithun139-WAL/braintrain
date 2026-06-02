import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

class MemoryType(str, Enum):
    SEMANTIC = "SEMANTIC"
    EPISODIC = "EPISODIC"
    BEHAVIORAL = "BEHAVIORAL"

@dataclass
class MemoryObject:
    memory_id: uuid.UUID
    candidate_id: uuid.UUID
    memory_type: MemoryType
    content: str
    embedding: Optional[List[float]] = None
    confidence_score: float = 1.0
    relevance_score: float = 1.0
    importance_score: float = 0.5
    decay_factor: float = 1.0
    access_count: int = 0
    source_session_id: Optional[uuid.UUID] = None
    behavioral_tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": str(self.memory_id),
            "candidate_id": str(self.candidate_id),
            "memory_type": self.memory_type.value,
            "content": self.content,
            "confidence_score": self.confidence_score,
            "relevance_score": self.relevance_score,
            "importance_score": self.importance_score,
            "decay_factor": self.decay_factor,
            "access_count": self.access_count,
            "source_session_id": str(self.source_session_id) if self.source_session_id else None,
            "behavioral_tags": self.behavioral_tags,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
        }
