import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any
from app.ai.voice.evaluation.deterministic import DeterministicEvaluator
from app.ai.voice.evaluation.heuristic import HeuristicEvaluator

logger = logging.getLogger("evidence_collector")

@dataclass
class EvidenceItem:
    category: str
    detail: str
    source: str
    value: float

class EvidenceCollector:
    def __init__(self):
        self._items: List[EvidenceItem] = []

    def add(self, category: str, detail: str, source: str, value: float = 0.0) -> None:
        item = EvidenceItem(
            category=category,
            detail=detail,
            source=source,
            value=value,
        )
        self._items.append(item)
        logger.debug("evidence_collected | category: %s | source: %s | detail: %s", category, source, detail)

    def add_from_deterministic(self, evaluator: DeterministicEvaluator, result: Dict[str, Any]) -> None:
        for ev in evaluator.evidence(result):
            self.add(
                category=evaluator.name,
                detail=ev,
                source="deterministic",
                value=result.get(list(result.keys())[0], 0.0),
            )

    def add_from_heuristic(self, evaluator: HeuristicEvaluator, result: Dict[str, Any]) -> None:
        for ev in evaluator.evidence(result):
            self.add(
                category=evaluator.name,
                detail=ev,
                source="heuristic",
                value=result.get(list(result.keys())[0], 0.0),
            )

    def get_all(self) -> List[EvidenceItem]:
        return self._items

    def get_by_category(self, category: str) -> List[EvidenceItem]:
        return [i for i in self._items if i.category == category]

    def get_by_source(self, source: str) -> List[EvidenceItem]:
        return [i for i in self._items if i.source == source]

    def format_for_report(self) -> Dict[str, Any]:
        strengths = []
        weaknesses = []
        neutral = []

        for item in self._items:
            if item.value > 70:
                strengths.append(item.detail)
            elif item.value < 40:
                weaknesses.append(item.detail)
            else:
                neutral.append(item.detail)

        return {
            "strengths": strengths[:5],
            "weaknesses": weaknesses[:5],
            "observations": neutral[:5],
            "total_evidence_points": len(self._items),
        }

    def clear(self) -> None:
        self._items.clear()
