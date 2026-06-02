from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class CandidateState:
    confidence_score: float = 50.0
    hesitation_count: int = 0
    interruption_count: int = 0
    avg_response_seconds: float = 0.0
    avg_thinking_seconds: float = 0.0
    verbosity_score: float = 50.0
    last_response_at: Optional[datetime] = None

    # Step 3 Behavioral Metadata
    interruptions_attempted: int = 0
    clarification_count: int = 0
    followup_count: int = 0
    topic_switches: int = 0
