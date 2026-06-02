from typing import List, Dict, Any, Set
from app.ai.voice.evaluation.heuristic.base_heuristic import HeuristicEvaluator

class TopicRelevanceEvaluator(HeuristicEvaluator):
    @property
    def name(self) -> str:
        return "topic_relevance"

    def analyze(self, question: str, answer: str, **kwargs) -> Dict[str, Any]:
        question_lower = question.lower()
        answer_lower = answer.lower()

        question_words = set(w for w in question_lower.split() if len(w) > 3 and w.isalpha())
        answer_words = set(w for w in answer_lower.split() if len(w) > 3 and w.isalpha())

        if not question_words:
            return {"relevance_score": 100.0, "overlap": 0, "question_keywords": [], "answer_keywords": []}

        overlap = question_words & answer_words
        question_keywords = list(question_words)
        answer_keywords = list(answer_words)

        relevance = (len(overlap) / len(question_words)) * 100

        return {
            "relevance_score": round(relevance, 1),
            "overlap_count": len(overlap),
            "question_keyword_count": len(question_words),
            "overlap_terms": list(overlap),
        }

    def evidence(self, result: Dict[str, Any]) -> List[str]:
        evidence = []
        score = result["relevance_score"]
        if score >= 70:
            evidence.append(f"High topic relevance: {result['overlap_count']} keywords overlapped with question")
        elif score >= 40:
            evidence.append(f"Moderate topic relevance: {result['overlap_count']}/{result['question_keyword_count']} keywords addressed")
        else:
            evidence.append(f"Low topic relevance: only {result['overlap_count']}/{result['question_keyword_count']} question keywords addressed")
        return evidence
