"""
Realism Rules Engine.

Ensures interview behavior is realistic:
- One question at a time
- Appropriate pacing
- Natural conversation flow
- Realistic follow-up depth
- Believable interviewer behavior
"""
from typing import Dict, Any
import logging
import re

from app.ai.intelligence.rules.rule_engine import (
    RuleEngine, Rule, RuleType, RuleSeverity, RuleViolation
)

logger = logging.getLogger(__name__)


class RealismRuleEngine(RuleEngine):
    """
    Specialized rule engine for enforcing realistic interview behavior.
    
    Prevents:
    - Multiple questions at once
    - Unrealistic rapid-fire questioning
    - Inappropriate interruptions
    - Unnatural conversation patterns
    """
    
    def __init__(self):
        super().__init__()
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register default realism rules."""
        
        # Rule: One question at a time
        self.register_rule(Rule(
            id="one_question_at_time",
            name="One Question at a Time",
            description="Ask only one question per turn, not multiple questions",
            rule_type=RuleType.REALISM,
            severity=RuleSeverity.BLOCKER,
            metadata={"max_questions": 1}
        ))
        
        # Rule: Allow recovery after uncertainty
        self.register_rule(Rule(
            id="allow_recovery",
            name="Allow Recovery After Uncertainty",
            description="Give candidates space to recover after showing uncertainty",
            rule_type=RuleType.REALISM,
            severity=RuleSeverity.WARNING,
            metadata={}
        ))
        
        # Rule: Realistic pacing
        self.register_rule(Rule(
            id="realistic_pacing",
            name="Realistic Pacing",
            description="Maintain realistic conversation pacing, not too rapid",
            rule_type=RuleType.REALISM,
            severity=RuleSeverity.WARNING,
            metadata={
                "min_turn_interval_seconds": 2,
                "max_questions_per_minute": 4
            }
        ))
        
        # Rule: No aggressive interruption loops
        self.register_rule(Rule(
            id="no_aggressive_interruption",
            name="No Aggressive Interruption",
            description="Avoid aggressive interruption patterns that feel unrealistic",
            rule_type=RuleType.REALISM,
            severity=RuleSeverity.WARNING,
            metadata={"max_interruptions_per_5_turns": 2}
        ))
        
        # Rule: Natural acknowledgment
        self.register_rule(Rule(
            id="natural_acknowledgment",
            name="Natural Acknowledgment",
            description="Acknowledge candidate responses naturally before follow-ups",
            rule_type=RuleType.REALISM,
            severity=RuleSeverity.WARNING,
            metadata={}
        ))
        
        # Rule: Appropriate question length
        self.register_rule(Rule(
            id="appropriate_question_length",
            name="Appropriate Question Length",
            description="Questions should be concise, not overly long or complex",
            rule_type=RuleType.REALISM,
            severity=RuleSeverity.WARNING,
            metadata={
                "max_words": 50,
                "max_sentences": 3
            }
        ))
    
    def evaluate_rule(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """Evaluate a realism rule against context."""
        self._rule_execution_count[rule.id] += 1
        
        if rule.id == "one_question_at_time":
            return self._check_one_question(rule, context)
        elif rule.id == "allow_recovery":
            return self._check_allow_recovery(rule, context)
        elif rule.id == "realistic_pacing":
            return self._check_realistic_pacing(rule, context)
        elif rule.id == "no_aggressive_interruption":
            return self._check_no_aggressive_interruption(rule, context)
        elif rule.id == "natural_acknowledgment":
            return self._check_natural_acknowledgment(rule, context)
        elif rule.id == "appropriate_question_length":
            return self._check_appropriate_length(rule, context)
        else:
            return super().evaluate_rule(rule, context)
    
    def _check_one_question(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Check if generated response contains only one question.
        
        Context should contain:
        - generated_question: str
        """
        generated_question = context.get("generated_question", "")
        
        # Count question marks
        question_count = generated_question.count('?')
        
        max_questions = rule.metadata.get("max_questions", 1)
        
        if question_count > max_questions:
            violation = RuleViolation(
                rule=rule,
                violated=True,
                reason=f"Generated response contains {question_count} questions (max: {max_questions})",
                context={"question_count": question_count}
            )
            self._rule_violation_count[rule.id] += 1
            return violation
        
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="Generated response contains appropriate number of questions",
            context={"question_count": question_count}
        )
    
    def _check_allow_recovery(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Check if interviewer gives candidate space to recover after uncertainty.
        
        Context should contain:
        - candidate_last_response: str
        - generated_followup: str
        - candidate_confidence_score: float (0-1)
        """
        candidate_response = context.get("candidate_last_response", "")
        generated_followup = context.get("generated_followup", "")
        confidence_score = context.get("candidate_confidence_score", 1.0)
        
        # Detect uncertainty indicators
        uncertainty_indicators = [
            "i think", "maybe", "probably", "not sure", "i'm not certain",
            "i believe", "if i remember", "i guess", "possibly"
        ]
        
        response_lower = candidate_response.lower()
        shows_uncertainty = any(ind in response_lower for ind in uncertainty_indicators)
        shows_uncertainty = shows_uncertainty or confidence_score < 0.5
        
        if shows_uncertainty:
            # Check if followup is supportive/recovery-oriented
            recovery_patterns = [
                r"that's (okay|fine|alright)",
                r"let me (rephrase|clarify)",
                r"or would you like",
                r"take your time",
                r"no worries"
            ]
            
            is_supportive = any(
                re.search(pattern, generated_followup.lower()) 
                for pattern in recovery_patterns
            )
            
            # Check if it's too aggressive
            aggressive_patterns = [
                r"but you should know",
                r"that's incorrect",
                r"actually",
                r"you must"
            ]
            
            is_aggressive = any(
                re.search(pattern, generated_followup.lower())
                for pattern in aggressive_patterns
            )
            
            if is_aggressive and not is_supportive:
                violation = RuleViolation(
                    rule=rule,
                    violated=True,
                    reason="Followup is aggressive after candidate showed uncertainty",
                    context={"confidence_score": confidence_score}
                )
                self._rule_violation_count[rule.id] += 1
                return violation
        
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="Recovery handling is appropriate",
            context={}
        )
    
    def _check_realistic_pacing(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Check if question pacing is realistic.
        
        Context should contain:
        - recent_turn_timestamps: list of timestamps
        - turn_count_last_minute: int
        """
        turn_count = context.get("turn_count_last_minute", 0)
        max_per_minute = rule.metadata.get("max_questions_per_minute", 4)
        
        if turn_count > max_per_minute:
            violation = RuleViolation(
                rule=rule,
                violated=True,
                reason=f"Too many questions in last minute: {turn_count} (max: {max_per_minute})",
                context={"turn_count_last_minute": turn_count}
            )
            self._rule_violation_count[rule.id] += 1
            return violation
        
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="Question pacing is realistic",
            context={"turn_count_last_minute": turn_count}
        )
    
    def _check_no_aggressive_interruption(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Check if interruption patterns are reasonable.
        
        Context should contain:
        - interruption_count_last_5_turns: int
        """
        interruption_count = context.get("interruption_count_last_5_turns", 0)
        max_interruptions = rule.metadata.get("max_interruptions_per_5_turns", 2)
        
        if interruption_count > max_interruptions:
            violation = RuleViolation(
                rule=rule,
                violated=True,
                reason=f"Too many interruptions: {interruption_count} in last 5 turns (max: {max_interruptions})",
                context={"interruption_count": interruption_count}
            )
            self._rule_violation_count[rule.id] += 1
            return violation
        
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="Interruption patterns are reasonable",
            context={"interruption_count": interruption_count}
        )
    
    def _check_natural_acknowledgment(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Check if generated followup includes natural acknowledgment.
        
        Context should contain:
        - generated_followup: str
        - is_followup: bool
        """
        generated_followup = context.get("generated_followup", "")
        is_followup = context.get("is_followup", False)
        
        if not is_followup:
            return RuleViolation(
                rule=rule,
                violated=False,
                reason="Not a followup question",
                context={}
            )
        
        # Check for acknowledgment patterns
        acknowledgment_patterns = [
            r"^(okay|alright|good|great|i see|understood|right)",
            r"^(thanks|thank you)",
            r"^(that's \w+)",
            r"makes sense"
        ]
        
        has_acknowledgment = any(
            re.search(pattern, generated_followup.lower().strip())
            for pattern in acknowledgment_patterns
        )
        
        if not has_acknowledgment:
            return RuleViolation(
                rule=rule,
                violated=True,
                reason="Followup lacks natural acknowledgment",
                context={}
            )
        
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="Followup includes natural acknowledgment",
            context={}
        )
    
    def _check_appropriate_length(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Check if question length is appropriate.
        
        Context should contain:
        - generated_question: str
        """
        generated_question = context.get("generated_question", "")
        
        word_count = len(generated_question.split())
        sentence_count = len([s for s in generated_question.split('.') if s.strip()])
        
        max_words = rule.metadata.get("max_words", 50)
        max_sentences = rule.metadata.get("max_sentences", 3)
        
        if word_count > max_words:
            violation = RuleViolation(
                rule=rule,
                violated=True,
                reason=f"Question too long: {word_count} words (max: {max_words})",
                context={"word_count": word_count, "sentence_count": sentence_count}
            )
            self._rule_violation_count[rule.id] += 1
            return violation
        
        if sentence_count > max_sentences:
            violation = RuleViolation(
                rule=rule,
                violated=True,
                reason=f"Question too complex: {sentence_count} sentences (max: {max_sentences})",
                context={"word_count": word_count, "sentence_count": sentence_count}
            )
            self._rule_violation_count[rule.id] += 1
            return violation
        
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="Question length is appropriate",
            context={"word_count": word_count, "sentence_count": sentence_count}
        )
