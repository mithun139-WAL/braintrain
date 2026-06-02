import math
import statistics
import logging
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("composite_scorer")

@dataclass
class ScoreComponent:
    name: str
    score: float
    weight: float
    evidence: List[str] = field(default_factory=list)

class CompositeScorer:
    def __init__(self):
        self._components: List[ScoreComponent] = []

    def add_component(self, name: str, score: float, weight: float, evidence: List[str] = None) -> None:
        self._components.append(ScoreComponent(
            name=name,
            score=max(0.0, min(100.0, score)),
            weight=weight,
            evidence=evidence or [],
        ))

    def calculate(self) -> Dict[str, Any]:
        if not self._components:
            return {"overall": 50.0, "components": [], "confidence_interval": (40.0, 60.0)}

        total_weight = sum(c.weight for c in self._components)
        if total_weight == 0:
            return {"overall": 50.0, "components": [], "confidence_interval": (40.0, 60.0)}

        weighted_sum = sum(c.score * c.weight for c in self._components)
        overall = weighted_sum / total_weight
        overall = max(0.0, min(100.0, overall))

        scores = [c.score for c in self._components]
        variance = statistics.variance(scores) if len(scores) > 1 else 0
        std_error = math.sqrt(variance / len(scores)) if len(scores) > 0 else 0
        ci_low = max(0.0, overall - 1.96 * std_error)
        ci_high = min(100.0, overall + 1.96 * std_error)

        return {
            "overall": round(overall, 1),
            "components": [
                {
                    "name": c.name,
                    "score": round(c.score, 1),
                    "weight": c.weight,
                    "evidence": c.evidence,
                }
                for c in sorted(self._components, key=lambda x: x.weight, reverse=True)
            ],
            "confidence_interval": (round(ci_low, 1), round(ci_high, 1)),
        }

    def clear(self) -> None:
        self._components.clear()


def calculate_confidence_score(
    hesitation_score: float,
    pace_score: float,
    decisiveness_score: float,
    interruption_recovery_score: float,
) -> float:
    weights = {"hesitation": 0.35, "pace": 0.25, "decisiveness": 0.20, "recovery": 0.20}

    hesitation_normalized = max(0, 100 - hesitation_score)
    pace_normalized = pace_score
    weighted = (
        hesitation_normalized * weights["hesitation"]
        + pace_normalized * weights["pace"]
        + decisiveness_score * weights["decisiveness"]
        + interruption_recovery_score * weights["recovery"]
    )
    return max(0.0, min(100.0, weighted))


def calculate_communication_score(
    verbosity_score: float,
    clarity_score: float,
    structure_score: float,
    star_completeness: float,
) -> float:
    weights = {"verbosity": 0.20, "clarity": 0.35, "structure": 0.25, "star": 0.20}

    verbosity_normalized = max(0, 100 - verbosity_score)
    weighted = (
        verbosity_normalized * weights["verbosity"]
        + clarity_score * weights["clarity"]
        + structure_score * weights["structure"]
        + star_completeness * weights["star"]
    )
    return max(0.0, min(100.0, weighted))
