import logging

logger = logging.getLogger("verbosity_analyzer")

class VerbosityAnalyzer:
    def analyze(self, transcript: str) -> float:
        """
        Analyzes answer length and repetitive patterns to compute a verbosity score (0-100).
        """
        words = transcript.split()
        count = len(words)
        
        if count == 0:
            return 0.0

        # Word count J-curve mapping
        if count < 15:
            base_score = 15.0 + (count / 15.0) * 20.0  # 15.0 to 35.0
        elif count <= 60:
            base_score = 35.0 + ((count - 15) / 45.0) * 25.0  # 35.0 to 60.0
        elif count <= 120:
            base_score = 60.0 + ((count - 60) / 60.0) * 25.0  # 60.0 to 85.0
        else:
            base_score = 85.0 + min(15.0, ((count - 120) / 100.0) * 15.0)  # 85.0 to 100.0

        # Repetitive vocabulary penalty
        unique_words = set(w.lower().strip(".,?!:;()") for w in words)
        if count > 15:
            uniqueness_ratio = len(unique_words) / count
            if uniqueness_ratio < 0.65:
                # Add redundancy score based on how repetitive the vocab is
                base_score = min(100.0, base_score + (0.65 - uniqueness_ratio) * 40.0)

        logger.info("verbosity_analyzer | word_count: %d | verbosity_score: %.2f", count, base_score)
        return base_score
