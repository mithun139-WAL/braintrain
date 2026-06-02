"""
Escalation policy for handling complex scenarios.
"""
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import logging

from app.ai.orchestrators.contracts.interview_contracts import InterviewPhase
from app.ai.orchestrators.contracts.turn_contracts import AnswerQuality

logger = logging.getLogger(__name__)


class EscalationTrigger(str, Enum):
    """Triggers that can cause escalation."""
    CANDIDATE_STUCK = "candidate_stuck"
    REPEATED_CONFUSION = "repeated_confusion"
    OFF_TOPIC_PATTERN = "off_topic_pattern"
    CONTRADICTIONS = "contradictions"
    TECHNICAL_DEPTH_INSUFFICIENT = "technical_depth_insufficient"
    SAFETY_CONCERN = "safety_concern"
    SYSTEM_ERROR = "system_error"
    LATENCY_VIOLATION = "latency_violation"


class EscalationAction(str, Enum):
    """Actions to take when escalation is triggered."""
    SIMPLIFY_QUESTION = "simplify_question"
    PROVIDE_HINT = "provide_hint"
    MOVE_TO_EASIER_TOPIC = "move_to_easier_topic"
    SKIP_TO_NEXT_PHASE = "skip_to_next_phase"
    USE_FALLBACK_MODEL = "use_fallback_model"
    ENABLE_DEGRADED_MODE = "enable_degraded_mode"
    NOTIFY_HUMAN_REVIEWER = "notify_human_reviewer"
    TERMINATE_INTERVIEW = "terminate_interview"


class EscalationRule(BaseModel):
    """Rule for escalation detection and action."""
    
    rule_name: str
    trigger: EscalationTrigger
    
    # Detection thresholds
    consecutive_occurrences: int = 3
    total_occurrences: int = 5
    time_window_seconds: int = 300
    
    # Actions
    primary_action: EscalationAction
    fallback_action: Optional[EscalationAction] = None
    
    # Severity
    severity: str = "medium"  # low, medium, high, critical
    notify_on_trigger: bool = False
    
    # Phase-specific
    applicable_phases: List[InterviewPhase] = Field(default_factory=list)


class EscalationPolicy(BaseModel):
    """Policy for handling escalation scenarios."""
    
    policy_name: str = "default_escalation"
    enabled: bool = True
    
    # Candidate struggling rules
    candidate_stuck_rule: EscalationRule = Field(
        default_factory=lambda: EscalationRule(
            rule_name="candidate_stuck",
            trigger=EscalationTrigger.CANDIDATE_STUCK,
            consecutive_occurrences=2,
            primary_action=EscalationAction.PROVIDE_HINT,
            fallback_action=EscalationAction.SIMPLIFY_QUESTION,
            severity="medium"
        )
    )
    
    repeated_confusion_rule: EscalationRule = Field(
        default_factory=lambda: EscalationRule(
            rule_name="repeated_confusion",
            trigger=EscalationTrigger.REPEATED_CONFUSION,
            consecutive_occurrences=3,
            primary_action=EscalationAction.SIMPLIFY_QUESTION,
            fallback_action=EscalationAction.MOVE_TO_EASIER_TOPIC,
            severity="medium"
        )
    )
    
    off_topic_pattern_rule: EscalationRule = Field(
        default_factory=lambda: EscalationRule(
            rule_name="off_topic_pattern",
            trigger=EscalationTrigger.OFF_TOPIC_PATTERN,
            consecutive_occurrences=2,
            total_occurrences=4,
            primary_action=EscalationAction.MOVE_TO_EASIER_TOPIC,
            severity="low"
        )
    )
    
    contradictions_rule: EscalationRule = Field(
        default_factory=lambda: EscalationRule(
            rule_name="contradictions",
            trigger=EscalationTrigger.CONTRADICTIONS,
            total_occurrences=3,
            primary_action=EscalationAction.NOTIFY_HUMAN_REVIEWER,
            severity="high",
            notify_on_trigger=True
        )
    )
    
    insufficient_depth_rule: EscalationRule = Field(
        default_factory=lambda: EscalationRule(
            rule_name="insufficient_depth",
            trigger=EscalationTrigger.TECHNICAL_DEPTH_INSUFFICIENT,
            consecutive_occurrences=3,
            primary_action=EscalationAction.MOVE_TO_EASIER_TOPIC,
            fallback_action=EscalationAction.SKIP_TO_NEXT_PHASE,
            severity="medium",
            applicable_phases=[
                InterviewPhase.TECHNICAL_ROUND_1,
                InterviewPhase.TECHNICAL_ROUND_2
            ]
        )
    )
    
    # System issue rules
    system_error_rule: EscalationRule = Field(
        default_factory=lambda: EscalationRule(
            rule_name="system_error",
            trigger=EscalationTrigger.SYSTEM_ERROR,
            consecutive_occurrences=1,
            primary_action=EscalationAction.USE_FALLBACK_MODEL,
            fallback_action=EscalationAction.ENABLE_DEGRADED_MODE,
            severity="high",
            notify_on_trigger=True
        )
    )
    
    latency_violation_rule: EscalationRule = Field(
        default_factory=lambda: EscalationRule(
            rule_name="latency_violation",
            trigger=EscalationTrigger.LATENCY_VIOLATION,
            consecutive_occurrences=2,
            primary_action=EscalationAction.USE_FALLBACK_MODEL,
            severity="medium"
        )
    )
    
    # Safety rules
    safety_concern_rule: EscalationRule = Field(
        default_factory=lambda: EscalationRule(
            rule_name="safety_concern",
            trigger=EscalationTrigger.SAFETY_CONCERN,
            consecutive_occurrences=1,
            primary_action=EscalationAction.TERMINATE_INTERVIEW,
            severity="critical",
            notify_on_trigger=True
        )
    )
    
    def get_rule(self, trigger: EscalationTrigger) -> Optional[EscalationRule]:
        """Get escalation rule for a specific trigger."""
        rules = {
            EscalationTrigger.CANDIDATE_STUCK: self.candidate_stuck_rule,
            EscalationTrigger.REPEATED_CONFUSION: self.repeated_confusion_rule,
            EscalationTrigger.OFF_TOPIC_PATTERN: self.off_topic_pattern_rule,
            EscalationTrigger.CONTRADICTIONS: self.contradictions_rule,
            EscalationTrigger.TECHNICAL_DEPTH_INSUFFICIENT: self.insufficient_depth_rule,
            EscalationTrigger.SYSTEM_ERROR: self.system_error_rule,
            EscalationTrigger.LATENCY_VIOLATION: self.latency_violation_rule,
            EscalationTrigger.SAFETY_CONCERN: self.safety_concern_rule,
        }
        return rules.get(trigger)
    
    def should_escalate(
        self,
        trigger: EscalationTrigger,
        consecutive_count: int,
        total_count: int,
        current_phase: InterviewPhase
    ) -> tuple[bool, Optional[EscalationAction]]:
        """
        Determine if escalation should occur.
        
        Returns:
            (should_escalate, action_to_take)
        """
        rule = self.get_rule(trigger)
        if not rule:
            return False, None
        
        # Check phase applicability
        if rule.applicable_phases and current_phase not in rule.applicable_phases:
            return False, None
        
        # Check consecutive threshold
        if consecutive_count >= rule.consecutive_occurrences:
            return True, rule.primary_action
        
        # Check total threshold
        if total_count >= rule.total_occurrences:
            return True, rule.primary_action
        
        return False, None


class EscalationTracker(BaseModel):
    """Tracks escalation events during an interview."""
    
    session_id: str
    
    # Occurrence tracking
    trigger_counts: Dict[str, int] = Field(default_factory=dict)
    consecutive_counts: Dict[str, int] = Field(default_factory=dict)
    
    # Action history
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timestamps
    last_trigger_time: Dict[str, float] = Field(default_factory=dict)
    
    def record_trigger(self, trigger: EscalationTrigger, timestamp: float) -> None:
        """Record an escalation trigger event."""
        trigger_key = trigger.value
        
        # Update total count
        self.trigger_counts[trigger_key] = self.trigger_counts.get(trigger_key, 0) + 1
        
        # Update consecutive count
        last_time = self.last_trigger_time.get(trigger_key, 0)
        if timestamp - last_time < 60:  # Within 60 seconds = consecutive
            self.consecutive_counts[trigger_key] = self.consecutive_counts.get(trigger_key, 0) + 1
        else:
            self.consecutive_counts[trigger_key] = 1
        
        # Update timestamp
        self.last_trigger_time[trigger_key] = timestamp
    
    def record_action(
        self,
        trigger: EscalationTrigger,
        action: EscalationAction,
        timestamp: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record an escalation action taken."""
        self.actions_taken.append({
            "trigger": trigger.value,
            "action": action.value,
            "timestamp": timestamp,
            "metadata": metadata or {}
        })
    
    def get_consecutive_count(self, trigger: EscalationTrigger) -> int:
        """Get consecutive count for a trigger."""
        return self.consecutive_counts.get(trigger.value, 0)
    
    def get_total_count(self, trigger: EscalationTrigger) -> int:
        """Get total count for a trigger."""
        return self.trigger_counts.get(trigger.value, 0)
    
    def reset_consecutive(self, trigger: EscalationTrigger) -> None:
        """Reset consecutive count for a trigger."""
        self.consecutive_counts[trigger.value] = 0


def detect_candidate_stuck(answer_quality: AnswerQuality, previous_qualities: List[AnswerQuality]) -> bool:
    """Detect if candidate is stuck."""
    stuck_qualities = [
        AnswerQuality.INSUFFICIENT,
        AnswerQuality.PARTIAL,
        AnswerQuality.VAGUE
    ]
    
    if answer_quality in stuck_qualities:
        recent_stuck = sum(1 for q in previous_qualities[-3:] if q in stuck_qualities)
        return recent_stuck >= 2
    
    return False


def detect_repeated_confusion(answer_quality: AnswerQuality, previous_qualities: List[AnswerQuality]) -> bool:
    """Detect repeated confusion pattern."""
    confusion_qualities = [
        AnswerQuality.OFF_TOPIC,
        AnswerQuality.VAGUE,
        AnswerQuality.CONTRADICTORY
    ]
    
    if answer_quality in confusion_qualities:
        recent_confused = sum(1 for q in previous_qualities[-3:] if q in confusion_qualities)
        return recent_confused >= 2
    
    return False


def detect_off_topic_pattern(answer_quality: AnswerQuality, previous_qualities: List[AnswerQuality]) -> bool:
    """Detect pattern of off-topic answers."""
    if answer_quality == AnswerQuality.OFF_TOPIC:
        recent_off_topic = sum(1 for q in previous_qualities[-4:] if q == AnswerQuality.OFF_TOPIC)
        return recent_off_topic >= 2
    
    return False


def detect_insufficient_depth(answer_quality: AnswerQuality, previous_qualities: List[AnswerQuality]) -> bool:
    """Detect insufficient technical depth."""
    shallow_qualities = [
        AnswerQuality.PARTIAL,
        AnswerQuality.VAGUE,
        AnswerQuality.INSUFFICIENT
    ]
    
    if answer_quality in shallow_qualities:
        recent_shallow = sum(1 for q in previous_qualities[-4:] if q in shallow_qualities)
        return recent_shallow >= 3
    
    return False
