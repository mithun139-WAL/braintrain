"""
Interview runtime state models.

Defines stateful data for interview orchestration.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.ai.orchestrators.contracts.interview_contracts import (
    InterviewPhase,
    InterviewDomain,
    ChallengeLevel,
    InterviewerMood,
    InterviewMetrics
)


class InterviewRuntimeState(BaseModel):
    """Complete runtime state for an interview session."""
    
    # Session identity
    session_id: str
    candidate_id: str
    journey_id: Optional[str] = None
    
    # Phase management
    current_phase: InterviewPhase
    phase_start_time: datetime = Field(default_factory=datetime.utcnow)
    phase_duration_seconds: int = 0
    phase_history: List[str] = Field(default_factory=list)
    
    # Question tracking
    current_question_id: Optional[str] = None
    current_question: Optional[str] = None
    current_round_index: int = 0
    questions_asked: int = 0
    followups_asked: int = 0
    consecutive_followups: int = 0
    
    # Domain and difficulty
    domain: InterviewDomain
    current_challenge_level: ChallengeLevel = ChallengeLevel.MODERATE
    
    # Interviewer state
    interviewer_mood: InterviewerMood = InterviewerMood.NEUTRAL
    interviewer_strategy: str = "standard"  # standard, probing, supportive, challenging
    
    # Progress tracking
    interview_progress_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    round_duration_seconds: int = 0
    total_duration_seconds: int = 0
    estimated_remaining_minutes: int = 0
    
    # Metrics
    metrics: InterviewMetrics = Field(default_factory=InterviewMetrics)
    
    # Flags
    is_paused: bool = False
    is_complete: bool = False
    requires_intervention: bool = False
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CandidateRuntimeState(BaseModel):
    """Runtime state tracking candidate performance and behavior."""
    
    candidate_id: str
    session_id: str
    
    # Performance tracking
    current_performance_score: float = Field(default=50.0, ge=0.0, le=100.0)
    performance_trend: str = "stable"  # improving, stable, declining
    recent_scores: List[float] = Field(default_factory=list)
    answer_quality_history: List[str] = Field(default_factory=list)
    
    # Confidence tracking
    current_confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    confidence_trend: str = "stable"
    recent_confidence_scores: List[float] = Field(default_factory=list)
    
    # Behavioral signals
    frustration_level: float = Field(default=0.0, ge=0.0, le=1.0)
    engagement_level: float = Field(default=1.0, ge=0.0, le=1.0)
    stress_level: float = Field(default=0.3, ge=0.0, le=1.0)
    
    # Communication patterns
    average_response_time_seconds: float = 0.0
    average_thinking_time_seconds: float = 0.0
    filler_word_frequency: float = 0.0
    hesitation_frequency: float = 0.0
    
    # Topic coverage
    topics_covered: List[str] = Field(default_factory=list)
    topics_struggled_with: List[str] = Field(default_factory=list)
    topics_excelled_at: List[str] = Field(default_factory=list)
    
    # Red flags
    contradiction_count: int = 0
    bluffing_detected_count: int = 0
    topic_drift_count: int = 0
    repeated_failures: int = 0
    
    # Recovery tracking
    recovery_attempts: int = 0
    successful_recoveries: int = 0
    recovery_rate: float = 0.0
    
    # Timestamps
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OrchestratorState(BaseModel):
    """State for orchestrator coordination."""
    
    session_id: str
    
    # Active orchestrators
    active_orchestrators: List[str] = Field(default_factory=list)
    
    # Current operations
    current_operation: Optional[str] = None
    operation_start_time: Optional[datetime] = None
    
    # Caches
    cached_context: Optional[Dict[str, Any]] = None
    cached_knowledge: Optional[Dict[str, Any]] = None
    cached_persona: Optional[Dict[str, Any]] = None
    
    # Speculative generation
    speculative_next_question: Optional[str] = None
    speculative_followup: Optional[str] = None
    speculative_hint: Optional[str] = None
    speculative_generation_timestamp: Optional[datetime] = None
    
    # Performance tracking
    total_orchestration_calls: int = 0
    total_orchestration_time_ms: int = 0
    average_orchestration_time_ms: float = 0.0
    
    # Fallback tracking
    fallback_count: int = 0
    last_fallback_reason: Optional[str] = None
    last_fallback_timestamp: Optional[datetime] = None
    
    # Health
    health_status: str = "healthy"  # healthy, degraded, critical
    error_count: int = 0
    last_error: Optional[str] = None
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class QuestionState(BaseModel):
    """State for current question."""
    
    question_id: str
    question_text: str
    question_type: str  # initial, followup, clarification, challenge, hint
    
    # Context
    domain: str
    difficulty: str
    target_topics: List[str]
    
    # Asked at
    asked_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Response tracking
    response_received: bool = False
    response_id: Optional[str] = None
    response_quality: Optional[str] = None
    
    # Follow-up tracking
    followup_count: int = 0
    max_followup_depth: int = 3
    can_ask_followup: bool = True
    
    # Evaluation
    evaluated: bool = False
    evaluation_score: Optional[float] = None


class TurnState(BaseModel):
    """State for current turn."""
    
    turn_index: int
    session_id: str
    
    # Question
    question_state: Optional[QuestionState] = None
    
    # Response
    candidate_transcript: Optional[str] = None
    response_duration_seconds: Optional[float] = None
    thinking_time_seconds: Optional[float] = None
    
    # Analysis
    analyzed: bool = False
    analysis_result: Optional[Dict[str, Any]] = None
    
    # Decision
    decision_made: bool = False
    decision: Optional[Dict[str, Any]] = None
    
    # Next action
    next_action: Optional[str] = None
    next_action_params: Optional[Dict[str, Any]] = None
    
    # Timing
    turn_start: datetime = Field(default_factory=datetime.utcnow)
    turn_end: Optional[datetime] = None
    total_turn_time_ms: Optional[int] = None


class PhaseState(BaseModel):
    """State for current interview phase."""
    
    phase: InterviewPhase
    session_id: str
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    target_duration_minutes: int = 15
    elapsed_seconds: int = 0
    
    # Completion criteria
    min_questions_required: int = 3
    questions_asked_in_phase: int = 0
    topics_to_cover: List[str] = Field(default_factory=list)
    topics_covered: List[str] = Field(default_factory=list)
    
    # Performance in phase
    average_score_in_phase: float = 0.0
    phase_scores: List[float] = Field(default_factory=list)
    
    # Completion
    is_complete: bool = False
    completion_reason: Optional[str] = None
    next_phase: Optional[InterviewPhase] = None


class SessionMemoryState(BaseModel):
    """State for session memory and history."""
    
    session_id: str
    
    # Conversation history
    conversation_turns: List[Dict[str, Any]] = Field(default_factory=list)
    compressed_history: Optional[str] = None
    history_token_count: int = 0
    
    # Key facts extracted
    extracted_facts: Dict[str, Any] = Field(default_factory=dict)
    verified_facts: Dict[str, Any] = Field(default_factory=dict)
    
    # Topics discussed
    all_topics_discussed: List[str] = Field(default_factory=list)
    topic_frequency: Dict[str, int] = Field(default_factory=dict)
    
    # Patterns identified
    recurring_patterns: List[str] = Field(default_factory=list)
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)
