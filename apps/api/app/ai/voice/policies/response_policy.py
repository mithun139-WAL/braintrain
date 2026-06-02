import logging

logger = logging.getLogger("response_policy")

class ResponsePolicy:
    def __init__(self):
        """
        Policy to select the conversational tone of the interviewer.
        """
        pass

    def select_tone(self, state) -> str:
        """
        Selects the conversational tone based on candidate state metrics and pressure level.
        """
        tone = "neutral"
        
        signals = getattr(state, "behavioral_signals", None)
        confidence_score = signals.confidence_score if signals else state.candidate.confidence_score
        verbosity_score = signals.verbosity_score if signals else state.candidate.verbosity_score
        pressure_level = getattr(state, "pressure_level", "NORMAL")

        if confidence_score < 40.0:
            tone = "encouraging"
        elif verbosity_score > 75.0:
            tone = "concise"
        elif pressure_level == "HIGH" or state.difficulty == "HARD":
            tone = "challenging"

        logger.info("response_tone_selected | tone: %s | pressure: %s", tone, pressure_level)
        return tone
