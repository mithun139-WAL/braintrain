"""
Mind State History model.

Stores snapshots of candidate mind state over time for longitudinal analysis.
Enables tracking of growth, trends, and adaptation patterns.
"""
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.candidate_mind_state import CandidateMindState



class MindStateHistory(Base):
    """
    Historical snapshots of candidate mind state.
    
    Enables:
    - Longitudinal trend analysis
    - Growth tracking over time
    - Session-to-session comparison
    - Adaptation pattern detection
    - Performance evolution visualization
    """
    
    __tablename__ = "mind_state_history"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    candidate_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    mind_state_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("candidate_mind_states.id", ondelete="CASCADE"),
        nullable=False
    )
    
    session_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # ============================================
    # Snapshot Data
    # ============================================
    
    snapshot_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Full mind state snapshot (JSONB for flexibility)
    # Contains all 19 psychological metrics at time of snapshot
    mind_state_snapshot = Column(JSONB, nullable=False)
    
    # ============================================
    # Session Context
    # ============================================
    
    session_type = Column(String, nullable=True)  # practice, mock, real
    interview_domain = Column(String, nullable=True)  # frontend, backend, etc.
    difficulty_level = Column(String, nullable=True)  # easy, medium, hard
    pressure_level = Column(String, nullable=True)  # safe, standard, high, etc.
    interviewer_persona = Column(String, nullable=True)  # persona used in session
    
    # ============================================
    # Performance Summary
    # ============================================
    
    # Session-level aggregates
    session_confidence_avg = Column(Float, nullable=True)
    session_pressure_avg = Column(Float, nullable=True)
    session_clarity_avg = Column(Float, nullable=True)
    session_resilience_avg = Column(Float, nullable=True)
    
    # Delta from previous snapshot
    confidence_delta = Column(Float, nullable=True)
    pressure_delta = Column(Float, nullable=True)
    communication_delta = Column(Float, nullable=True)
    
    # ============================================
    # Metadata
    # ============================================
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ============================================
    # Relationships
    # ============================================
    
    candidate = relationship("User")
    mind_state = relationship("CandidateMindState", back_populates="history")
    session = relationship("InterviewSession")
    
    def __repr__(self) -> str:
        return (
            f"<MindStateHistory("
            f"candidate_id={self.candidate_id}, "
            f"session_id={self.session_id}, "
            f"confidence_avg={self.session_confidence_avg:.1f if self.session_confidence_avg else 'N/A'}"
            f")>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "candidate_id": str(self.candidate_id),
            "session_id": str(self.session_id) if self.session_id else None,
            "snapshot_timestamp": self.snapshot_timestamp.isoformat(),
            
            # Snapshot
            "mind_state_snapshot": self.mind_state_snapshot,
            
            # Context
            "session_type": self.session_type,
            "interview_domain": self.interview_domain,
            "difficulty_level": self.difficulty_level,
            "pressure_level": self.pressure_level,
            "interviewer_persona": self.interviewer_persona,
            
            # Performance
            "session_confidence_avg": self.session_confidence_avg,
            "session_pressure_avg": self.session_pressure_avg,
            "session_clarity_avg": self.session_clarity_avg,
            "session_resilience_avg": self.session_resilience_avg,
            
            # Deltas
            "confidence_delta": self.confidence_delta,
            "pressure_delta": self.pressure_delta,
            "communication_delta": self.communication_delta,
            
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def create_snapshot(
        cls,
        candidate_id: UUID,
        mind_state: "CandidateMindState",
        session_id: Optional[UUID] = None,
        session_context: Optional[Dict[str, Any]] = None
    ) -> "MindStateHistory":
        """
        Create a snapshot from current mind state.
        
        Args:
            candidate_id: Candidate UUID
            mind_state: Current CandidateMindState instance
            session_id: Optional session UUID
            session_context: Optional session context data
        
        Returns:
            New MindStateHistory instance
        """
        snapshot_data = mind_state.to_dict()
        
        context = session_context or {}
        
        return cls(
            candidate_id=candidate_id,
            mind_state_id=mind_state.id,
            session_id=session_id,
            snapshot_timestamp=datetime.utcnow(),
            mind_state_snapshot=snapshot_data,
            session_type=context.get("session_type"),
            interview_domain=context.get("interview_domain"),
            difficulty_level=context.get("difficulty_level"),
            pressure_level=context.get("pressure_level"),
            interviewer_persona=context.get("interviewer_persona"),
            session_confidence_avg=context.get("session_confidence_avg"),
            session_pressure_avg=context.get("session_pressure_avg"),
            session_clarity_avg=context.get("session_clarity_avg"),
            session_resilience_avg=context.get("session_resilience_avg")
        )
