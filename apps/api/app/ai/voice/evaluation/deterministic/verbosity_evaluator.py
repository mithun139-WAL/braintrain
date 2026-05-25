from typing import List, Dict, Any
from app.ai.voice.evaluation.deterministic.base_deterministic import DeterministicEvaluator

class VerbosityEvaluator(DeterministicEvaluator):
    @property
    def name(self) -> str:
        return "verbosity_evaluator"

    def evaluate(self, text: str, **kwargs) -> Dict[str, Any]:
        words = text.split()
        word_count = len(words)

        if word_count <= 15:
            score = word_count / 15 * 30
            level = "too_short"
        elif word_count <= 40:
            score = 30 + (word_count - 15) / 25 * 30
            level = "concise"
        elif word_count <= 80:
            score = 60 + (word_count - 40) / 40 * 20
            level = "moderate"
        elif word_count <= 150:
            score = 80 + (word_count - 80) / 70 * 15
            level = "verbose"
        else:
            score = 95 + min((word_count - 150) / 50 * 5, 5)
            level = "rambling"

        score = max(0, min(100, score))

        unique_words = len(set(w.lower() for w in words))
        repetition_ratio = 1 - (unique_words / word_count) if word_count > 0 else 0

        return {
            "verbosity_score": round(score, 1),
            "word_count": word_count,
            "unique_words": unique_words,
            "repetition_ratio": round(repetition_ratio, 3),
            "level": level,
        }

    def evidence(self, result: Dict[str, Any]) -> List[str]:
        evidence = []
        level = result["level"]
        if level == "too_short":
            evidence.append(f"Response very short: {result['word_count']} words")
        elif level == "verbose":
            evidence.append(f"Response lengthy: {result['word_count']} words with repetition ratio {result['repetition_ratio']}")
        elif level == "rambling":
            evidence.append(f"Response excessively long: {result['word_count']} words, consider being more concise")
        if result["repetition_ratio"] > 0.4:
            evidence.append(f"High word repetition: {result['repetition_ratio']*100:.0f}% repeated vocabulary")
        return evidence
