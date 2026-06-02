import logging

logger = logging.getLogger("confidence_tracker")

class ConfidenceTracker:
    def update_confidence(self, current_confidence: float, hesitation_score: float, verbosity_score: float) -> float:
        """
        Updates the running candidate confidence estimation (0-100).
        """
        change = 0.0

        # Hesitation reduces confidence
        if hesitation_score > 40.0:
            change -= (hesitation_score - 40.0) * 0.35
        elif hesitation_score < 20.0:
            # Low hesitation increases confidence
            change += (20.0 - hesitation_score) * 0.20

        # Verbosity checks (extreme rambling reduces score)
        if verbosity_score > 75.0:
            change -= (verbosity_score - 75.0) * 0.25
        elif 30.0 <= verbosity_score <= 60.0:
            # Good concise answer structure boosts score
            change += 3.0

        new_confidence = min(100.0, max(0.0, current_confidence + change))
        logger.info(
            "confidence_tracker | old_confidence: %.2f | new_confidence: %.2f | change: %.2f",
            current_confidence,
            new_confidence,
            change,
        )
        return new_confidence
