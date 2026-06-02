"""
Evaluation Rules Engine.

Implements rule-based deterministic evaluation metrics:
- Filler word counting
- Hesitation detection
- STAR structure detection
- Ownership language detection
- Quantified impact detection
- Communication stability metrics
"""
from typing import Dict, Any, List
import logging
import re

from app.ai.intelligence.rules.rule_engine import (
    RuleEngine, Rule, RuleType, RuleSeverity, RuleViolation
)

logger = logging.getLogger(__name__)


# Linguistic pattern definitions
FILLER_WORDS = {
    "um", "uh", "like", "you know", "so", "kind of", "sort of",
    "basically", "actually", "literally", "right", "i mean",
    "well", "hmm", "erm", "ah"
}

HESITATION_PATTERNS = [
    r"\b(i think|maybe|probably|possibly|perhaps|i guess|i believe)\b",
    r"\b(not sure|uncertain|unclear|don't know)\b",
    r"\.\.\.",  # Ellipsis
    r"--",  # Em dash indicating pause
]

OWNERSHIP_PHRASES = [
    r"\bi (led|owned|drove|managed|built|created|designed|implemented)\b",
    r"\bmy (team|project|initiative|decision|responsibility)\b",
    r"\bi was responsible for",
    r"\bi took ownership",
    r"\bi decided to"
]

QUANTIFIED_IMPACT_PATTERNS = [
    r"\d+%",  # Percentages
    r"\$[\d,]+",  # Dollar amounts
    r"\b\d+[xX]\b",  # Multipliers (e.g., 3x faster)
    r"\b\d+\s*(users|customers|requests|transactions|minutes|hours|days)\b",
    r"\b(increased|reduced|improved|decreased)\s+\w+\s+by\s+\d+",
]

STAR_INDICATORS = {
    "situation": [
        r"\b(when|while|during|at the time|back when)\b",
        r"\b(situation|context|background|scenario)\b",
    ],
    "task": [
        r"\b(needed to|had to|was tasked|my goal|objective|challenge)\b",
        r"\b(task|responsibility|assignment|mission)\b",
    ],
    "action": [
        r"\b(i (did|took|implemented|built|designed|created|developed))\b",
        r"\b(my approach|i decided|i chose|i started)\b",
    ],
    "result": [
        r"\b(resulted in|outcome|impact|ended up|finally|ultimately)\b",
        r"\b(achieved|accomplished|delivered|shipped)\b",
    ]
}

CONFIDENCE_UNDERMINING_PHRASES = [
    r"\bi'm not an expert",
    r"\bi might be wrong",
    r"\bi could be mistaken",
    r"\bi'm not entirely sure",
    r"\bdon't quote me on"
]


class EvaluationRuleEngine(RuleEngine):
    """
    Rule-based evaluation engine for deterministic scoring.
    
    Computes metrics based on linguistic patterns and structure,
    not subjective LLM interpretation.
    """
    
    def __init__(self):
        super().__init__()
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register default evaluation rules."""
        
        # Rule: Filler word detection
        self.register_rule(Rule(
            id="filler_word_detection",
            name="Filler Word Detection",
            description="Count filler words to assess communication clarity",
            rule_type=RuleType.EVALUATION,
            severity=RuleSeverity.INFO,
            metadata={"threshold_per_100_words": 5}
        ))
        
        # Rule: Hesitation detection
        self.register_rule(Rule(
            id="hesitation_detection",
            name="Hesitation Detection",
            description="Detect hesitation patterns indicating uncertainty",
            rule_type=RuleType.EVALUATION,
            severity=RuleSeverity.INFO,
            metadata={}
        ))
        
        # Rule: STAR structure detection
        self.register_rule(Rule(
            id="star_structure_detection",
            name="STAR Structure Detection",
            description="Detect if behavioral answer follows STAR methodology",
            rule_type=RuleType.EVALUATION,
            severity=RuleSeverity.INFO,
            metadata={"min_components": 3}  # Need at least 3 of 4 STAR components
        ))
        
        # Rule: Ownership language detection
        self.register_rule(Rule(
            id="ownership_detection",
            name="Ownership Language Detection",
            description="Detect ownership language (I vs we, taking responsibility)",
            rule_type=RuleType.EVALUATION,
            severity=RuleSeverity.INFO,
            metadata={}
        ))
        
        # Rule: Quantified impact detection
        self.register_rule(Rule(
            id="quantified_impact_detection",
            name="Quantified Impact Detection",
            description="Detect quantified metrics and impact statements",
            rule_type=RuleType.EVALUATION,
            severity=RuleSeverity.INFO,
            metadata={}
        ))
        
        # Rule: Communication stability
        self.register_rule(Rule(
            id="communication_stability",
            name="Communication Stability",
            description="Assess consistency and stability of communication patterns",
            rule_type=RuleType.EVALUATION,
            severity=RuleSeverity.INFO,
            metadata={}
        ))
    
    def evaluate_rule(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """Evaluate an evaluation rule and return metrics."""
        self._rule_execution_count[rule.id] += 1
        
        if rule.id == "filler_word_detection":
            return self._detect_filler_words(rule, context)
        elif rule.id == "hesitation_detection":
            return self._detect_hesitation(rule, context)
        elif rule.id == "star_structure_detection":
            return self._detect_star_structure(rule, context)
        elif rule.id == "ownership_detection":
            return self._detect_ownership(rule, context)
        elif rule.id == "quantified_impact_detection":
            return self._detect_quantified_impact(rule, context)
        elif rule.id == "communication_stability":
            return self._assess_communication_stability(rule, context)
        else:
            return super().evaluate_rule(rule, context)
    
    def _detect_filler_words(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Count filler words in response.
        
        Context should contain:
        - candidate_response: str
        """
        response = context.get("candidate_response", "")
        response_lower = response.lower()
        
        # Count filler words
        filler_count = sum(
            response_lower.count(f" {filler} ") + response_lower.count(f"{filler} ") + response_lower.count(f" {filler}")
            for filler in FILLER_WORDS
        )
        
        # Calculate density (per 100 words)
        word_count = len(response.split())
        filler_density = (filler_count / word_count * 100) if word_count > 0 else 0
        
        threshold = rule.metadata.get("threshold_per_100_words", 5)
        
        return RuleViolation(
            rule=rule,
            violated=filler_density > threshold,
            reason=f"Filler word density: {filler_density:.2f} per 100 words (threshold: {threshold})",
            context={
                "filler_count": filler_count,
                "word_count": word_count,
                "filler_density": filler_density,
                "score": max(0, 100 - (filler_density * 10))  # Score: 100 - (density * 10)
            }
        )
    
    def _detect_hesitation(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Detect hesitation patterns.
        
        Context should contain:
        - candidate_response: str
        """
        response = context.get("candidate_response", "")
        
        # Count hesitation patterns
        hesitation_count = 0
        for pattern in HESITATION_PATTERNS:
            matches = re.findall(pattern, response, re.IGNORECASE)
            hesitation_count += len(matches)
        
        # Calculate hesitation score (0-100, lower is more confident)
        word_count = len(response.split())
        hesitation_density = (hesitation_count / word_count * 100) if word_count > 0 else 0
        confidence_score = max(0, 100 - (hesitation_density * 20))
        
        return RuleViolation(
            rule=rule,
            violated=hesitation_count > 3,
            reason=f"Detected {hesitation_count} hesitation patterns",
            context={
                "hesitation_count": hesitation_count,
                "hesitation_density": hesitation_density,
                "confidence_score": confidence_score
            }
        )
    
    def _detect_star_structure(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Detect STAR structure in behavioral responses.
        
        Context should contain:
        - candidate_response: str
        """
        response = context.get("candidate_response", "")
        
        # Check for each STAR component
        star_components = {}
        for component, patterns in STAR_INDICATORS.items():
            found = any(
                re.search(pattern, response, re.IGNORECASE)
                for pattern in patterns
            )
            star_components[component] = found
        
        components_found = sum(star_components.values())
        min_components = rule.metadata.get("min_components", 3)
        
        has_star = components_found >= min_components
        star_score = (components_found / 4) * 100  # 0-100 score based on components
        
        return RuleViolation(
            rule=rule,
            violated=not has_star,
            reason=f"Found {components_found}/4 STAR components (need {min_components})",
            context={
                "star_components": star_components,
                "components_found": components_found,
                "has_star_structure": has_star,
                "star_score": star_score
            }
        )
    
    def _detect_ownership(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Detect ownership language.
        
        Context should contain:
        - candidate_response: str
        """
        response = context.get("candidate_response", "")
        
        # Count ownership phrases
        ownership_count = 0
        for pattern in OWNERSHIP_PHRASES:
            matches = re.findall(pattern, response, re.IGNORECASE)
            ownership_count += len(matches)
        
        # Count "we" vs "I" usage
        i_count = len(re.findall(r'\bi\b', response, re.IGNORECASE))
        we_count = len(re.findall(r'\bwe\b', response, re.IGNORECASE))
        
        # Ownership ratio (I / (I + we))
        ownership_ratio = i_count / (i_count + we_count) if (i_count + we_count) > 0 else 0
        
        # Ownership score (0-100)
        ownership_score = min(100, (ownership_count * 20) + (ownership_ratio * 50))
        
        return RuleViolation(
            rule=rule,
            violated=ownership_score < 30,
            reason=f"Ownership score: {ownership_score:.1f}/100",
            context={
                "ownership_phrases": ownership_count,
                "i_count": i_count,
                "we_count": we_count,
                "ownership_ratio": ownership_ratio,
                "ownership_score": ownership_score
            }
        )
    
    def _detect_quantified_impact(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Detect quantified impact statements.
        
        Context should contain:
        - candidate_response: str
        """
        response = context.get("candidate_response", "")
        
        # Find quantified metrics
        quantified_matches = []
        for pattern in QUANTIFIED_IMPACT_PATTERNS:
            matches = re.findall(pattern, response, re.IGNORECASE)
            quantified_matches.extend(matches)
        
        quantified_count = len(quantified_matches)
        
        # Calculate impact score
        impact_score = min(100, quantified_count * 30)
        
        return RuleViolation(
            rule=rule,
            violated=quantified_count == 0,
            reason=f"Found {quantified_count} quantified impact statements",
            context={
                "quantified_count": quantified_count,
                "quantified_examples": quantified_matches[:5],  # First 5 examples
                "impact_score": impact_score
            }
        )
    
    def _assess_communication_stability(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Assess communication stability across responses.
        
        Context should contain:
        - recent_responses: list of str
        """
        recent_responses = context.get("recent_responses", [])
        
        if len(recent_responses) < 2:
            return RuleViolation(
                rule=rule,
                violated=False,
                reason="Not enough responses to assess stability",
                context={"stability_score": 100}
            )
        
        # Calculate metrics for each response
        filler_densities = []
        hesitation_counts = []
        
        for response in recent_responses:
            # Filler density
            response_lower = response.lower()
            filler_count = sum(
                response_lower.count(f" {filler} ")
                for filler in FILLER_WORDS
            )
            word_count = len(response.split())
            filler_density = (filler_count / word_count * 100) if word_count > 0 else 0
            filler_densities.append(filler_density)
            
            # Hesitation count
            hesitation = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in HESITATION_PATTERNS
            )
            hesitation_counts.append(hesitation)
        
        # Calculate variance (stability = inverse of variance)
        filler_variance = self._calculate_variance(filler_densities)
        hesitation_variance = self._calculate_variance([float(h) for h in hesitation_counts])
        
        # Stability score (0-100, higher is more stable)
        stability_score = max(0, 100 - (filler_variance * 10 + hesitation_variance * 10))
        
        return RuleViolation(
            rule=rule,
            violated=stability_score < 60,
            reason=f"Communication stability score: {stability_score:.1f}/100",
            context={
                "stability_score": stability_score,
                "filler_variance": filler_variance,
                "hesitation_variance": hesitation_variance
            }
        )
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def compute_all_metrics(self, candidate_response: str, recent_responses: List[str] = None) -> Dict[str, Any]:
        """
        Compute all rule-based metrics for a candidate response.
        
        Returns a comprehensive metrics dictionary.
        """
        if recent_responses is None:
            recent_responses = [candidate_response]
        
        context = {
            "candidate_response": candidate_response,
            "recent_responses": recent_responses
        }
        
        # Evaluate all rules
        violations = self.evaluate_all(context, rule_type=RuleType.EVALUATION)
        
        # Aggregate metrics
        metrics = {
            "filler_word_score": 100,
            "confidence_score": 100,
            "star_score": 0,
            "ownership_score": 0,
            "impact_score": 0,
            "communication_stability_score": 100,
        }
        
        for violation in violations:
            if violation.rule.id == "filler_word_detection":
                metrics["filler_word_score"] = violation.context.get("score", 100)
                metrics["filler_count"] = violation.context.get("filler_count", 0)
            elif violation.rule.id == "hesitation_detection":
                metrics["confidence_score"] = violation.context.get("confidence_score", 100)
                metrics["hesitation_count"] = violation.context.get("hesitation_count", 0)
            elif violation.rule.id == "star_structure_detection":
                metrics["star_score"] = violation.context.get("star_score", 0)
                metrics["star_components"] = violation.context.get("star_components", {})
            elif violation.rule.id == "ownership_detection":
                metrics["ownership_score"] = violation.context.get("ownership_score", 0)
            elif violation.rule.id == "quantified_impact_detection":
                metrics["impact_score"] = violation.context.get("impact_score", 0)
                metrics["quantified_count"] = violation.context.get("quantified_count", 0)
            elif violation.rule.id == "communication_stability":
                metrics["communication_stability_score"] = violation.context.get("stability_score", 100)
        
        return metrics
