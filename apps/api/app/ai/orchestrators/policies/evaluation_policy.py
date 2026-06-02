"""
Evaluation policy for combining rule-based and LLM-based scoring.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import logging

from app.ai.orchestrators.contracts.evaluation_contracts import (
    RuleBasedMetrics,
    LLMBasedMetrics,
    UnifiedEvaluation,
    EvaluationWeights
)
from app.ai.orchestrators.contracts.interview_contracts import InterviewPhase, InterviewDomain

logger = logging.getLogger(__name__)


class EvaluationPolicy(BaseModel):
    """
    Policy for evaluation scoring and weighting.
    
    Key principle: Rule-based evaluation is primary (60%), LLM is secondary (40%).
    This prevents hallucinated scores and ensures deterministic evaluation.
    """
    
    policy_name: str = "default_evaluation"
    
    # Global weights
    rule_based_weight: float = 0.6
    llm_based_weight: float = 0.4
    
    # Phase-specific weights
    phase_weights: Dict[str, EvaluationWeights] = Field(default_factory=dict)
    
    # Domain-specific weights
    domain_weights: Dict[str, EvaluationWeights] = Field(default_factory=dict)
    
    # Minimum acceptable scores
    min_acceptable_technical_accuracy: float = 0.4
    min_acceptable_depth: float = 0.3
    min_acceptable_confidence: float = 0.3
    
    # Quality thresholds for answer quality classification
    excellent_threshold: float = 85.0
    good_threshold: float = 70.0
    satisfactory_threshold: float = 55.0
    partial_threshold: float = 40.0
    
    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_phase_weights()
        self._initialize_domain_weights()
    
    def _initialize_phase_weights(self) -> None:
        """Initialize phase-specific evaluation weights."""
        self.phase_weights = {
            InterviewPhase.INTRODUCTION.value: EvaluationWeights(
                technical_accuracy=0.2,
                depth=0.1,
                problem_solving=0.1,
                communication=0.4,
                confidence=0.2
            ),
            InterviewPhase.RESUME_DISCUSSION.value: EvaluationWeights(
                technical_accuracy=0.25,
                depth=0.2,
                problem_solving=0.15,
                communication=0.25,
                confidence=0.15
            ),
            InterviewPhase.TECHNICAL_ROUND_1.value: EvaluationWeights(
                technical_accuracy=0.35,
                depth=0.25,
                problem_solving=0.25,
                communication=0.1,
                confidence=0.05
            ),
            InterviewPhase.TECHNICAL_ROUND_2.value: EvaluationWeights(
                technical_accuracy=0.4,
                depth=0.3,
                problem_solving=0.25,
                communication=0.05,
                confidence=0.0
            ),
            InterviewPhase.SYSTEM_DESIGN.value: EvaluationWeights(
                technical_accuracy=0.3,
                depth=0.25,
                problem_solving=0.35,
                communication=0.1,
                confidence=0.0
            ),
            InterviewPhase.BEHAVIORAL.value: EvaluationWeights(
                technical_accuracy=0.0,
                depth=0.2,
                problem_solving=0.3,
                communication=0.35,
                confidence=0.15
            ),
            InterviewPhase.WRAP_UP.value: EvaluationWeights(
                technical_accuracy=0.0,
                depth=0.0,
                problem_solving=0.0,
                communication=0.7,
                confidence=0.3
            )
        }
    
    def _initialize_domain_weights(self) -> None:
        """Initialize domain-specific evaluation weights."""
        self.domain_weights = {
            InterviewDomain.FRONTEND.value: EvaluationWeights(
                technical_accuracy=0.35,
                depth=0.2,
                problem_solving=0.2,
                communication=0.15,
                confidence=0.1
            ),
            InterviewDomain.BACKEND.value: EvaluationWeights(
                technical_accuracy=0.4,
                depth=0.25,
                problem_solving=0.25,
                communication=0.05,
                confidence=0.05
            ),
            InterviewDomain.FULLSTACK.value: EvaluationWeights(
                technical_accuracy=0.35,
                depth=0.25,
                problem_solving=0.25,
                communication=0.1,
                confidence=0.05
            ),
            InterviewDomain.BEHAVIORAL.value: EvaluationWeights(
                technical_accuracy=0.0,
                depth=0.2,
                problem_solving=0.3,
                communication=0.35,
                confidence=0.15
            )
        }
    
    def get_weights(
        self,
        phase: InterviewPhase,
        domain: Optional[InterviewDomain] = None
    ) -> EvaluationWeights:
        """
        Get evaluation weights for current phase and domain.
        
        Phase weights take precedence over domain weights.
        """
        # Try phase-specific weights first
        phase_key = phase.value
        if phase_key in self.phase_weights:
            return self.phase_weights[phase_key]
        
        # Fall back to domain weights
        if domain:
            domain_key = domain.value
            if domain_key in self.domain_weights:
                return self.domain_weights[domain_key]
        
        # Default weights
        return EvaluationWeights()
    
    def compute_unified_score(
        self,
        rule_based: RuleBasedMetrics,
        llm_based: LLMBasedMetrics,
        weights: EvaluationWeights
    ) -> UnifiedEvaluation:
        """
        Compute unified evaluation score.
        
        Combines rule-based (60%) and LLM-based (40%) metrics.
        """
        
        # Compute rule-based component score
        rule_score = self._compute_rule_based_score(rule_based, weights)
        
        # Compute LLM-based component score
        llm_score = self._compute_llm_based_score(llm_based, weights)
        
        # Weighted combination
        final_score = (
            rule_score * self.rule_based_weight +
            llm_score * self.llm_based_weight
        )
        
        # Determine answer quality classification
        answer_quality = self._classify_answer_quality(final_score)
        
        # Combine all metrics
        evaluation = UnifiedEvaluation(
            final_score=final_score,
            rule_based_score=rule_score,
            llm_based_score=llm_score,
            answer_quality=answer_quality,
            rule_based_metrics=rule_based,
            llm_based_metrics=llm_based,
            weights_used=weights,
            confidence=self._compute_confidence(rule_based, llm_based)
        )
        
        return evaluation
    
    def _compute_rule_based_score(
        self,
        metrics: RuleBasedMetrics,
        weights: EvaluationWeights
    ) -> float:
        """
        Compute rule-based component score.
        
        Rule-based metrics:
        - filler_word_score (0-100)
        - confidence_score (0-100)
        - star_score (0-100)
        - ownership_score (0-100)
        - impact_score (0-100)
        - technical_keyword_coverage (0-1)
        """
        
        # Map rule-based metrics to evaluation dimensions
        communication_score = (
            metrics.filler_word_score * 0.4 +
            metrics.confidence_score * 0.3 +
            (metrics.star_score if metrics.star_score else 70) * 0.3
        )
        
        confidence_dim_score = metrics.confidence_score
        
        # For technical dimensions, use keyword coverage as proxy
        technical_proxy = metrics.technical_keyword_coverage * 100
        
        depth_score = (
            technical_proxy * 0.6 +
            (metrics.star_score if metrics.star_score else 60) * 0.4
        )
        
        problem_solving_score = (
            (metrics.ownership_score if metrics.ownership_score else 60) * 0.4 +
            (metrics.impact_score if metrics.impact_score else 60) * 0.4 +
            technical_proxy * 0.2
        )
        
        # Weighted combination using evaluation weights
        rule_score = (
            communication_score * weights.communication +
            confidence_dim_score * weights.confidence +
            technical_proxy * weights.technical_accuracy +
            depth_score * weights.depth +
            problem_solving_score * weights.problem_solving
        )
        
        return min(100.0, max(0.0, rule_score))
    
    def _compute_llm_based_score(
        self,
        metrics: LLMBasedMetrics,
        weights: EvaluationWeights
    ) -> float:
        """
        Compute LLM-based component score.
        
        LLM-based metrics:
        - technical_accuracy (0-100)
        - depth (0-100)
        - problem_solving (0-100)
        """
        
        # Weighted combination
        llm_score = (
            metrics.technical_accuracy * weights.technical_accuracy +
            metrics.depth * weights.depth +
            metrics.problem_solving * weights.problem_solving +
            # Communication and confidence not provided by LLM in current setup,
            # so we distribute their weight proportionally
            (metrics.technical_accuracy + metrics.depth + metrics.problem_solving) / 3 * 
            (weights.communication + weights.confidence)
        )
        
        return min(100.0, max(0.0, llm_score))
    
    def _classify_answer_quality(self, score: float) -> str:
        """
        Classify answer quality based on unified score.
        
        Maps to AnswerQuality enum values.
        """
        if score >= self.excellent_threshold:
            return "excellent"
        elif score >= self.good_threshold:
            return "good"
        elif score >= self.satisfactory_threshold:
            return "satisfactory"
        elif score >= self.partial_threshold:
            return "partial"
        else:
            return "insufficient"
    
    def _compute_confidence(
        self,
        rule_based: RuleBasedMetrics,
        llm_based: LLMBasedMetrics
    ) -> float:
        """
        Compute confidence in the evaluation.
        
        Higher confidence when:
        - Rule-based and LLM-based scores agree
        - Strong signals from both
        """
        
        # Normalize scores to 0-1
        rule_normalized = rule_based.confidence_score / 100
        llm_avg = (
            llm_based.technical_accuracy +
            llm_based.depth +
            llm_based.problem_solving
        ) / 300
        
        # Agreement between rule-based and LLM-based
        agreement = 1.0 - abs(rule_normalized - llm_avg)
        
        # Signal strength
        signal_strength = (rule_normalized + llm_avg) / 2
        
        # Confidence is combination of agreement and signal strength
        confidence = (agreement * 0.6 + signal_strength * 0.4)
        
        return confidence
    
    def validate_evaluation(self, evaluation: UnifiedEvaluation) -> tuple[bool, Optional[str]]:
        """
        Validate that evaluation meets minimum standards.
        
        Returns:
            (is_valid, error_message)
        """
        
        # Check for minimum acceptable scores in critical dimensions
        if evaluation.llm_based_metrics:
            llm = evaluation.llm_based_metrics
            
            if llm.technical_accuracy < self.min_acceptable_technical_accuracy * 100:
                if evaluation.final_score > 50:
                    return False, "Technical accuracy too low for this score"
            
            if llm.depth < self.min_acceptable_depth * 100:
                if evaluation.final_score > 60:
                    return False, "Depth too low for this score"
        
        # Check confidence threshold
        if evaluation.confidence < 0.3:
            return False, "Evaluation confidence too low"
        
        # Check for score disagreement
        score_diff = abs(evaluation.rule_based_score - evaluation.llm_based_score)
        if score_diff > 30:
            return False, f"Large disagreement between rule-based and LLM-based scores: {score_diff:.1f}"
        
        return True, None
    
    def should_request_llm_reevaluation(
        self,
        evaluation: UnifiedEvaluation
    ) -> bool:
        """
        Determine if LLM re-evaluation should be requested.
        
        Use cases:
        - Low confidence
        - Large disagreement between rule and LLM
        - Edge cases (scores near thresholds)
        """
        
        # Low confidence
        if evaluation.confidence < 0.4:
            return True
        
        # Large disagreement
        score_diff = abs(evaluation.rule_based_score - evaluation.llm_based_score)
        if score_diff > 25:
            return True
        
        # Near threshold boundaries
        thresholds = [
            self.excellent_threshold,
            self.good_threshold,
            self.satisfactory_threshold,
            self.partial_threshold
        ]
        
        for threshold in thresholds:
            if abs(evaluation.final_score - threshold) < 3:
                return True
        
        return False


class EvaluationCache(BaseModel):
    """Cache for evaluation results to improve latency."""
    
    cache: Dict[str, UnifiedEvaluation] = Field(default_factory=dict)
    max_size: int = 100
    
    def get(self, cache_key: str) -> Optional[UnifiedEvaluation]:
        """Get cached evaluation."""
        return self.cache.get(cache_key)
    
    def set(self, cache_key: str, evaluation: UnifiedEvaluation) -> None:
        """Cache evaluation result."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        
        self.cache[cache_key] = evaluation
    
    def generate_cache_key(
        self,
        transcript: str,
        question: str,
        phase: InterviewPhase
    ) -> str:
        """Generate cache key for evaluation."""
        import hashlib
        content = f"{transcript}|{question}|{phase.value}"
        return hashlib.md5(content.encode()).hexdigest()


def adjust_score_for_phase(
    score: float,
    phase: InterviewPhase,
    expected_difficulty: str
) -> float:
    """
    Adjust score based on phase expectations.
    
    Early phases: more lenient
    Later phases: stricter standards
    """
    
    adjustments = {
        InterviewPhase.INTRODUCTION: 1.1,  # 10% boost
        InterviewPhase.RESUME_DISCUSSION: 1.05,  # 5% boost
        InterviewPhase.TECHNICAL_ROUND_1: 1.0,  # No adjustment
        InterviewPhase.TECHNICAL_ROUND_2: 0.95,  # 5% stricter
        InterviewPhase.SYSTEM_DESIGN: 0.95,  # 5% stricter
        InterviewPhase.BEHAVIORAL: 1.0,  # No adjustment
        InterviewPhase.WRAP_UP: 1.0  # No adjustment
    }
    
    multiplier = adjustments.get(phase, 1.0)
    adjusted = score * multiplier
    
    return min(100.0, adjusted)


def compute_trend_score(recent_scores: List[float]) -> str:
    """
    Compute performance trend from recent scores.
    
    Returns: "improving", "stable", "declining"
    """
    if len(recent_scores) < 2:
        return "stable"
    
    # Simple linear regression
    n = len(recent_scores)
    x_avg = (n - 1) / 2
    y_avg = sum(recent_scores) / n
    
    numerator = sum((i - x_avg) * (score - y_avg) for i, score in enumerate(recent_scores))
    denominator = sum((i - x_avg) ** 2 for i in range(n))
    
    if denominator == 0:
        return "stable"
    
    slope = numerator / denominator
    
    if slope > 2:
        return "improving"
    elif slope < -2:
        return "declining"
    else:
        return "stable"
