import logging

logger = logging.getLogger("turn_predictor")

class TurnPredictor:
    def __init__(self):
        pass

    def predict_turn_end(self, transcript: str, silence_duration_sec: float) -> bool:
        """
        Heuristically predicts if the user is ending their turn.
        Returns True if VAD silence delay exceeds threshold compared to answer complexity.
        """
        words = transcript.split()
        count = len(words)
        
        if count == 0:
            return False

        # If answer is short and there is a pause, it is highly likely to be a turn end
        if count < 15:
            # Short answers need very short silence to be considered finished
            threshold = 0.5
        elif count < 60:
            # Medium answers
            threshold = 0.8
        else:
            # Very long answers might have natural mid-sentence pauses, require longer silence
            threshold = 1.2

        is_end = silence_duration_sec >= threshold
        
        if is_end:
            logger.debug(
                "turn_predictor | turn_end predicted | count: %d | silence: %.2fs (threshold: %.1fs)",
                count,
                silence_duration_sec,
                threshold,
            )
        return is_end
