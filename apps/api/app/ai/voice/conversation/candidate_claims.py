import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class CandidateClaim:
    fact_id: str
    fact_type: str
    subject: str
    claim: str
    confidence: str
    source_turn_id: int
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if self.confidence not in ("explicit", "uncertain", "inferred"):
            raise ValueError(f"confidence must be explicit, uncertain, or inferred, got: {self.confidence}")

    @classmethod
    def create(
        cls,
        fact_type: str,
        subject: str,
        claim: str,
        confidence: str,
        source_turn_id: int,
    ) -> "CandidateClaim":
        return cls(
            fact_id=str(uuid.uuid4()),
            fact_type=fact_type,
            subject=subject,
            claim=claim,
            confidence=confidence,
            source_turn_id=source_turn_id,
        )
