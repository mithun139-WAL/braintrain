import re
import statistics
from typing import List, Dict, Any
from app.ai.voice.evaluation.deterministic.base_deterministic import DeterministicEvaluator

FILLER_WORDS = [
    "um", "uh", "ah", "er", "like", "you know", "sort of", "kind of",
    "actually", "basically", "literally", "honestly", "well", "so",
    "i mean", "right", "okay", "you see", "anyway",
]

HEDGE_WORDS = [
    "i think", "i believe", "i guess", "maybe", "probably", "possibly",
    "perhaps", "might", "could be", "i suppose", "sort of", "kind of",
    "not sure", "i don't know", "i'm not certain",
]

class HesitationEvaluator(DeterministicEvaluator):
    @property
    def name(self) -> str:
        return "hesitation_evaluator"

    def evaluate(self, text: str, **kwargs) -> Dict[str, Any]:
        text_lower = text.lower()
        words = text.split()
        word_count = len(words)
        if word_count == 0:
            return {
                "hesitation_score": 0.0,
                "filler_count": 0,
                "hedge_count": 0,
                "filler_density": 0.0,
                "hedge_density": 0.0,
                "restart_count": 0,
            }

        filler_count = sum(text_lower.count(fw) for fw in FILLER_WORDS)
        hedge_count = sum(text_lower.count(hw) for hw in HEDGE_WORDS)

        restart_markers = re.findall(r'\b(i mean|that is|rather|actually|correction)\b', text_lower)
        restart_count = len(restart_markers)

        filler_density = (filler_count / word_count) * 100
        hedge_density = (hedge_count / word_count) * 100

        raw_score = (filler_density * 0.5 + hedge_density * 0.3 + min(restart_count * 10, 20))
        score = min(100.0, raw_score)

        return {
            "hesitation_score": round(score, 1),
            "filler_count": filler_count,
            "hedge_count": hedge_count,
            "filler_density": round(filler_density, 2),
            "hedge_density": round(hedge_density, 2),
            "restart_count": restart_count,
        }

    def evidence(self, result: Dict[str, Any]) -> List[str]:
        evidence = []
        if result["filler_count"] > 0:
            evidence.append(f"{result['filler_count']} filler phrases detected")
        if result["hedge_count"] > 0:
            evidence.append(f"{result['hedge_count']} hedging phrases used ('I think', 'maybe', etc.)")
        if result["restart_count"] > 0:
            evidence.append(f"{result['restart_count']} speech restarts detected")
        if result["filler_density"] > 10:
            evidence.append(f"High filler density: {result['filler_density']}% of words were fillers")
        return evidence
