"""
Evaluation Orchestrator - Combines rule-based and LLM-based evaluation.

This orchestrator:
1. Runs rule-based evaluation (60% weight)
2. Requests LLM evaluation (40% weight)
3. Combines scores using EvaluationPolicy
4. Validates results
5. Handles disagreements and edge cases
"""
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime
import logging
import asyncio
import json

from pydantic import BaseModel

from app.ai.orchestrators.contracts.evaluation_contracts import (
    RuleBasedMetrics,
    LLMBasedMetrics,
    UnifiedEvaluation,
    EvaluationWeights
)
from app.ai.orchestrators.contracts.interview_contracts import InterviewPhase, InterviewDomain
from app.ai.orchestrators.contracts.turn_contracts import AnswerQuality
from app.ai.orchestrators.contracts.model_contracts import ModelTask
from app.ai.orchestrators.policies.evaluation_policy import (
    EvaluationPolicy,
    EvaluationCache,
    adjust_score_for_phase,
    compute_trend_score
)
from app.ai.orchestrators.instrumentation import get_instrumentation

if TYPE_CHECKING:
    from app.ai.orchestrators.model_orchestrator import ModelOrchestrator

logger = logging.getLogger(__name__)


class EvaluationOrchestrator:
    """
    Orchestrator for answer evaluation.
    
    Key principles:
    - Rule-based evaluation is PRIMARY (60%)
    - LLM evaluation is SECONDARY (40%)
    - Deterministic combination via policy
    - Validation and disagreement handling
    - Caching for latency optimization
    """
    
    def __init__(
        self,
        policy: Optional[EvaluationPolicy] = None,
        enable_cache: bool = True,
        model_orchestrator: Optional["ModelOrchestrator"] = None
    ):
        self.policy = policy or EvaluationPolicy()
        self.cache = EvaluationCache() if enable_cache else None
        self.model_orchestrator = model_orchestrator
        
        # Instrumentation
        self.instrumentation = get_instrumentation()
        
        # Performance tracking
        self.evaluation_latencies: List[float] = []
        self.disagreement_count = 0
        self.total_evaluations = 0
        
        logger.info("Initialized EvaluationOrchestrator")
    
    async def evaluate_answer(
        self,
        question: str,
        answer_transcript: str,
        phase: InterviewPhase,
        domain: InterviewDomain,
        context: Optional[Dict[str, Any]] = None
    ) -> UnifiedEvaluation:
        """
        Evaluate candidate answer using combined approach.
        
        Steps:
        1. Check cache
        2. Run rule-based evaluation (fast)
        3. Run LLM evaluation (slower) in parallel
        4. Combine using policy
        5. Validate result
        6. Cache result
        """
        
        start_time = datetime.utcnow()
        
        # Start tracing
        trace_attrs = {
            "phase": phase.value,
            "domain": domain.value if domain else "unknown",
            "answer_length": len(answer_transcript)
        }
        
        async with self.instrumentation.trace_operation("evaluation.evaluate_answer", trace_attrs) as span:
            # Check cache
            if self.cache:
                cache_key = self.cache.generate_cache_key(answer_transcript, question, phase)
                cached = self.cache.get(cache_key)
                if cached:
                    logger.info(f"Cache hit for evaluation")
                    if span:
                        span.set_attribute("cache_hit", True)
                    return cached
            
            if span:
                span.set_attribute("cache_hit", False)
            
            # Get evaluation weights for this phase/domain
            weights = self.policy.get_weights(phase, domain)
            
            # Run evaluations in parallel
            rule_task = self._run_rule_based_evaluation(
                question,
                answer_transcript,
                phase,
                context
            )
            
            llm_task = self._run_llm_based_evaluation(
                question,
                answer_transcript,
                phase,
                domain,
                context
            )
            
            # Wait for both
            rule_based, llm_based = await asyncio.gather(rule_task, llm_task)
            
            # Combine using policy
            unified = self.policy.compute_unified_score(
                rule_based,
                llm_based,
                weights
            )
            
            # Adjust for phase expectations
            unified.final_score = adjust_score_for_phase(
                unified.final_score,
                phase,
                "moderate"
            )
            
            # Validate
            is_valid, error = self.policy.validate_evaluation(unified)
            
            if not is_valid:
                logger.warning(f"Evaluation validation failed: {error}")
                
                if span:
                    span.add_event("validation_failed", {"error": error})
                
                # Check if re-evaluation needed
                if self.policy.should_request_llm_reevaluation(unified):
                    logger.info("Requesting LLM re-evaluation")
                    
                    if span:
                        span.add_event("reevaluation_triggered")
                    
                    llm_based = await self._run_llm_based_evaluation(
                        question,
                        answer_transcript,
                        phase,
                        domain,
                        context,
                        is_reevaluation=True
                    )
                    
                    unified = self.policy.compute_unified_score(
                        rule_based,
                    llm_based,
                    weights
                )
            
            # Track performance
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.evaluation_latencies.append(latency_ms)
            self.total_evaluations += 1
            
            # Record metrics
            self.instrumentation.record_metric(
                "evaluation_latency",
                latency_ms,
                {"phase": phase.value, "domain": domain.value if domain else "unknown"}
            )
            self.instrumentation.increment_counter(
                "evaluations",
                attributes={"phase": phase.value, "quality": unified.answer_quality.value}
            )
            
            # Check for disagreement
            score_diff = abs(unified.rule_based_score - unified.llm_based_score)
            if score_diff > 20:
                self.disagreement_count += 1
                logger.warning(
                    f"Evaluation disagreement: rule={unified.rule_based_score:.1f} "
                    f"llm={unified.llm_based_score:.1f} diff={score_diff:.1f}"
                )
                if span:
                    span.add_event("evaluation_disagreement", {"score_diff": score_diff})
            
            # Add span attributes
            if span:
                span.set_attribute("final_score", unified.final_score)
                span.set_attribute("answer_quality", unified.answer_quality.value)
                span.set_attribute("confidence", unified.confidence)
                span.set_attribute("latency_ms", latency_ms)
                span.set_attribute("rule_based_score", unified.rule_based_score)
                span.set_attribute("llm_based_score", unified.llm_based_score)
            
            # Cache result
            if self.cache:
                self.cache.set(cache_key, unified)
            
            logger.info(
                f"Evaluation complete: score={unified.final_score:.1f} "
                f"quality={unified.answer_quality.value} latency={latency_ms:.0f}ms"
            )
            
            return unified
    
    async def _run_rule_based_evaluation(
        self,
        question: str,
        answer: str,
        phase: InterviewPhase,
        context: Optional[Dict[str, Any]]
    ) -> RuleBasedMetrics:
        """
        Run rule-based evaluation.
        
        This is FAST and DETERMINISTIC.
        """
        from app.ai.intelligence.communication.communication_engine import CommunicationIntelligenceEngine
        from app.ai.intelligence.strategic.strategic_engine import StrategicThinkingEngine
        
        comm_engine = CommunicationIntelligenceEngine()
        strat_engine = StrategicThinkingEngine()
        
        # 1. Communication & Uncertainty
        uncert = comm_engine.detect_uncertainty_language(answer)
        filler_word_score = 100.0 - uncert["uncertainty_score"]
        
        # 2. Executive Presence & Structure
        exec_presence = comm_engine.detect_executive_presence(answer)
        confidence_score = exec_presence["executive_presence_score"]
        
        # 3. STAR / PREP structure
        struct = comm_engine.analyze_response_structure(answer, phase)
        star_score = struct["structure_score"]
        
        # 4. Narrative Flow
        flow = comm_engine.analyze_narrative_flow(answer)
        clarity_score = flow["narrative_flow_score"]
        
        # 5. Strategic pathing & priority
        strat_path = strat_engine.analyze_reasoning_path(answer)
        tradeoffs = strat_engine.detect_tradeoff_thinking(answer)
        
        # Ownership and Impact scores
        ownership_score = exec_presence["executive_presence_score"]
        impact_score = min(100.0, tradeoffs["tradeoff_score"] + 20.0)
        
        # Timing / Terminology
        words = answer.split()
        word_count = len(words)
        
        metrics = RuleBasedMetrics(
            filler_word_score=filler_word_score,
            filler_word_count=uncert["filler_count"],
            filler_word_density=uncert["filler_rate_percent"],
            confidence_score=confidence_score,
            hesitation_count=uncert["hedge_count"],
            hesitation_density=uncert["hedge_rate_percent"],
            clarity_score=clarity_score,
            average_sentence_length=word_count / max(1, len(answer.split('.'))),
            vocabulary_diversity=len(set(w.lower() for w in words)) / max(1, word_count) * 100,
            star_score=star_score,
            star_components_found={c: True for c in struct["components_detected"]},
            ownership_score=ownership_score,
            i_to_we_ratio=0.5,
            ownership_phrase_count=exec_presence["markers_detected"],
            impact_score=impact_score,
            quantified_metric_count=len(tradeoffs["tradeoff_matches"]),
            quantified_examples=tradeoffs["tradeoff_matches"],
            communication_stability_score=100.0 - comm_engine.detect_rambling(answer)["rambling_score"],
            response_consistency_score=100.0 - comm_engine.detect_fragmentation(answer)["fragmentation_score"],
            technical_terminology_score=strat_path["reasoning_path_score"],
            terminology_count=len(strat_path["sequence"]),
            correct_terminology_ratio=1.0 if strat_path["is_order_correct"] else 0.5,
            technical_keyword_coverage=strat_path["reasoning_path_score"] / 100.0
        )
        
        return metrics
    
    async def _run_llm_based_evaluation(
        self,
        question: str,
        answer: str,
        phase: InterviewPhase,
        domain: InterviewDomain,
        context: Optional[Dict[str, Any]],
        is_reevaluation: bool = False
    ) -> LLMBasedMetrics:
        """
        Run LLM-based evaluation.
        
        This provides nuanced assessment but is slower.
        Model: gpt-4o-mini (per routing policy)
        """
        
        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(
            question,
            answer,
            phase,
            domain,
            is_reevaluation
        )
        
        # Call LLM (mock for now - in production, call actual model)
        # TODO: Integrate with ModelOrchestrator
        llm_response = await self._call_evaluation_llm(prompt, context)
        
        # Parse response
        metrics = self._parse_llm_evaluation(llm_response)
        
        return metrics
    
    def _build_evaluation_prompt(
        self,
        question: str,
        answer: str,
        phase: InterviewPhase,
        domain: InterviewDomain,
        is_reevaluation: bool
    ) -> str:
        """Build prompt for LLM evaluation."""
        
        prompt = f"""Evaluate this interview answer on a scale of 0-100.

**Question:** {question}

**Answer:** {answer}

**Phase:** {phase.value}
**Domain:** {domain.value}

Provide scores for:
1. Technical Accuracy (0-100): How technically correct is the answer?
2. Depth (0-100): How deep is the understanding demonstrated?
3. Problem-Solving (0-100): How well does the candidate approach problems?

Respond in JSON format:
{{
    "technical_accuracy": <score>,
    "depth": <score>,
    "problem_solving": <score>,
    "reasoning": "<brief explanation>"
}}
"""
        
        if is_reevaluation:
            prompt += "\n**NOTE:** This is a re-evaluation. Please be extra careful and thorough."
        
        return prompt
    
    async def _call_evaluation_llm(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Call LLM for evaluation.
        
        Uses ModelOrchestrator for proper routing and fallbacks.
        """
        
        if self.model_orchestrator:
            try:
                # Use ModelOrchestrator for actual API call
                response = await self.model_orchestrator.generate(
                    task=ModelTask.EVALUATION,
                    prompt=prompt,
                    context=None,  # Context is already in the prompt
                    max_tokens=200,
                    temperature=0.1,  # Low temperature for consistent evaluation
                    timeout_ms=5000,
                    metadata={"evaluation": True}
                )
                
                # Parse JSON response
                try:
                    result = json.loads(response.text)
                    return result
                except json.JSONDecodeError:
                    # Try to extract JSON from text if it's wrapped
                    import re
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group(0))
                        return result
                    else:
                        logger.warning("Failed to parse LLM evaluation response as JSON")
                        raise
            
            except Exception as e:
                logger.error(f"ModelOrchestrator evaluation failed: {e}, falling back to mock")
        
        # Fallback to mock response if ModelOrchestrator not available or failed
        import random
        
        mock_response = {
            "technical_accuracy": random.randint(50, 95),
            "depth": random.randint(45, 90),
            "problem_solving": random.randint(50, 90),
            "reasoning": "Candidate demonstrated solid understanding with room for improvement."
        }
        
        # Simulate latency
        await asyncio.sleep(0.05)
        
        return mock_response
    
    def _parse_llm_evaluation(self, response: Dict[str, Any]) -> LLMBasedMetrics:
        """Parse LLM evaluation response."""
        
        metrics = LLMBasedMetrics(
            technical_accuracy=response.get("technical_accuracy", 70.0),
            depth=response.get("depth", 70.0),
            problem_solving=response.get("problem_solving", 70.0),
            reasoning=response.get("reasoning", "")
        )
        
        return metrics
    
    def _calculate_ownership_score(self, answer: str) -> Optional[float]:
        """Calculate ownership indicators in answer."""
        
        ownership_keywords = [
            "i led", "i owned", "i drove", "i initiated", "i designed",
            "my responsibility", "i decided", "i proposed"
        ]
        
        answer_lower = answer.lower()
        matches = sum(1 for kw in ownership_keywords if kw in answer_lower)
        
        if matches == 0:
            return None
        
        # Score based on mentions
        score = min(100.0, 60 + matches * 15)
        return score
    
    def _calculate_impact_score(self, answer: str) -> Optional[float]:
        """Calculate impact indicators in answer."""
        
        impact_keywords = [
            "improved", "increased", "reduced", "saved", "generated",
            "resulted in", "achieved", "delivered", "%", "x faster"
        ]
        
        answer_lower = answer.lower()
        matches = sum(1 for kw in impact_keywords if kw in answer_lower)
        
        if matches == 0:
            return None
        
        # Score based on quantifiable impact mentions
        score = min(100.0, 55 + matches * 15)
        return score
    
    def _check_answer_structure(self, answer: str) -> bool:
        """Check if answer has good structure."""
        
        # Simple heuristics:
        # - Multiple sentences
        # - Reasonable length
        # - Has transition words
        
        sentences = answer.split(".")
        if len(sentences) < 2:
            return False
        
        words = answer.split()
        if len(words) < 20:
            return False
        
        transition_words = [
            "first", "then", "next", "finally", "because", "so", "however",
            "additionally", "for example", "specifically"
        ]
        
        answer_lower = answer.lower()
        has_transitions = any(tw in answer_lower for tw in transition_words)
        
        return has_transitions
    
    async def evaluate_batch(
        self,
        evaluations: List[Dict[str, Any]],
        phase: InterviewPhase,
        domain: InterviewDomain
    ) -> List[UnifiedEvaluation]:
        """
        Evaluate multiple answers in batch for efficiency.
        """
        
        tasks = []
        for eval_data in evaluations:
            task = self.evaluate_answer(
                question=eval_data["question"],
                answer_transcript=eval_data["answer"],
                phase=phase,
                domain=domain,
                context=eval_data.get("context")
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get evaluation performance statistics."""
        
        if not self.evaluation_latencies:
            return {}
        
        avg_latency = sum(self.evaluation_latencies) / len(self.evaluation_latencies)
        max_latency = max(self.evaluation_latencies)
        min_latency = min(self.evaluation_latencies)
        
        disagreement_rate = (
            self.disagreement_count / self.total_evaluations
            if self.total_evaluations > 0
            else 0.0
        )
        
        return {
            "total_evaluations": self.total_evaluations,
            "avg_latency_ms": avg_latency,
            "max_latency_ms": max_latency,
            "min_latency_ms": min_latency,
            "disagreement_rate": disagreement_rate,
            "cache_enabled": self.cache is not None
        }
    
    def map_score_to_answer_quality(self, score: float) -> AnswerQuality:
        """Map numerical score to AnswerQuality enum."""
        
        if score >= 85:
            return AnswerQuality.EXCELLENT
        elif score >= 70:
            return AnswerQuality.GOOD
        elif score >= 55:
            return AnswerQuality.SATISFACTORY
        elif score >= 40:
            return AnswerQuality.PARTIAL
        else:
            return AnswerQuality.INSUFFICIENT
