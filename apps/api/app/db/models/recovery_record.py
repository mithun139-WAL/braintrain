"""
Recovery Record model.

Tracks recovery loops triggered during interviews when candidates struggle.
Measures intervention effectiveness and improvement after recovery.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class RecoveryRecord(Base):
    """
    Recovery intervention records.
    
    Recovery modes:
    - HINT: Directional hint
    - BREAKDOWN: Break question into parts
    - REFRAME: Rephrase question
    - STEP_BY_STEP: Guide through reasoning
    - ENCOURAGEMENT: Acknowledge effort, encourage
    - SIMPLIFIED_VERSION: Offer simpler variant
    - PARTIAL_CREDIT_RECOVERY: Build on correct parts
    
    Tracks:
    - Initial struggle
    - Intervention provided
    - Post-recovery performance
    - Success metrics
    """
    
    __tablename__ = "recovery_records"
    
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
    # Recovery Context
    # ============================================
    
    recovery_mode = Column(String, nullable=False)
    # hint, breakdown, reframe, step_by_step, encouragement,
    # simplified_version, partial_credit_recovery
    
    trigger_reason = Column(String, nullable=True)
    # poor_answer, confusion, panic, cognitive_overload, 
    # repeated_failure, confidence_drop
    
    # ============================================
    # Before Recovery
    # ============================================
    
    initial_answer = Column(Text, nullable=True)
    
    initial_quality = Column(Float, nullable=True)  # 0-100
    
    # Struggle indicators (JSONB for structured data)
    # Format: {
    #   "filler_words": 15,
    #   "pauses": 8,
    #   "fragmentation": 0.7,
    #   "latency": 5.2
    # }
    struggle_indicators = Column(JSONB, nullable=True)
    
    # ============================================
    # Recovery Intervention
    # ============================================
    
    intervention_provided = Column(Text, nullable=False)
    # The actual hint/guidance/reframe provided
    
    intervention_type = Column(String, nullable=True)
    # Type of intervention within the mode
    
    # ============================================
    # After Recovery
    # ============================================
    
    post_recovery_answer = Column(Text, nullable=True)
    
    post_recovery_quality = Column(Float, nullable=True)  # 0-100
    
    improvement_delta = Column(Float, nullable=True)
    # post_recovery_quality - initial_quality
    
    # ============================================
    # Success Metrics
    # ============================================
    
    recovery_successful = Column(Boolean, nullable=True)
    # Did the recovery help?
    
    recovery_time_seconds = Column(Float, nullable=True)
    # Time from intervention to stabilization
    
    confidence_restored = Column(Boolean, nullable=True)
    # Did confidence return to baseline?
    
    # Additional success indicators
    structure_improved = Column(Boolean, default=False)
    clarity_improved = Column(Boolean, default=False)
    completeness_improved = Column(Boolean, default=False)
    
    # ============================================
    # Metadata
    # ============================================
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ============================================
    # Relationships
    # ============================================
    
    session = relationship("InterviewSession")
    turn = relationship("Turn")
    candidate = relationship("User")
    
    def __repr__(self) -> str:
        return (
            f"<RecoveryRecord("
            f"mode={self.recovery_mode}, "
            f"success={self.recovery_successful}, "
            f"delta={self.improvement_delta:.1f if self.improvement_delta else 'N/A'}"
            f")>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "turn_id": str(self.turn_id) if self.turn_id else None,
            "candidate_id": str(self.candidate_id),
            
            # Context
            "recovery_mode": self.recovery_mode,
            "trigger_reason": self.trigger_reason,
            
            # Before
            "initial_answer": self.initial_answer,
            "initial_quality": self.initial_quality,
            "struggle_indicators": self.struggle_indicators,
            
            # Intervention
            "intervention_provided": self.intervention_provided,
            "intervention_type": self.intervention_type,
            
            # After
            "post_recovery_answer": self.post_recovery_answer,
            "post_recovery_quality": self.post_recovery_quality,
            "improvement_delta": self.improvement_delta,
            
            # Success
            "recovery_successful": self.recovery_successful,
            "recovery_time_seconds": self.recovery_time_seconds,
            "confidence_restored": self.confidence_restored,
            "structure_improved": self.structure_improved,
            "clarity_improved": self.clarity_improved,
            "completeness_improved": self.completeness_improved,
            
            # Metadata
            "timestamp": self.timestamp.isoformat(),
            "created_at": self.created_at.isoformat()
        }
    
    def calculate_success(self) -> bool:
        """
        Calculate if recovery was successful based on metrics.
        
        Success criteria:
        - Quality improved by at least 10 points OR
        - At least 2 of: structure, clarity, completeness improved
        """
        if self.improvement_delta is not None and self.improvement_delta >= 10:
            return True
        
        improvements = sum([
            self.structure_improved or False,
            self.clarity_improved or False,
            self.completeness_improved or False
        ])
        
        return improvements >= 2
    
    def get_recovery_effectiveness(self) -> str:
        """
        Get recovery effectiveness rating.
        
        Returns: highly_effective, effective, partially_effective, ineffective
        """
        if not self.improvement_delta:
            return "unknown"
        
        if self.improvement_delta >= 20:
            return "highly_effective"
        elif self.improvement_delta >= 10:
            return "effective"
        elif self.improvement_delta >= 5:
            return "partially_effective"
        else:
            return "ineffective"
