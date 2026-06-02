"""
Confidence Event model.

Tracks significant confidence events: spikes, collapses, recoveries, milestones.
Enables analysis of confidence patterns and triggers.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class ConfidenceEvent(Base):
    """
    Significant confidence events during candidate journey.
    
    Event types:
    - SPIKE: Sudden confidence increase
    - COLLAPSE: Sudden confidence drop
    - RECOVERY: Recovery after struggle
    - MILESTONE: Achievement milestone
    - BREAKTHROUGH: Significant breakthrough moment
    - PLATEAU: Performance plateau reached
    - REGRESSION: Temporary regression
    
    Enables:
    - Confidence pattern analysis
    - Trigger identification
    - Intervention effectiveness
    - Psychological timeline
    """
    
    __tablename__ = "confidence_events"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    candidate_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    session_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="SET NULL"),
        nullable=True
    )
    
    turn_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("turns.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # ============================================
    # Event Details
    # ============================================
    
    event_type = Column(String, nullable=False)
    # spike, collapse, recovery, milestone, breakthrough, plateau, regression
    
    # ============================================
    # Confidence Metrics
    # ============================================
    
    confidence_before = Column(Float, nullable=True)  # 0-100
    confidence_after = Column(Float, nullable=True)  # 0-100
    confidence_delta = Column(Float, nullable=True)  # Change amount
    
    # ============================================
    # Context
    # ============================================
    
    # Trigger context (JSONB for structured data)
    # Format: {
    #   "trigger_type": "successful_recovery",
    #   "question_type": "system_design",
    #   "pressure_level": "high",
    #   "recovery_mode": "hint"
    # }
    trigger_context = Column(JSONB, nullable=True)
    
    # Contributing factors (JSONB for structured data)
    # Format: [
    #   {"factor": "successful_hint_recovery", "impact": 0.3},
    #   {"factor": "positive_reinforcement", "impact": 0.2}
    # ]
    contributing_factors = Column(JSONB, nullable=True)
    
    # Description
    event_description = Column(String, nullable=True)
    
    # ============================================
    # Metadata
    # ============================================
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ============================================
    # Relationships
    # ============================================
    
    candidate = relationship("User")
    session = relationship("InterviewSession")
    turn = relationship("Turn")
    
    def __repr__(self) -> str:
        return (
            f"<ConfidenceEvent("
            f"type={self.event_type}, "
            f"candidate_id={self.candidate_id}, "
            f"delta={self.confidence_delta:.1f if self.confidence_delta else 'N/A'}"
            f")>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "candidate_id": str(self.candidate_id),
            "session_id": str(self.session_id) if self.session_id else None,
            "turn_id": str(self.turn_id) if self.turn_id else None,
            
            # Event
            "event_type": self.event_type,
            "event_description": self.event_description,
            
            # Metrics
            "confidence_before": self.confidence_before,
            "confidence_after": self.confidence_after,
            "confidence_delta": self.confidence_delta,
            
            # Context
            "trigger_context": self.trigger_context,
            "contributing_factors": self.contributing_factors,
            
            # Metadata
            "timestamp": self.timestamp.isoformat(),
            "created_at": self.created_at.isoformat()
        }
    
    def is_positive_event(self) -> bool:
        """Check if this is a positive confidence event."""
        positive_events = ["spike", "recovery", "milestone", "breakthrough"]
        return self.event_type in positive_events
    
    def is_negative_event(self) -> bool:
        """Check if this is a negative confidence event."""
        negative_events = ["collapse", "regression"]
        return self.event_type in negative_events
    
    def get_magnitude(self) -> str:
        """
        Get event magnitude.
        
        Returns: minor, moderate, major
        """
        if not self.confidence_delta:
            return "unknown"
        
        abs_delta = abs(self.confidence_delta)
        
        if abs_delta >= 20:
            return "major"
        elif abs_delta >= 10:
            return "moderate"
        else:
            return "minor"
