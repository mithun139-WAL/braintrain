import re
from typing import List, Dict, Any, Set
from app.ai.voice.evaluation.heuristic.base_heuristic import HeuristicEvaluator

TOPIC_CONTINUITY_STOP_WORDS = {
    "the", "a", "an", "is", "was", "were", "and", "or", "but", "in", "on",
    "at", "to", "for", "of", "with", "by", "from", "as", "it", "its",
    "that", "this", "these", "those", "i", "you", "we", "they", "he", "she",
    "my", "our", "your", "their", "his", "her", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "can",
    "very", "really", "just", "also", "then", "now", "about", "what",
    "which", "who", "where", "when", "how", "all", "some", "any",
}

class DriftDetector(HeuristicEvaluator):
    @property
    def name(self) -> str:
        return "drift_detector"

    def analyze(self, question: str, answer: str, **kwargs) -> Dict[str, Any]:
        question_words = self._tokenize(question)
        answer_words = self._tokenize(answer)

        if not question_words:
            return {"drift_score": 0.0, "overlap_jaccard": 0.0, "drift_markers": []}

        intersection = question_words & answer_words
        union = question_words | answer_words

        jaccard = len(intersection) / len(union) if union else 0
        drift_score = (1 - jaccard) * 100

        new_topics = answer_words - question_words
        drift_markers = sorted(new_topics)[:5] if new_topics else []

        return {
            "drift_score": round(drift_score, 1),
            "jaccard_similarity": round(jaccard, 3),
            "intersection_count": len(intersection),
            "union_count": len(union),
            "possible_new_topics": drift_markers,
        }

    def _tokenize(self, text: str) -> Set[str]:
        words = set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))
        return words - TOPIC_CONTINUITY_STOP_WORDS

    def evidence(self, result: Dict[str, Any]) -> List[str]:
        evidence = []
        score = result["drift_score"]
        if score > 70:
            evidence.append(f"Significant topic drift: {score:.0f}% new terms not in question")
            if result["possible_new_topics"]:
                evidence.append(f"New topics introduced: {', '.join(result['possible_new_topics'][:3])}")
        elif score > 45:
            evidence.append(f"Moderate topic drift: {score:.0f}% new content detected")
        else:
            evidence.append("Response stays on topic")
        return evidence
