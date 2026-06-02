from typing import List, Dict, Any
from app.ai.voice.evaluation.deterministic.base_deterministic import DeterministicEvaluator

IDEAL_WPM = 150
WPM_LOW = 80
WPM_HIGH = 220

class PaceEvaluator(DeterministicEvaluator):
    @property
    def name(self) -> str:
        return "pace_evaluator"

    def evaluate(self, text: str, **kwargs) -> Dict[str, Any]:
        words = text.split()
        word_count = len(words)
        response_time_ms = kwargs.get("response_time_ms", 0.0)
        thinking_time_ms = kwargs.get("thinking_time_ms", 0.0)

        speaking_time_s = max(0.001, response_time_ms - thinking_time_ms) / 1000.0
        wpm = (word_count / speaking_time_s) * 60 if speaking_time_s > 0 else 0

        if wpm < WPM_LOW:
            pace_score = max(0, (wpm / WPM_LOW) * 30)
        elif wpm > WPM_HIGH:
            pace_score = max(0, 100 - ((wpm - WPM_HIGH) / WPM_HIGH) * 50)
        else:
            pace_score = 100 - abs(wpm - IDEAL_WPM) / IDEAL_WPM * 50
            pace_score = max(0, min(100, pace_score))

        return {
            "pace_score": round(pace_score, 1),
            "wpm": round(wpm, 1),
            "word_count": word_count,
            "speaking_time_s": round(speaking_time_s, 2),
        }

    def evidence(self, result: Dict[str, Any]) -> List[str]:
        evidence = []
        wpm = result["wpm"]
        if wpm < 80:
            evidence.append(f"Very slow speaking pace: {wpm} words per minute")
        elif wpm < 120:
            evidence.append(f"Slightly slow pace: {wpm} words per minute")
        elif wpm > 220:
            evidence.append(f"Very fast speaking pace: {wpm} words per minute")
        elif wpm > 180:
            evidence.append(f"Fast speaking pace: {wpm} words per minute")
        else:
            evidence.append(f"Good speaking pace: {wpm} words per minute")
        return evidence
