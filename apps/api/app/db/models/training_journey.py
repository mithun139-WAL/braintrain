"""
Training Journey model.

Tracks candidate enrollment and progress through structured training programs.
Examples: First Interview Anxiety, FAANG Pressure Simulation, Executive Communication.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class TrainingJourney(Base):
    """
    Candidate enrollment in structured training journey.
    
    Journey examples:
    - first_interview_anxiety: Build confidence for first interviews
    - faang_pressure_simulation: Prepare for FAANG-level pressure
    - executive_communication: Develop executive presence
    - system_design_mastery: Master system design interviews
    - behavioral_confidence: Build behavioral interview confidence
    
    Tracks:
    - Current progress through phases
    - Performance metrics
    - Improvement over time
    - Completion status
    """
    
    __tablename__ = "training_journeys"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    candidate_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # ============================================
    # Journey Details
    # ============================================
    
    journey_id = Column(String, nullable=False)
    # first_interview_anxiety, faang_pressure_simulation, etc.
    
    journey_name = Column(String, nullable=True)
    # Human-readable name
    
    # ============================================
    # Progress
    # ============================================
    
    current_phase = Column(Integer, default=1, nullable=False)
    # Current phase number (1-indexed)
    
    total_phases = Column(Integer, nullable=True)
    # Total number of phases in journey
    
    sessions_completed = Column(Integer, default=0, nullable=False)
    # Sessions completed so far
    
    sessions_in_current_phase = Column(Integer, default=0, nullable=False)
    # Sessions completed in current phase
    
    # ============================================
    # Status
    # ============================================
    
    status = Column(String, default="in_progress", nullable=False)
    # in_progress, completed, abandoned, paused
    
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    paused_at = Column(DateTime, nullable=True)
    
    # ============================================
    # Performance Tracking
    # ============================================
    
    # Baseline metrics at journey start (JSONB)
    # Format: {
    #   "confidence": 60.0,
    #   "resilience": 55.0,
    #   "clarity": 65.0,
    #   "pressure_handling": 58.0
    # }
    baseline_metrics = Column(JSONB, nullable=True)
    
    # Current metrics (JSONB)
    current_metrics = Column(JSONB, nullable=True)
    
    # Improvement metrics (JSONB)
    # Format: {
    #   "confidence": +12.5,
    #   "resilience": +15.0,
    #   "clarity": +8.0
    # }
    improvement_metrics = Column(JSONB, nullable=True)
    
    # Phase-by-phase progress (JSONB)
    # Format: [
    #   {
    #     "phase": 1,
    #     "status": "completed",
    #     "sessions": 3,
    #     "performance": {"confidence": 65, "resilience": 60}
    #   },
    #   {
    #     "phase": 2,
    #     "status": "in_progress",
    #     "sessions": 2,
    #     "performance": {"confidence": 70, "resilience": 68}
    #   }
    # ]
    phase_progress = Column(JSONB, nullable=True, default=list)
    
    # ============================================
    # Goals and Success Criteria
    # ============================================
    
    # Journey goals (JSONB)
    # Format: {
    #   "confidence_goal": 80.0,
    #   "resilience_goal": 75.0,
    #   "clarity_goal": 85.0
    # }
    journey_goals = Column(JSONB, nullable=True)
    
    # Success criteria met (JSONB)
    # Format: {
    #   "confidence_goal_met": true,
    #   "resilience_goal_met": false,
    #   "clarity_goal_met": true
    # }
    success_criteria_met = Column(JSONB, nullable=True, default=dict)
    
    # ============================================
    # Metadata
    # ============================================
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ============================================
    # Relationships
    # ============================================
    
    candidate = relationship("User")
    
    def __repr__(self) -> str:
        return (
            f"<TrainingJourney("
            f"journey_id={self.journey_id}, "
            f"candidate_id={self.candidate_id}, "
            f"phase={self.current_phase}/{self.total_phases}, "
            f"status={self.status}"
            f")>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "candidate_id": str(self.candidate_id),
            
            # Journey
            "journey_id": self.journey_id,
            "journey_name": self.journey_name,
            
            # Progress
            "current_phase": self.current_phase,
            "total_phases": self.total_phases,
            "sessions_completed": self.sessions_completed,
            "sessions_in_current_phase": self.sessions_in_current_phase,
            "progress_percentage": self.get_progress_percentage(),
            
            # Status
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
            
            # Performance
            "baseline_metrics": self.baseline_metrics,
            "current_metrics": self.current_metrics,
            "improvement_metrics": self.improvement_metrics,
            "phase_progress": self.phase_progress,
            
            # Goals
            "journey_goals": self.journey_goals,
            "success_criteria_met": self.success_criteria_met,
            
            # Metadata
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        if not self.total_phases:
            return 0.0
        
        # Progress = (completed_phases + partial_progress_in_current) / total
        completed_phases = max(0, self.current_phase - 1)
        
        # Assume each phase takes roughly equal sessions
        # This is a simplification; could be made more sophisticated
        return (completed_phases / self.total_phases) * 100.0
    
    def advance_to_next_phase(self) -> bool:
        """
        Advance to next phase.
        
        Returns: True if advanced, False if already at last phase
        """
        if self.total_phases and self.current_phase < self.total_phases:
            self.current_phase += 1
            self.sessions_in_current_phase = 0
            return True
        return False
    
    def complete_journey(self) -> None:
        """Mark journey as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
    
    def pause_journey(self) -> None:
        """Pause journey."""
        self.status = "paused"
        self.paused_at = datetime.utcnow()
    
    def resume_journey(self) -> None:
        """Resume paused journey."""
        if self.status == "paused":
            self.status = "in_progress"
            self.paused_at = None
    
    def is_goal_met(self, metric_name: str) -> bool:
        """Check if a specific goal is met."""
        if not self.success_criteria_met:
            return False
        
        goal_key = f"{metric_name}_goal_met"
        return self.success_criteria_met.get(goal_key, False)
    
    def calculate_improvement(self, metric_name: str) -> Optional[float]:
        """Calculate improvement for a specific metric."""
        if not self.baseline_metrics or not self.current_metrics:
            return None
        
        baseline = self.baseline_metrics.get(metric_name)
        current = self.current_metrics.get(metric_name)
        
        if baseline is None or current is None:
            return None
        
        return current - baseline
