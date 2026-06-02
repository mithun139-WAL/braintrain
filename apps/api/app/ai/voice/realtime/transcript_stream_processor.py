import logging
from typing import Dict, Any

logger = logging.getLogger("transcript_stream_processor")

class TranscriptStreamProcessor:
    def __init__(self):
        pass

    def process_partial(self, partial_text: str) -> Dict[str, Any]:
        """
        Analyzes intermediate text chunks to detect early conversational intent 
        before the STT transcription completes.
        """
        if not partial_text:
            return {"intent": "none", "concepts": []}

        lower_text = partial_text.lower().strip()
        concepts = []
        
        # Check for early keywords
        for kw in ["scaling", "cache", "optimize", "database", "security", "cloud"]:
            if kw in lower_text:
                concepts.append(kw)

        # Early intent heuristic
        intent = "elaboration"
        if any(w in lower_text for w in ["yes", "yeah", "sure", "correct", "exactly"]):
            intent = "agreement"
        elif any(w in lower_text for w in ["no", "never", "disagree", "actually"]):
            intent = "correction"

        logger.debug("transcript_stream_processor | partial analyzed | intent: %s | concepts: %s", intent, concepts)
        return {
            "intent": intent,
            "concepts": concepts,
        }

    def process_final(self, final_text: str) -> Dict[str, Any]:
        """Finalizes intent analysis on complete text."""
        return self.process_partial(final_text)
