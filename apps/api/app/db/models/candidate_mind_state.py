"""
Candidate Mind State model.

Represents the persistent psychological-performance model for a candidate.
This is the CENTRAL intelligence layer for adaptive interviewing.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class CandidateMindState(Base):
    """
    Persistent psychological-performance model for candidate.
    
    Tracks 19 psychological metrics that evolve over time:
    - Confidence and resilience
    - Communication clarity
    - Pressure handling
    - Recovery abilities
    - Strategic thinking
    - Executive presence
    
    This model serves as the central intelligence for:
    - Adaptive interviewer behavior
    - Confidence-aware turn routing
    - Pressure progression decisions
    - Recovery loop triggering
    """
    
    __tablename__ = "candidate_mind_states"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    candidate_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True  # One mind state per candidate
    )
    
    # ============================================
    # Core Psychological Metrics (0-100 normalized)
    # ============================================
    
    # Confidence and resilience
    confidence_level = Column(Float, default=50.0, nullable=False)
    stress_tolerance = Column(Float, default=50.0, nullable=False)
    emotional_stability = Column(Float, default=50.0, nullable=False)
    confidence_under_pressure = Column(Float, default=50.0, nullable=False)
    recovery_speed = Column(Float, default=50.0, nullable=False)
    freeze_response_risk = Column(Float, default=50.0, nullable=False)
    
    # Communication abilities
    communication_clarity = Column(Float, default=50.0, nullable=False)
    response_structure = Column(Float, default=50.0, nullable=False)
    filler_word_control = Column(Float, default=50.0, nullable=False)
    speaking_consistency = Column(Float, default=50.0, nullable=False)
    executive_presence = Column(Float, default=50.0, nullable=False)
    
    # Cognitive abilities
    memory_recall_strength = Column(Float, default=50.0, nullable=False)
    strategic_thinking = Column(Float, default=50.0, nullable=False)
    cognitive_load_tolerance = Column(Float, default=50.0, nullable=False)
    
    # Performance abilities
    hesitation_recovery = Column(Float, default=50.0, nullable=False)
    pressure_handling = Column(Float, default=50.0, nullable=False)
    technical_depth_confidence = Column(Float, default=50.0, nullable=False)
    
    # Behavioral abilities
    storytelling_ability = Column(Float, default=50.0, nullable=False)
    behavioral_authenticity = Column(Float, default=50.0, nullable=False)
    
    # ============================================
    # Trend Tracking
    # ============================================
    
    # Rolling averages (last N sessions)
    # Format: {"confidence_level": [65, 68, 70], "stress_tolerance": [60, 62, 65]}
    rolling_average_scores = Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}"
    )
    
    # Improvement velocity (rate of change per session)
    # Format: {"confidence_level": 0.5, "stress_tolerance": 0.3}
    improvement_velocity = Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}"
    )
    
    # Trend directions
    confidence_trend = Column(
        String,
        default="stable",
        nullable=False
    )  # improving, stable, declining
    
    pressure_trend = Column(
        String,
        default="stable",
        nullable=False
    )  # improving, stable, declining
    
    communication_trend = Column(
        String,
        default="stable",
        nullable=False
    )  # improving, stable, declining
    
    # ============================================
    # Topic Performance
    # ============================================
    
    # Topics where candidate struggles
    # Format: [{"topic": "system_design", "score": 45, "sessions": 3}]
    weak_topics = Column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]"
    )
    
    # Topics where candidate excels
    # Format: [{"topic": "behavioral", "score": 85, "sessions": 5}]
    strong_topics = Column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]"
    )
    
    # Recurring failure patterns
    # Format: [{"pattern": "rambling", "frequency": 0.7, "context": "technical_questions"}]
    recurring_failures = Column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]"
    )
    
    # Recurring strengths
    # Format: [{"pattern": "clear_structure", "frequency": 0.8, "context": "behavioral"}]
    recurring_strengths = Column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]"
    )
    
    # ============================================
    # Metadata
    # ============================================
    
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Statistics
    session_count = Column(Integer, default=0, nullable=False)
    total_turns_analyzed = Column(Integer, default=0, nullable=False)
    
    # ============================================
    # Relationships
    # ============================================
    
    candidate = relationship("User", back_populates="mind_state")
    history = relationship(
        "MindStateHistory",
        back_populates="mind_state",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return (
            f"<CandidateMindState("
            f"candidate_id={self.candidate_id}, "
            f"confidence={self.confidence_level:.1f}, "
            f"trend={self.confidence_trend}"
            f")>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "candidate_id": str(self.candidate_id),
            
            # Core metrics
            "confidence_level": self.confidence_level,
            "stress_tolerance": self.stress_tolerance,
            "communication_clarity": self.communication_clarity,
            "memory_recall_strength": self.memory_recall_strength,
            "strategic_thinking": self.strategic_thinking,
            "emotional_stability": self.emotional_stability,
            "hesitation_recovery": self.hesitation_recovery,
            "storytelling_ability": self.storytelling_ability,
            "technical_depth_confidence": self.technical_depth_confidence,
            "pressure_handling": self.pressure_handling,
            "behavioral_authenticity": self.behavioral_authenticity,
            "response_structure": self.response_structure,
            "filler_word_control": self.filler_word_control,
            "confidence_under_pressure": self.confidence_under_pressure,
            "executive_presence": self.executive_presence,
            "recovery_speed": self.recovery_speed,
            "freeze_response_risk": self.freeze_response_risk,
            "cognitive_load_tolerance": self.cognitive_load_tolerance,
            "speaking_consistency": self.speaking_consistency,
            
            # Trends
            "rolling_average_scores": self.rolling_average_scores,
            "improvement_velocity": self.improvement_velocity,
            "confidence_trend": self.confidence_trend,
            "pressure_trend": self.pressure_trend,
            "communication_trend": self.communication_trend,
            
            # Topics
            "weak_topics": self.weak_topics,
            "strong_topics": self.strong_topics,
            "recurring_failures": self.recurring_failures,
            "recurring_strengths": self.recurring_strengths,
            
            # Metadata
            "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "session_count": self.session_count,
            "total_turns_analyzed": self.total_turns_analyzed
        }
    
    def get_metric_score(self, metric_name: str) -> Optional[float]:
        """Get score for a specific metric."""
        return getattr(self, metric_name, None)
    
    def update_metric(self, metric_name: str, delta: float) -> None:
        """
        Update a metric with delta, keeping it in 0-100 range.
        
        Args:
            metric_name: Name of the metric to update
            delta: Change amount (can be negative)
        """
        current = getattr(self, metric_name, 50.0)
        new_value = max(0.0, min(100.0, current + delta))
        setattr(self, metric_name, new_value)
    
    def get_overall_confidence_score(self) -> float:
        """
        Calculate overall confidence composite score.
        
        Weighted combination of key confidence metrics.
        """
        return (
            self.confidence_level * 0.30 +
            self.confidence_under_pressure * 0.25 +
            self.emotional_stability * 0.20 +
            self.recovery_speed * 0.15 +
            (100 - self.freeze_response_risk) * 0.10
        )
    
    def get_overall_communication_score(self) -> float:
        """
        Calculate overall communication composite score.
        """
        return (
            self.communication_clarity * 0.30 +
            self.response_structure * 0.25 +
            self.filler_word_control * 0.20 +
            self.executive_presence * 0.15 +
            self.speaking_consistency * 0.10
        )
    
    def get_overall_resilience_score(self) -> float:
        """
        Calculate overall resilience composite score.
        """
        return (
            self.pressure_handling * 0.30 +
            self.stress_tolerance * 0.25 +
            self.recovery_speed * 0.20 +
            self.hesitation_recovery * 0.15 +
            self.emotional_stability * 0.10
        )
