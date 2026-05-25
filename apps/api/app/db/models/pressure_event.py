"""
Pressure Event model.

Tracks pressure events during interviews (interruptions, challenges, silences, etc.)
and measures candidate response and recovery.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PressureEvent(Base):
    """
    Pressure events applied during interviews.
    
    Event types:
    - INTERRUPTION: Interviewer interrupts candidate mid-answer
    - RAPID_FOLLOWUP: Quick followup question
    - AMBIGUOUS_QUESTION: Deliberately ambiguous question
    - SILENCE_PRESSURE: Interviewer remains silent after answer
    - CHALLENGE_ASSUMPTION: Challenge candidate's reasoning
    - TRADEOFF_CONFRONTATION: Press on tradeoff decisions
    - CLARIFICATION_DEMAND: Demand clarification
    - MULTI_PART_QUESTION: Complex multi-part question
    - TECHNICAL_DEEP_DIVE: Deep technical probing
    
    Tracks:
    - Event details and intensity
    - Candidate response quality
    - Recovery metrics
    - Performance impact
    """
    
    __tablename__ = "pressure_events"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    session_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    turn_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("turns.id", ondelete="SET NULL"),
        nullable=True
    )
    
    candidate_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # ============================================
    # Event Details
    # ============================================
    
    event_type = Column(String, nullable=False)
    # interruption, rapid_followup, ambiguous_question, silence_pressure,
    # challenge_assumption, tradeoff_confrontation, clarification_demand,
    # multi_part_question, technical_deep_dive
    
    intensity = Column(Float, nullable=True)  # 0-1 scale
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ============================================
    # Context
    # ============================================
    
    interviewer_persona = Column(String, nullable=True)
    pressure_level = Column(String, nullable=True)  # safe, standard, high, etc.
    
    # Event-specific context
    event_context = Column(Text, nullable=True)  # Description of what happened
    
    # ============================================
    # Candidate Response
    # ============================================
    
    candidate_response = Column(Text, nullable=True)
    
    response_quality = Column(Float, nullable=True)  # 0-100
    
    recovery_time_seconds = Column(Float, nullable=True)
    
    composure_maintained = Column(Boolean, nullable=True)
    
    # ============================================
    # Performance Impact
    # ============================================
    
    # Performance before pressure event
    performance_before = Column(Float, nullable=True)  # 0-100
    
    # Performance after pressure event
    performance_after = Column(Float, nullable=True)  # 0-100
    
    # Change in performance
    performance_delta = Column(Float, nullable=True)  # Can be negative
    
    # Recovery success
    recovered_successfully = Column(Boolean, nullable=True)
    
    # ============================================
    # Metadata
    # ============================================
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ============================================
    # Relationships
    # ============================================
    
    session = relationship("InterviewSession")
    turn = relationship("Turn")
    candidate = relationship("User")
    
    def __repr__(self) -> str:
        return (
            f"<PressureEvent("
            f"type={self.event_type}, "
            f"candidate_id={self.candidate_id}, "
            f"composure={self.composure_maintained}"
            f")>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "turn_id": str(self.turn_id) if self.turn_id else None,
            "candidate_id": str(self.candidate_id),
            
            # Event
            "event_type": self.event_type,
            "intensity": self.intensity,
            "timestamp": self.timestamp.isoformat(),
            
            # Context
            "interviewer_persona": self.interviewer_persona,
            "pressure_level": self.pressure_level,
            "event_context": self.event_context,
            
            # Response
            "candidate_response": self.candidate_response,
            "response_quality": self.response_quality,
            "recovery_time_seconds": self.recovery_time_seconds,
            "composure_maintained": self.composure_maintained,
            
            # Impact
            "performance_before": self.performance_before,
            "performance_after": self.performance_after,
            "performance_delta": self.performance_delta,
            "recovered_successfully": self.recovered_successfully,
            
            "created_at": self.created_at.isoformat()
        }
    
    def was_successful_recovery(self) -> bool:
        """
        Determine if candidate successfully recovered from pressure event.
        
        Successful recovery:
        - Composure maintained
        - Performance delta >= 0 (didn't degrade)
        - Recovery time reasonable (<30 seconds)
        """
        if self.composure_maintained is False:
            return False
        
        if self.performance_delta is not None and self.performance_delta < -10:
            return False  # Significant performance drop
        
        if self.recovery_time_seconds is not None and self.recovery_time_seconds > 30:
            return False  # Took too long to recover
        
        return True
