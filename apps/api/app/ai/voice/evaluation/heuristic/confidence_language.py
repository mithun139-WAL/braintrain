import re
from typing import List, Dict, Any
from app.ai.voice.evaluation.heuristic.base_heuristic import HeuristicEvaluator

HIGH_CONFIDENCE_MARKERS = [
    r"\bI'm confident\b", r"\bI know\b", r"\bI'm certain\b", r"\bI'm sure\b",
    r"\bdefinitely\b", r"\bcertainly\b", r"\babsolutely\b", r"\bwithout question\b",
    r"\bundoubtedly\b", r"\bclearly\b", r"\bobviously\b", r"\bprecisely\b",
    r"\bI can explain\b", r"\bhere's how\b", r"\bthe key is\b",
]

LOW_CONFIDENCE_MARKERS = [
    r"\bi think\b", r"\bi believe\b", r"\bmaybe\b", r"\bperhaps\b",
    r"\bprobably\b", r"\bpossibly\b", r"\bi guess\b", r"\bnot sure\b",
    r"\bdon't know\b", r"\bnot certain\b", r"\bi'm not sure\b",
    r"\bi don't really\b", r"\bkind of\b", r"\bsort of\b",
    r"\bi'm not an expert\b", r"\bi could be wrong\b", r"\broughly\b",
]

class ConfidenceLanguageEvaluator(HeuristicEvaluator):
    @property
    def name(self) -> str:
        return "confidence_language"

    def analyze(self, question: str, answer: str, **kwargs) -> Dict[str, Any]:
        answer_lower = answer.lower()

        high_matches = []
        for pattern in HIGH_CONFIDENCE_MARKERS:
            found = re.findall(pattern, answer_lower)
            high_matches.extend(found)

        low_matches = []
        for pattern in LOW_CONFIDENCE_MARKERS:
            found = re.findall(pattern, answer_lower)
            low_matches.extend(found)

        high_count = len(high_matches)
        low_count = len(low_matches)

        total = high_count + low_count
        if total == 0:
            confidence_score = 50.0
        else:
            confidence_score = (high_count / total) * 100

        return {
            "confidence_score": round(confidence_score, 1),
            "high_confidence_markers": high_count,
            "low_confidence_markers": low_count,
            "high_examples": high_matches[:3],
            "low_examples": low_matches[:3],
        }

    def evidence(self, result: Dict[str, Any]) -> List[str]:
        evidence = []
        if result["high_confidence_markers"] > 0:
            evidence.append(f"{result['high_confidence_markers']} strong confidence markers used")
        if result["low_confidence_markers"] > 0:
            evidence.append(f"{result['low_confidence_markers']} hedging/low-confidence phrases detected")
        if result["confidence_score"] < 30:
            evidence.append("Consistently low confidence language throughout response")
        elif result["confidence_score"] > 70:
            evidence.append("Language indicates strong confidence")
        return evidence
