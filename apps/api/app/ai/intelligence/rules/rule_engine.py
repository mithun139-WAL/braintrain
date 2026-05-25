"""
Core Rule Engine for deterministic interview behavior.

This engine enforces interview rules independently of LLM behavior,
ensuring consistent, realistic, and hallucination-free interviews.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class RuleType(str, Enum):
    """Types of interview rules."""
    HALLUCINATION = "hallucination"
    TOPIC_BOUNDARY = "topic_boundary"
    BEHAVIORAL = "behavioral"
    SCOPE = "scope"
    EVALUATION = "evaluation"
    REALISM = "realism"


class RuleSeverity(str, Enum):
    """Severity levels for rule violations."""
    BLOCKER = "blocker"  # Must prevent action
    WARNING = "warning"  # Log but allow
    INFO = "info"  # Informational only


@dataclass
class Rule:
    """
    A single interview rule.
    
    Rules define constraints that the system must enforce
    regardless of LLM output.
    """
    id: str
    name: str
    description: str
    rule_type: RuleType
    severity: RuleSeverity
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RuleViolation:
    """Result of a rule check."""
    rule: Rule
    violated: bool
    reason: str
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


class RuleEngine:
    """
    Core rule engine for interview orchestration.
    
    Responsibilities:
    - Load and manage interview rules
    - Evaluate contexts against rules
    - Block or warn on violations
    - Track rule execution metrics
    """
    
    def __init__(self):
        self.rules: Dict[str, Rule] = {}
        self._rule_execution_count: Dict[str, int] = {}
        self._rule_violation_count: Dict[str, int] = {}
    
    def register_rule(self, rule: Rule) -> None:
        """Register a new rule in the engine."""
        self.rules[rule.id] = rule
        self._rule_execution_count[rule.id] = 0
        self._rule_violation_count[rule.id] = 0
        logger.info(f"Registered rule: {rule.id} ({rule.rule_type.value})")
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID."""
        return self.rules.get(rule_id)
    
    def get_rules_by_type(self, rule_type: RuleType) -> List[Rule]:
        """Get all rules of a specific type."""
        return [rule for rule in self.rules.values() if rule.rule_type == rule_type and rule.enabled]
    
    def evaluate_rule(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Evaluate a single rule against a context.
        
        This method should be overridden by specialized rule engines
        (e.g., HallucinationRuleEngine, TopicBoundaryRuleEngine).
        
        Args:
            rule: The rule to evaluate
            context: Context data for evaluation
            
        Returns:
            RuleViolation indicating whether the rule was violated
        """
        self._rule_execution_count[rule.id] += 1
        
        # Base implementation - override in subclasses
        violation = RuleViolation(
            rule=rule,
            violated=False,
            reason="Base rule engine - no violation logic",
            context=context
        )
        
        if violation.violated:
            self._rule_violation_count[rule.id] += 1
        
        return violation
    
    def evaluate_all(self, context: Dict[str, Any], rule_type: Optional[RuleType] = None) -> List[RuleViolation]:
        """
        Evaluate all rules (or rules of a specific type) against a context.
        
        Args:
            context: Context data for evaluation
            rule_type: Optional filter for rule type
            
        Returns:
            List of RuleViolation objects
        """
        rules_to_evaluate = (
            self.get_rules_by_type(rule_type) if rule_type 
            else [r for r in self.rules.values() if r.enabled]
        )
        
        violations = []
        for rule in rules_to_evaluate:
            try:
                violation = self.evaluate_rule(rule, context)
                violations.append(violation)
                
                if violation.violated and violation.rule.severity == RuleSeverity.BLOCKER:
                    logger.warning(
                        f"BLOCKER violation: {rule.id} - {violation.reason}",
                        extra={"context": context}
                    )
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {str(e)}", exc_info=True)
        
        return violations
    
    def has_blocker_violations(self, violations: List[RuleViolation]) -> bool:
        """Check if any violations are blockers."""
        return any(
            v.violated and v.rule.severity == RuleSeverity.BLOCKER 
            for v in violations
        )
    
    def get_blocker_violations(self, violations: List[RuleViolation]) -> List[RuleViolation]:
        """Get only blocker violations from a list."""
        return [
            v for v in violations 
            if v.violated and v.rule.severity == RuleSeverity.BLOCKER
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get rule engine metrics."""
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules.values() if r.enabled]),
            "rule_execution_count": self._rule_execution_count.copy(),
            "rule_violation_count": self._rule_violation_count.copy(),
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics counters."""
        for rule_id in self.rules.keys():
            self._rule_execution_count[rule_id] = 0
            self._rule_violation_count[rule_id] = 0
        logger.info("Rule engine metrics reset")
