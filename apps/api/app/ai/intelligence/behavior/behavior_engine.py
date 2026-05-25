"""
Behavior Engine for controlling interviewer personality and dynamics.

This engine determines how the interviewer should behave based on:
- Company culture (e.g., Amazon's high pressure vs Google's collaborative)
- Candidate performance
- Interview stage
- Configured personality
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PressureLevel(str, Enum):
    """Pressure levels for interviewer behavior."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class PacingSpeed(str, Enum):
    """Pacing speed for question flow."""
    VERY_SLOW = "very_slow"
    SLOW = "slow"
    MODERATE = "moderate"
    FAST = "fast"
    RAPID = "rapid"


class InterviewerPersonality(str, Enum):
    """Interviewer personality archetypes."""
    SUPPORTIVE = "supportive"  # Encouraging, patient
    NEUTRAL = "neutral"  # Standard professional
    CHALLENGING = "challenging"  # Probing, pressure-testing
    COLLABORATIVE = "collaborative"  # Partnership-oriented
    DIRECT = "direct"  # No-nonsense, efficiency-focused


@dataclass
class BehaviorState:
    """Current state of interviewer behavior."""
    pressure_level: PressureLevel
    pacing_speed: PacingSpeed
    personality: InterviewerPersonality
    interruption_enabled: bool
    follow_up_depth: int  # 1-5, how deep to probe
    supportiveness: float  # 0-1, how supportive vs challenging
    
    # Dynamic adjustments based on candidate performance
    escalation_count: int = 0
    recovery_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pressure_level": self.pressure_level.value,
            "pacing_speed": self.pacing_speed.value,
            "personality": self.personality.value,
            "interruption_enabled": self.interruption_enabled,
            "follow_up_depth": self.follow_up_depth,
            "supportiveness": self.supportiveness,
            "escalation_count": self.escalation_count,
            "recovery_mode": self.recovery_mode,
        }


class BehaviorEngine:
    """
    Core behavior engine for interview orchestration.
    
    Responsibilities:
    - Determine appropriate pressure level
    - Control pacing and interruptions
    - Adjust behavior based on candidate performance
    - Implement company-specific interview styles
    """
    
    def __init__(self, initial_state: Optional[BehaviorState] = None):
        self.state = initial_state or self._default_state()
        self._behavior_history: list[Dict[str, Any]] = []
    
    def _default_state(self) -> BehaviorState:
        """Create default behavior state."""
        return BehaviorState(
            pressure_level=PressureLevel.MEDIUM,
            pacing_speed=PacingSpeed.MODERATE,
            personality=InterviewerPersonality.NEUTRAL,
            interruption_enabled=False,
            follow_up_depth=3,
            supportiveness=0.5
        )
    
    def configure_from_company(self, company_name: str) -> None:
        """Configure behavior based on company culture."""
        company_configs = {
            "amazon": BehaviorState(
                pressure_level=PressureLevel.HIGH,
                pacing_speed=PacingSpeed.FAST,
                personality=InterviewerPersonality.CHALLENGING,
                interruption_enabled=True,
                follow_up_depth=5,
                supportiveness=0.3
            ),
            "google": BehaviorState(
                pressure_level=PressureLevel.MEDIUM,
                pacing_speed=PacingSpeed.MODERATE,
                personality=InterviewerPersonality.COLLABORATIVE,
                interruption_enabled=False,
                follow_up_depth=4,
                supportiveness=0.6
            ),
            "meta": BehaviorState(
                pressure_level=PressureLevel.HIGH,
                pacing_speed=PacingSpeed.FAST,
                personality=InterviewerPersonality.DIRECT,
                interruption_enabled=True,
                follow_up_depth=4,
                supportiveness=0.4
            ),
            "netflix": BehaviorState(
                pressure_level=PressureLevel.VERY_HIGH,
                pacing_speed=PacingSpeed.FAST,
                personality=InterviewerPersonality.CHALLENGING,
                interruption_enabled=True,
                follow_up_depth=5,
                supportiveness=0.2
            ),
            "startup": BehaviorState(
                pressure_level=PressureLevel.MEDIUM,
                pacing_speed=PacingSpeed.MODERATE,
                personality=InterviewerPersonality.COLLABORATIVE,
                interruption_enabled=False,
                follow_up_depth=3,
                supportiveness=0.6
            ),
        }
        
        config = company_configs.get(company_name.lower())
        if config:
            self.state = config
            logger.info(f"Configured behavior for {company_name}")
        else:
            logger.warning(f"No behavior config for {company_name}, using default")
    
    def adjust_for_performance(self, performance_score: float, confidence_score: float) -> None:
        """
        Adjust behavior based on candidate performance.
        
        Args:
            performance_score: 0-100, how well candidate is doing
            confidence_score: 0-100, candidate's confidence level
        """
        # If candidate is struggling (low performance + low confidence), be more supportive
        if performance_score < 50 and confidence_score < 50:
            self.state.recovery_mode = True
            self.state.supportiveness = min(1.0, self.state.supportiveness + 0.2)
            self.state.pressure_level = self._decrease_pressure(self.state.pressure_level)
            logger.info("Entering recovery mode due to low performance/confidence")
        
        # If candidate is doing well, can increase pressure
        elif performance_score > 75 and confidence_score > 70:
            self.state.recovery_mode = False
            self.state.pressure_level = self._increase_pressure(self.state.pressure_level)
            self.state.follow_up_depth = min(5, self.state.follow_up_depth + 1)
            logger.info("Increasing pressure due to strong performance")
        
        # Record adjustment
        self._behavior_history.append({
            "performance_score": performance_score,
            "confidence_score": confidence_score,
            "new_state": self.state.to_dict()
        })
    
    def should_interrupt(self, candidate_rambling: bool, turn_count: int) -> bool:
        """
        Determine if interviewer should interrupt candidate.
        
        Args:
            candidate_rambling: Whether candidate is rambling
            turn_count: Current turn number
            
        Returns:
            True if interruption is appropriate
        """
        if not self.state.interruption_enabled:
            return False
        
        if self.state.recovery_mode:
            return False  # Don't interrupt during recovery
        
        # Interrupt if rambling and pressure is high
        if candidate_rambling and self.state.pressure_level in [PressureLevel.HIGH, PressureLevel.VERY_HIGH]:
            return turn_count > 3  # Allow some setup time
        
        return False
    
    def get_follow_up_depth(self) -> int:
        """Get current follow-up depth (1-5)."""
        return self.state.follow_up_depth
    
    def get_behavioral_instructions(self) -> Dict[str, Any]:
        """
        Get behavioral instructions for prompt assembly.
        
        Returns instructions that should be included in the system prompt.
        """
        personality_instructions = {
            InterviewerPersonality.SUPPORTIVE: (
                "Be encouraging and patient. Acknowledge good answers. "
                "Provide hints if candidate struggles. Use positive reinforcement."
            ),
            InterviewerPersonality.NEUTRAL: (
                "Maintain professional demeanor. Be fair and consistent. "
                "Neither overly supportive nor challenging."
            ),
            InterviewerPersonality.CHALLENGING: (
                "Probe deeply on answers. Ask for tradeoffs and alternatives. "
                "Push candidate to defend their choices. Test depth of knowledge."
            ),
            InterviewerPersonality.COLLABORATIVE: (
                "Act as a thought partner. Explore solutions together. "
                "Build on candidate's ideas. Use 'we' language occasionally."
            ),
            InterviewerPersonality.DIRECT: (
                "Be concise and efficient. Get to the point quickly. "
                "Value clear, direct answers. Don't waste time on pleasantries."
            ),
        }
        
        pressure_instructions = {
            PressureLevel.VERY_LOW: "Take your time. No pressure.",
            PressureLevel.LOW: "Comfortable pacing. Allow thinking time.",
            PressureLevel.MEDIUM: "Standard interview pressure. Professional but focused.",
            PressureLevel.HIGH: "Maintain pressure. Expect quick responses. Probe uncertainties.",
            PressureLevel.VERY_HIGH: "High pressure environment. Quick decisions. Deep scrutiny.",
        }
        
        return {
            "personality": self.state.personality.value,
            "personality_instruction": personality_instructions[self.state.personality],
            "pressure_level": self.state.pressure_level.value,
            "pressure_instruction": pressure_instructions[self.state.pressure_level],
            "pacing_speed": self.state.pacing_speed.value,
            "interruption_enabled": self.state.interruption_enabled,
            "follow_up_depth": self.state.follow_up_depth,
            "supportiveness": self.state.supportiveness,
            "recovery_mode": self.state.recovery_mode,
        }
    
    def _increase_pressure(self, current: PressureLevel) -> PressureLevel:
        """Increase pressure level by one step."""
        levels = list(PressureLevel)
        idx = levels.index(current)
        return levels[min(idx + 1, len(levels) - 1)]
    
    def _decrease_pressure(self, current: PressureLevel) -> PressureLevel:
        """Decrease pressure level by one step."""
        levels = list(PressureLevel)
        idx = levels.index(current)
        return levels[max(idx - 1, 0)]
    
    def reset_to_default(self) -> None:
        """Reset behavior to default state."""
        self.state = self._default_state()
        logger.info("Behavior reset to default")
