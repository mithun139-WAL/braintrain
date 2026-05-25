import re
import logging

logger = logging.getLogger("response_formatter")

class ResponseFormatter:
    def __init__(self):
        # Conversational filler/politeness regex
        self.polite_filler_regex = re.compile(
            r"^(?:great|excellent|awesome|perfect|amazing|wonderful|fantastic|thank you for sharing|thanks for the explanation|thank you|good response|thanks|glad to hear that|that is a great answer|that's a great answer)[!.,\s]*",
            re.IGNORECASE
        )

    def format_response(self, text: str) -> str:
        """
        Formats response content for natural TTS execution.
        Strips repetitive robotic greetings, excessive polite praise, and normalizes punctuation.
        """
        if not text:
            return ""

        # 1. Strip repetitive polite filler prefixes
        formatted = text.strip()
        while True:
            new_formatted = self.polite_filler_regex.sub("", formatted).strip()
            if new_formatted == formatted:
                break
            formatted = new_formatted

        # Capitalize the first letter if it got lowercased by the regex sub
        if formatted and formatted[0].islower():
            formatted = formatted[0].upper() + formatted[1:]

        # 2. Normalize ending punctuation
        if formatted and formatted[-1] not in (".", "?", "!", ";"):
            formatted += "."

        # 3. Prevent overlong responses for voice interactions (soft clamp to ~350 characters / ~60 words if needed)
        # We don't truncate aggressively, but we log a warning if it exceeds limits
        word_count = len(formatted.split())
        if word_count > 60:
            logger.warning("response_formatter | long response detected: %d words", word_count)

        logger.debug("response_formatter | original: %s | formatted: %s", text[:80], formatted[:80])
        return formatted
