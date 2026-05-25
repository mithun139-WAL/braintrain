"""
Evaluation orchestrator contracts.

Defines data models for unified evaluation system.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.ai.orchestrators.contracts.turn_contracts import AnswerQuality


class EvaluationDimension(BaseModel):
    """Single evaluation dimension."""
    name: str
    score: float = Field(ge=0.0, le=100.0)
    weight: float = Field(ge=0.0, le=1.0)
    explanation: str
    evidence: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class EvaluationWeights(BaseModel):
    """Weights for different evaluation dimensions."""
    technical_accuracy: float = Field(default=0.3, ge=0.0, le=1.0)
    depth: float = Field(default=0.2, ge=0.0, le=1.0)
    problem_solving: float = Field(default=0.2, ge=0.0, le=1.0)
    communication: float = Field(default=0.2, ge=0.0, le=1.0)
    confidence: float = Field(default=0.1, ge=0.0, le=1.0)
    
    def validate_sum(self) -> bool:
        """Check if weights sum to approximately 1.0."""
        total = (
            self.technical_accuracy +
            self.depth +
            self.problem_solving +
            self.communication +
            self.confidence
        )
        return abs(total - 1.0) < 0.01


class RuleBasedMetrics(BaseModel):
    """Deterministic rule-based metrics."""
    
    # Communication metrics
    filler_word_score: float = Field(default=0.0, ge=0.0, le=100.0)
    filler_word_count: int = 0
    filler_word_density: float = 0.0
    
    confidence_score: float = Field(default=0.0, ge=0.0, le=100.0)
    hesitation_count: int = 0
    hesitation_density: float = 0.0
    
    clarity_score: float = Field(default=0.0, ge=0.0, le=100.0)
    average_sentence_length: float = 0.0
    vocabulary_diversity: float = 0.0
    
    # Structure metrics (behavioral)
    star_score: float = Field(default=0.0, ge=0.0, le=100.0)
    star_components_found: Dict[str, bool] = Field(default_factory=dict)
    
    # Ownership metrics
    ownership_score: float = Field(default=0.0, ge=0.0, le=100.0)
    i_to_we_ratio: float = 0.0
    ownership_phrase_count: int = 0
    
    # Impact metrics
    impact_score: float = Field(default=0.0, ge=0.0, le=100.0)
    quantified_metric_count: int = 0
    quantified_examples: List[str] = Field(default_factory=list)
    
    # Stability metrics
    communication_stability_score: float = Field(default=0.0, ge=0.0, le=100.0)
    response_consistency_score: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Technical metrics
    technical_terminology_score: float = Field(default=0.0, ge=0.0, le=100.0)
    terminology_count: int = 0
    correct_terminology_ratio: float = 0.0
    technical_keyword_coverage: float = 0.0


class LLMBasedMetrics(BaseModel):
    """LLM-derived semantic metrics (secondary)."""
    
    technical_accuracy: Optional[float] = Field(None, ge=0.0, le=100.0)
    depth: Optional[float] = Field(None, ge=0.0, le=100.0)
    problem_solving: Optional[float] = Field(None, ge=0.0, le=100.0)
    reasoning: Optional[str] = ""
    
    communication_effectiveness: Optional[float] = Field(None, ge=0.0, le=100.0)
    answer_relevance: Optional[float] = Field(None, ge=0.0, le=100.0)
    completeness: Optional[float] = Field(None, ge=0.0, le=100.0)
    
    # Observations (not scores)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class TimingMetrics(BaseModel):
    """Response timing analysis."""
    
    thinking_time_score: float = Field(ge=0.0, le=100.0)
    thinking_time_seconds: float = 0.0
    
    response_time_score: float = Field(ge=0.0, le=100.0)
    response_time_seconds: float = 0.0
    
    pacing_score: float = Field(ge=0.0, le=100.0)
    pacing_consistency: float = 0.0
    
    # Pressure handling
    pressure_handling_score: float = Field(ge=0.0, le=100.0)
    recovers_quickly: bool = False


class UnifiedEvaluation(BaseModel):
    """Unified evaluation combining all signals."""
    model_config = ConfigDict(use_enum_values=False)
    
    final_score: float = Field(ge=0.0, le=100.0)
    rule_based_score: float = Field(default=0.0, ge=0.0, le=100.0)
    llm_based_score: float = Field(default=0.0, ge=0.0, le=100.0)
    answer_quality: AnswerQuality
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Optional / default fields to support different schemas
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0)
    weights_used: Optional[EvaluationWeights] = None
    
    # Component scores
    rule_based_metrics: RuleBasedMetrics
    llm_based_metrics: LLMBasedMetrics
    timing_metrics: Optional[TimingMetrics] = None
    
    # Dimensions (weighted combination)
    dimensions: List[EvaluationDimension] = Field(default_factory=list)
    
    # Summary
    performance_level: Optional[str] = None  # excellent, good, average, below_average, poor
    key_strengths: List[str] = Field(default_factory=list)
    key_weaknesses: List[str] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)
    
    # Red flags
    red_flags: List[str] = Field(default_factory=list)
    contradiction_detected: bool = False
    bluffing_detected: bool = False
    topic_drift_detected: bool = False
    
    # Metadata
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    evaluation_latency_ms: Optional[int] = None
    evaluator_model: Optional[str] = None


class ResponseEvaluation(BaseModel):
    """Evaluation for a single response."""
    
    response_id: str
    question_id: str
    transcript: str
    
    evaluation: UnifiedEvaluation
    
    # Context
    question_difficulty: str
    domain: str
    is_followup: bool = False
    
    # History comparison
    improvement_from_previous: Optional[float] = None
    consistency_with_history: Optional[float] = None


class SessionEvaluation(BaseModel):
    """Aggregated evaluation for entire session."""
    
    session_id: str
    
    # Overall metrics
    overall_score: float = Field(ge=0.0, le=100.0)
    overall_confidence: float = Field(ge=0.0, le=1.0)
    
    # Aggregated dimensions
    aggregated_dimensions: List[EvaluationDimension]
    
    # Response evaluations
    response_count: int
    responses_evaluated: List[ResponseEvaluation]
    
    # Trends
    performance_trend: str  # improving, stable, declining, mixed
    trend_analysis: str
    
    # Summary
    top_strengths: List[str]
    top_weaknesses: List[str]
    overall_recommendation: str
    hiring_recommendation: Optional[str] = None  # strong_yes, yes, maybe, no, strong_no
    
    # Metadata
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    duration_minutes: int


class EvaluationConfig(BaseModel):
    """Configuration for evaluation orchestrator."""
    
    # Weights for rule-based vs LLM-based
    rule_based_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    llm_based_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    
    # Domain-specific weights
    domain_weights: Dict[str, float] = Field(default_factory=dict)
    
    # Rubric
    dimensions_config: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Thresholds
    excellent_threshold: float = 85.0
    good_threshold: float = 70.0
    average_threshold: float = 50.0
    
    # Flags
    enable_contradiction_detection: bool = True
    enable_bluff_detection: bool = True
    enable_topic_drift_detection: bool = True
    
    # Normalization
    normalize_scores: bool = True
    calibration_factor: float = 1.0


class EvaluationRequest(BaseModel):
    """Request to evaluate a response."""
    
    response_id: str
    transcript: str
    question: str
    question_id: str
    
    # Context
    domain: str
    difficulty: str
    is_followup: bool = False
    
    # History
    previous_responses: List[str] = Field(default_factory=list)
    previous_scores: List[float] = Field(default_factory=list)
    
    # Timing data
    thinking_time_seconds: Optional[float] = None
    response_time_seconds: Optional[float] = None
    
    # Configuration
    config: Optional[EvaluationConfig] = None
