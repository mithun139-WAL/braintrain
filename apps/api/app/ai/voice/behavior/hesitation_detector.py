import logging

logger = logging.getLogger("hesitation_detector")

class HesitationDetector:
    def __init__(self):
        self.filler_phrases = ["umm", "uh", "maybe", "sort of", "kind of", "i think", "like", "probably", "not sure", "don't know", "dont know"]

    def detect(self, transcript: str, response_time_ms: float) -> float:
        """
        Determines hesitation score (0-100) based on filler words and pause duration.
        """
        if not transcript:
            return 100.0

        lower_text = transcript.lower().strip()
        
        # 1. Count filler words
        count = 0
        for phrase in self.filler_phrases:
            count += lower_text.count(phrase)

        # 2. Estimate pause delay contribution (response delay > 2500ms suggests hesitation)
        pause_score = 0.0
        if response_time_ms > 2500:
            pause_score = min(50.0, (response_time_ms - 2500) / 100.0) # e.g. 5 seconds delay is 25.0 score

        # 3. Combine counts (each filler phrase adds 15 points)
        hesitation_score = min(100.0, count * 15.0 + pause_score)
        
        logger.info(
            "hesitation_detector | fillers_count: %d | pause_score: %.2f | hesitation_score: %.2f",
            count,
            pause_score,
            hesitation_score,
        )
        return hesitation_score
