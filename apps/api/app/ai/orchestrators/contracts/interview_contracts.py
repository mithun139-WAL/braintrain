"""
Interview orchestrator contracts.

Defines data models for interview lifecycle management.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class InterviewPhase(str, Enum):
    """Interview phases for orchestrated flow."""
    INTRODUCTION = "introduction"
    RESUME_DISCUSSION = "resume_discussion"
    TECHNICAL_ROUND_1 = "technical_round_1"
    TECHNICAL_ROUND_2 = "technical_round_2"
    SYSTEM_DESIGN = "system_design"
    DEBUGGING = "debugging"
    BEHAVIORAL = "behavioral"
    HR = "hr"
    WRAP_UP = "wrap_up"
    COMPLETE = "complete"


class InterviewDomain(str, Enum):
    """Interview domain types."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"
    DATA_STRUCTURES = "data_structures"
    MIXED = "mixed"


class ChallengeLevel(str, Enum):
    """Challenge intensity levels."""
    EASY = "easy"
    MODERATE = "moderate"
    CHALLENGING = "challenging"
    DIFFICULT = "difficult"
    EXTREME = "extreme"


class InterviewerMood(str, Enum):
    """Interviewer mood states."""
    NEUTRAL = "neutral"
    SUPPORTIVE = "supportive"
    INQUISITIVE = "inquisitive"
    SKEPTICAL = "skeptical"
    IMPRESSED = "impressed"
    CONCERNED = "concerned"


class InterviewConfig(BaseModel):
    """Interview configuration."""
    model_config = ConfigDict(use_enum_values=True)
    
    domain: InterviewDomain
    target_duration_minutes: int = Field(default=45, ge=15, le=120)
    max_questions_per_round: int = Field(default=10, ge=1, le=20)
    max_followup_depth: int = Field(default=3, ge=1, le=5)
    enable_adaptive_difficulty: bool = True
    enable_interruptions: bool = False
    company_name: Optional[str] = None
    interview_style: str = "standard"  # standard, faang, startup, relaxed


class InterviewMetrics(BaseModel):
    """Real-time interview metrics."""
    questions_asked: int = 0
    followups_asked: int = 0
    total_turns: int = 0
    candidate_speaking_time_seconds: float = 0.0
    interviewer_speaking_time_seconds: float = 0.0
    average_response_time_seconds: float = 0.0
    hesitation_count: int = 0
    interruption_count: int = 0
    clarification_requests: int = 0


class PhaseTransition(BaseModel):
    """Phase transition event."""
    from_phase: InterviewPhase
    to_phase: InterviewPhase
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(ge=0.0, le=1.0)


class InterviewConstraints(BaseModel):
    """Domain-specific interview constraints."""
    allowed_topics: List[str] = Field(default_factory=list)
    forbidden_topics: List[str] = Field(default_factory=list)
    domain_boundaries: Dict[str, Any] = Field(default_factory=dict)
    max_topic_drift_threshold: float = 0.3
    enforce_star_method: bool = False  # For behavioral
    require_code_walkthrough: bool = False  # For technical


class RoundCompletion(BaseModel):
    """Round completion assessment."""
    round_index: int
    phase: InterviewPhase
    is_complete: bool
    completion_reason: str
    questions_covered: int
    topics_covered: List[str]
    candidate_performance_score: float = Field(ge=0.0, le=100.0)
    time_used_seconds: int
    should_continue: bool


class InterviewStartRequest(BaseModel):
    """Request to start an interview."""
    session_id: str
    candidate_id: str
    journey_id: Optional[str] = None
    config: InterviewConfig
    initial_phase: InterviewPhase = InterviewPhase.INTRODUCTION
    resume_context: Optional[str] = None
    job_description_context: Optional[str] = None


class InterviewStopRequest(BaseModel):
    """Request to stop an interview."""
    session_id: str
    reason: str
    force: bool = False


class PhaseChangeRequest(BaseModel):
    """Request to change interview phase."""
    session_id: str
    target_phase: InterviewPhase
    reason: str
    skip_validation: bool = False
