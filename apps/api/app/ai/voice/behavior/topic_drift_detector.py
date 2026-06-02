import logging

logger = logging.getLogger("topic_drift_detector")

class TopicDriftDetector:
    def __init__(self):
        # Basic common stopwords set
        self.stop_words = {
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "as", "at",
            "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "could", "did", "do",
            "does", "doing", "down", "during", "each", "few", "for", "from", "further", "had", "has", "have", "having",
            "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
            "it", "its", "itself", "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
            "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should",
            "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there",
            "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "we",
            "were", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "would", "you", "your",
            "yours", "yourself", "yourselves"
        }

    def detect(self, current_question: str, transcript: str) -> float:
        """
        Estimates Jaccard conceptual drift (0-100) based on keyword overlaps.
        """
        if not current_question or not transcript:
            return 0.0

        # Helper to clean and split words
        def clean_words(text: str) -> set[str]:
            words = text.lower().replace("?", " ").replace(".", " ").replace(",", " ").split()
            return {w.strip("'\":;()[]{}*-_") for w in words if w not in self.stop_words and len(w) > 2}

        q_keywords = clean_words(current_question)
        a_keywords = clean_words(transcript)

        if not q_keywords:
            return 0.0

        overlap = q_keywords.intersection(a_keywords)
        
        # Calculate overlap ratio relative to question keywords
        overlap_ratio = len(overlap) / len(q_keywords)
        
        # Drift score is the inverse of overlap: 0 means no drift, 100 means total drift
        drift_score = (1.0 - overlap_ratio) * 100.0
        
        logger.info(
            "topic_drift_detector | q_keys: %d | overlap: %d | drift_score: %.2f",
            len(q_keywords),
            len(overlap),
            drift_score,
        )
        return drift_score
