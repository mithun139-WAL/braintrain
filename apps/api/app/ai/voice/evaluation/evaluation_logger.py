import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("evaluation_logger")

class EvaluationLogger:
    def log_hallucination_prevention(self, session_id: str, followup_text: str, reason: str) -> None:
        logger.warning(
            "hallucination_prevented | session: %s | reason: %s | followup: %s",
            session_id, reason, followup_text[:100],
        )

    def log_rejected_followup(self, session_id: str, followup_text: str, reason: str) -> None:
        logger.info(
            "followup_rejected | session: %s | reason: %s | followup: %s",
            session_id, reason, followup_text[:100],
        )

    def log_domain_violation(self, session_id: str, domain: str, topic: str) -> None:
        logger.warning(
            "domain_violation | session: %s | domain: %s | topic: %s",
            session_id, domain, topic,
        )

    def log_scoring_breakdown(self, session_id: str, scores: Dict[str, float]) -> None:
        logger.info(
            "scoring_breakdown | session: %s | scores: %s",
            session_id, scores,
        )

    def log_heuristic_output(self, session_id: str, evaluator: str, result: Dict[str, Any]) -> None:
        logger.debug(
            "heuristic_output | session: %s | evaluator: %s | result: %s",
            session_id, evaluator, result,
        )

    def log_evidence_generated(self, session_id: str, evidence_count: int) -> None:
        logger.info(
            "evidence_generated | session: %s | count: %d",
            session_id, evidence_count,
        )

evaluation_logger = EvaluationLogger()
