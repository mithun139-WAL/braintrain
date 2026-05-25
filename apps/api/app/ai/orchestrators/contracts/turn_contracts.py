"""
Turn orchestrator contracts.

Defines data models for turn-level decision making.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TurnAction(str, Enum):
    """Actions the orchestrator can take after a candidate turn."""
    FOLLOW_UP = "follow_up"
    NEXT_QUESTION = "next_question"
    CLARIFY = "clarify"
    PROBE_DEEPER = "probe_deeper"
    MOVE_TO_NEXT_ROUND = "move_to_next_round"
    CHALLENGE_CANDIDATE = "challenge_candidate"
    GIVE_HINT = "give_hint"
    SIMPLIFY_QUESTION = "simplify_question"
    REQUEST_ELABORATION = "request_elaboration"
    ACKNOWLEDGE_AND_CONTINUE = "acknowledge_and_continue"
    # Fired when the session-level topic-fixation guard detects the candidate
    # is circling one concept. Signals the generator to produce a broad
    # context / "let's step back" prompt.
    BREADTH_REDIRECT = "breadth_redirect"


class AnswerQuality(str, Enum):
    """Candidate answer quality assessment."""
    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"
    INCORRECT = "incorrect"
    OFF_TOPIC = "off_topic"
    VAGUE = "vague"
    CONTRADICTORY = "contradictory"


class ConfidenceLevel(str, Enum):
    """Candidate confidence levels."""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


class CandidateTurn(BaseModel):
    """Candidate's turn data."""
    model_config = ConfigDict(use_enum_values=True)
    
    transcript: str
    duration_seconds: float
    hesitation_seconds: float = 0.0
    filler_word_count: int = 0
    response_latency_seconds: float = 0.0  # Time to start responding
    
    # Analyzed signals
    confidence_score: float = Field(ge=0.0, le=1.0)
    detected_topics: List[str] = Field(default_factory=list)
    detected_technologies: List[str] = Field(default_factory=list)
    detected_patterns: List[str] = Field(default_factory=list)  # e.g., "STAR", "tradeoff"
    
    # Flags
    uncertainty_flags: List[str] = Field(default_factory=list)  # "i think", "maybe", etc.
    interruption_detected: bool = False
    clarification_requested: bool = False
    topic_drift_detected: bool = False
    
    # Context
    question_id: Optional[str] = None
    is_followup_response: bool = False
    turn_index: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TurnDecision(BaseModel):
    """Orchestrator's decision for next action."""
    model_config = ConfigDict(use_enum_values=True, extra="allow")
    
    action: TurnAction
    reasoning: Optional[str] = None
    reason: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Action parameters
    target_topic: Optional[str] = None
    followup_depth: int = Field(default=1, ge=1, le=5)
    escalation_level: int = Field(default=0, ge=0, le=3)
    challenge_intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Answer assessment
    answer_quality: Optional[AnswerQuality] = None
    quality_explanation: Optional[str] = None
    
    # Extra fields
    should_adjust_difficulty: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    followup_strategy: Optional["FollowUpStrategy"] = None
    
    # Session-layer directive (set by SessionOrchestrator before turn processing).
    # Contains coverage pivot, pressure level, recovery state, etc.
    # Type is Dict to avoid circular import; consumers cast to SessionDirective.
    session_directive: Optional[Dict[str, Any]] = None

    # Next question hints
    suggested_question_type: Optional[str] = None
    suggested_difficulty: Optional[str] = None
    context_to_include: List[str] = Field(default_factory=list)

    # Timing
    estimated_response_time_ms: Optional[int] = None
    urgency: str = "normal"  # normal, high, low



class TurnAnalysis(BaseModel):
    """Detailed turn analysis from multiple signals."""
    
    # Content analysis
    topics_mentioned: List[str]
    technologies_mentioned: List[str]
    concepts_explained: List[str]
    
    # Quality signals
    has_star_structure: bool = False
    has_quantified_metrics: bool = False
    shows_ownership: bool = False
    demonstrates_tradeoffs: bool = False
    mentions_alternatives: bool = False
    
    # Communication signals
    clarity_score: float = Field(ge=0.0, le=100.0)
    conciseness_score: float = Field(ge=0.0, le=100.0)
    relevance_score: float = Field(ge=0.0, le=100.0)
    
    # Confidence signals
    confidence_level: ConfidenceLevel
    hesitation_indicators: List[str]
    certainty_language_count: int
    uncertainty_language_count: int
    
    # Behavioral signals
    interruption_handled_gracefully: Optional[bool] = None
    recovered_from_confusion: Optional[bool] = None
    asked_clarifying_questions: bool = False
    
    # Red flags
    contradicts_previous_answer: bool = False
    appears_to_be_bluffing: bool = False
    topic_drift_severity: float = Field(default=0.0, ge=0.0, le=1.0)


class FollowUpStrategy(BaseModel):
    """Strategy for follow-up questioning."""
    
    strategy_type: str  # probe_deeper, clarify, challenge, explore_related
    target_weakness: Optional[str] = None
    depth_increase: int = Field(default=1, ge=0, le=3)
    
    # Question characteristics
    should_reference_previous_answer: bool = True
    should_ask_for_example: bool = False
    should_ask_for_tradeoff: bool = False
    should_ask_for_alternative: bool = False
    should_simplify: bool = False
    
    # Tone
    tone: str = "neutral"  # neutral, supportive, challenging, skeptical


class TurnContext(BaseModel):
    """Context for turn decision making."""
    
    current_question: str
    current_question_id: str
    question_difficulty: str
    question_domain: str
    
    # History
    previous_turns_count: int
    consecutive_followups: int
    recent_answer_qualities: List[AnswerQuality]
    
    # Interview state
    interview_phase: str
    time_remaining_minutes: int
    questions_remaining: int
    
    # Candidate state
    candidate_performance_trend: str  # improving, stable, declining
    candidate_frustration_level: float = Field(ge=0.0, le=1.0)
    candidate_engagement_level: float = Field(ge=0.0, le=1.0)


class TurnMetrics(BaseModel):
    """Metrics for a turn."""
    
    stt_latency_ms: Optional[int] = None
    analysis_latency_ms: Optional[int] = None
    decision_latency_ms: Optional[int] = None
    question_generation_latency_ms: Optional[int] = None
    tts_latency_ms: Optional[int] = None
    total_latency_ms: Optional[int] = None
    
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    
    cache_hit: bool = False
    fallback_triggered: bool = False
