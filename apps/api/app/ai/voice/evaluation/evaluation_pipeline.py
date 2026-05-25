import uuid
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple

from app.ai.voice.conversation.memory import ConversationMessage
from app.ai.voice.evaluation.evaluation_types import (
    EvaluatorOutput,
    EvaluationDimension,
    EvaluationReport,
    TurnEvaluation,
    DimensionBreakdown,
)
from app.ai.voice.evaluation.evaluator import BaseEvaluator
from app.ai.voice.evaluation.scoring_engine import ScoringEngine
from app.ai.voice.evaluation.rubric_engine import RubricEngine
from app.ai.voice.evaluation.deterministic import (
    HesitationEvaluator,
    PaceEvaluator,
    VerbosityEvaluator,
)
from app.ai.voice.evaluation.heuristic import (
    STARDetector,
    TopicRelevanceEvaluator,
    ConfidenceLanguageEvaluator,
    DriftDetector,
)
from app.ai.voice.evaluation.evidence import EvidenceCollector
from app.ai.voice.evaluation.aggregators import (
    CompositeScorer,
    calculate_confidence_score,
    calculate_communication_score,
)
from app.ai.voice.evaluation.rubrics import RubricRegistry
from app.ai.voice.policies.domain_policy import InterviewDomain

logger = logging.getLogger("evaluation_pipeline")

class RefactoredEvaluationPipeline:
    def __init__(self, evaluators: List[BaseEvaluator] = None, domain: InterviewDomain = InterviewDomain.GENERAL):
        self.evaluators = evaluators or []
        self.rubric_engine = RubricEngine()
        self.rubric_registry = RubricRegistry()
        self.domain = domain
        self.evidence_collector = EvidenceCollector()

        self.hesitation_eval = HesitationEvaluator()
        self.pace_eval = PaceEvaluator()
        self.verbosity_eval = VerbosityEvaluator()
        self.star_detector = STARDetector()
        self.topic_relevance = TopicRelevanceEvaluator()
        self.confidence_lang = ConfidenceLanguageEvaluator()
        self.drift_detector = DriftDetector()

    def set_domain(self, domain: InterviewDomain) -> None:
        self.domain = domain

    def register_evaluator(self, evaluator: BaseEvaluator) -> None:
        self.evaluators.append(evaluator)

    async def execute_evaluation(
        self,
        session_id: uuid.UUID,
        candidate_id: uuid.UUID,
        messages: List[ConversationMessage],
        behavioral_metrics: Dict[str, Any],
    ) -> EvaluationReport:
        logger.info("Starting refactored evaluation pipeline for session: %s", session_id)

        self.evidence_collector.clear()

        user_turns = [m for m in messages if m.role == "user"]
        assistant_turns = [m for m in messages if m.role == "assistant"]

        all_text = " ".join(m.content for m in user_turns)
        he_result = self.hesitation_eval.evaluate(all_text)
        pa_result = self.pace_eval.evaluate(all_text, **behavioral_metrics)
        ve_result = self.verbosity_eval.evaluate(all_text)

        self.evidence_collector.add_from_deterministic(self.hesitation_eval, he_result)
        self.evidence_collector.add_from_deterministic(self.pace_eval, pa_result)
        self.evidence_collector.add_from_deterministic(self.verbosity_eval, ve_result)

        turn_timeline = self._build_turn_timeline(user_turns, assistant_turns)
        for entry in turn_timeline:
            if entry.hesitation_score > 40:
                self.evidence_collector.add(
                    "behavioral",
                    f"Turn {entry.turn}: high hesitation ({entry.hesitation_score:.0f})",
                    "timeline",
                    value=100 - entry.hesitation_score,
                )

        for turn_entry in turn_timeline:
            q = turn_entry.question_text
            a = turn_entry.answer_text
            if q and a:
                star_result = self.star_detector.analyze(q, a)
                self.evidence_collector.add_from_heuristic(self.star_detector, star_result)
                topic_result = self.topic_relevance.analyze(q, a)
                self.evidence_collector.add_from_heuristic(self.topic_relevance, topic_result)
                conf_result = self.confidence_lang.analyze(q, a)
                self.evidence_collector.add_from_heuristic(self.confidence_lang, conf_result)
                drift_result = self.drift_detector.analyze(q, a)
                self.evidence_collector.add_from_heuristic(self.drift_detector, drift_result)

        composite = self._calculate_composite_scores(he_result, pa_result, ve_result)
        evidence_report = self.evidence_collector.format_for_report()

        tasks = [evaluator.evaluate(messages, behavioral_metrics) for evaluator in self.evaluators]
        runs: List[EvaluatorOutput] = await asyncio.gather(*tasks) if tasks else []

        consistency_multiplier = self._analyze_consistency(messages, runs)
        scores, ci = ScoringEngine.calculate_dimension_scores(runs, consistency_multiplier)

        rubric = self.rubric_registry.get_rubric(self.domain)
        dimension_breakdowns = self._build_dimension_breakdowns(scores, runs, composite)

        feedback = self._generate_evidence_feedback(evidence_report, composite)
        recommendations = self._generate_recommendations(scores, evidence_report, composite)

        report = EvaluationReport(
            session_id=session_id,
            candidate_id=candidate_id,
            scores=scores,
            confidence_interval=ci,
            evaluator_runs=runs,
            feedback=feedback,
            recommendations=recommendations,
            turn_timeline=turn_timeline,
            dimension_breakdowns=dimension_breakdowns,
            behavioral_metrics={
                "overall_confidence": composite.get("overall_confidence", 50.0),
                "hesitation": he_result,
                "pace": pa_result,
            },
            communication_metrics={
                "verbosity": ve_result,
                "structure": composite.get("structure_score", 50.0),
                "star_completeness": composite.get("star_completeness", 0),
            },
            technical_metrics={"conceptual_depth": composite.get("conceptual_depth", 50.0)},
        )

        logger.info(
            "Evaluation pipeline complete | session: %s | overall: %.1f | CI: %s",
            session_id,
            composite.get("overall", 0),
            ci,
        )
        return report

    def _build_turn_timeline(
        self, user_turns: List[ConversationMessage], assistant_turns: List[ConversationMessage]
    ) -> List[TurnEvaluation]:
        timeline = []
        for i, (q, a) in enumerate(zip(assistant_turns, user_turns)):
            hesitation = self.hesitation_eval.evaluate(a.content)["hesitation_score"]
            drift = self.drift_detector.analyze(q.content, a.content)["drift_score"]
            verbosity = self.verbosity_eval.evaluate(a.content)["verbosity_score"]
            conf_lang = self.confidence_lang.analyze(q.content, a.content)
            conf_score = conf_lang["confidence_score"]

            strength = None
            issue = None
            if hesitation < 30 and drift < 40:
                strength = "clear and focused response"
            elif drift > 60:
                issue = "topic drift detected"
            elif hesitation > 60:
                issue = "high hesitation"

            timeline.append(TurnEvaluation(
                turn=i + 1,
                question_text=q.content[:200] if q else "",
                answer_text=a.content[:500] if a else "",
                hesitation_score=hesitation,
                confidence_score=conf_score,
                verbosity_score=verbosity,
                drift_score=drift,
                strength=strength,
                issue=issue,
            ))
        return timeline

    def _calculate_composite_scores(self, he: dict, pa: dict, ve: dict) -> Dict[str, Any]:
        scorer = CompositeScorer()

        scorer.add_component(
            "confidence",
            calculate_confidence_score(
                hesitation_score=he["hesitation_score"],
                pace_score=pa["pace_score"],
                decisiveness_score=50.0,
                interruption_recovery_score=50.0,
            ),
            weight=0.30,
            evidence=self.evidence_collector.get_by_category("hesitation_evaluator")[:3],
        )
        scorer.add_component("hesitation", 100 - he["hesitation_score"], weight=0.20,
                             evidence=self.hesitation_eval.evidence(he)[:2])
        scorer.add_component("pace", pa["pace_score"], weight=0.15,
                             evidence=self.pace_eval.evidence(pa)[:2])
        scorer.add_component("verbosity", 100 - ve["verbosity_score"], weight=0.15,
                             evidence=self.verbosity_eval.evidence(ve)[:2])

        result = scorer.calculate()
        result["overall_confidence"] = result["overall"]
        return result

    def _build_dimension_breakdowns(
        self,
        scores: Dict[EvaluationDimension, float],
        runs: List[EvaluatorOutput],
        composite: Dict[str, Any],
    ) -> List[DimensionBreakdown]:
        breakdowns = []
        rubric = self.rubric_registry.get_rubric(self.domain)
        if rubric:
            for dim_def in rubric.dimensions:
                dim_key = EvaluationDimension.TECHNICAL if dim_def.name in (
                    "TECHNICAL_DEPTH", "FRONTEND_FUNDAMENTALS", "SYSTEMS_AND_ARCHITECTURE"
                ) else EvaluationDimension.COMMUNICATION

                score = scores.get(dim_key, 3.0)
                level_info = self.rubric_engine.get_level_info(dim_key, score)

                breakdowns.append(DimensionBreakdown(
                    dimension=dim_def.name,
                    score=score,
                    weight=dim_def.weight,
                    rubric_level=level_info.get("name", "Unknown"),
                    rubric_description=level_info.get("desc", ""),
                    evidence=self.evidence_collector.get_all()[:3],
                ))

        if not breakdowns:
            for dim, score in scores.items():
                level_info = self.rubric_engine.get_level_info(dim, score)
                breakdowns.append(DimensionBreakdown(
                    dimension=dim.value,
                    score=score,
                    weight=0.25,
                    rubric_level=level_info.get("name", "Unknown"),
                    rubric_description=level_info.get("desc", ""),
                ))

        return breakdowns

    def _analyze_consistency(self, messages, runs) -> float:
        multiplier = 1.0
        tech_scores = [r.score for r in runs if r.dimension == EvaluationDimension.TECHNICAL]
        behavior_runs = [r for r in runs if r.dimension == EvaluationDimension.BEHAVIORAL]

        if tech_scores and behavior_runs:
            avg_tech = sum(tech_scores) / len(tech_scores)
            avg_behavior = sum(r.score for r in behavior_runs) / len(behavior_runs)
            if avg_tech >= 4.0 and avg_behavior <= 2.0:
                logger.warning("Consistency: high technical but low confidence/hesitation.")
                multiplier -= 0.15

        return max(0.5, multiplier)

    def _generate_evidence_feedback(self, evidence_report: dict, composite: dict) -> Dict[str, Any]:
        return {
            "strengths": evidence_report.get("strengths", []),
            "areas_of_improvement": evidence_report.get("weaknesses", []),
            "observations": evidence_report.get("observations", []),
            "total_evidence_points": evidence_report.get("total_evidence_points", 0),
            "composite_overall": composite.get("overall", 50.0),
        }

    def _generate_recommendations(
        self,
        scores: Dict[EvaluationDimension, float],
        evidence_report: dict,
        composite: dict,
    ) -> List[str]:
        recommendations = []

        weakness_count = len(evidence_report.get("weaknesses", []))
        if weakness_count > 2:
            recommendations.append(
                f"Focus on reducing filler words and hedging language ({weakness_count} hesitation markers detected). "
                "Practice pausing silently instead of using filler phrases."
            )

        overall = composite.get("overall", 50)
        if overall < 40:
            recommendations.append(
                "Overall communication could be more structured. Practice using the STAR method "
                "(Situation, Task, Action, Result) to organize your responses."
            )

        for dim, score in scores.items():
            if score < 3.0:
                if dim == EvaluationDimension.TECHNICAL:
                    recommendations.append(
                        "Review core technical topics focusing on edge case handling and tradeoff reasoning. "
                        "Practice explaining complex concepts with concrete examples."
                    )
                elif dim == EvaluationDimension.COMMUNICATION:
                    recommendations.append(
                        "Work on response structure: lead with your answer, then explain your reasoning, "
                        "and end with a specific example or result."
                    )
                elif dim == EvaluationDimension.BEHAVIORAL:
                    recommendations.append(
                        "Practice pacing drills: record yourself answering questions and check for "
                        "filler words, long pauses, and hedging language."
                    )

        if not recommendations:
            recommendations.append(
                "Strong overall performance. To further improve, practice explaining the same concept "
                "at different levels of depth (executive summary vs technical deep dive)."
            )

        return recommendations


# Backward compatibility alias
EvaluationPipeline = RefactoredEvaluationPipeline

