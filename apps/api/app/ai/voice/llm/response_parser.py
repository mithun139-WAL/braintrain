import re
import time
import logging

logger = logging.getLogger("response_parser")

class ResponseParser:
    def __init__(self):
        # Match speaker prefix styles like "Marcus:", "**Marcus**:", "David here:", "Sarah says:"
        self.speaker_prefix_regex = re.compile(
            r"^\*?\*?(Marcus|Sarah|David|Interviewer)\*?\*?\s*(?:here|says)?\s*:\s*",
            re.IGNORECASE
        )

    def parse(self, response: str) -> str:
        """
        Cleans and normalizes raw LLM output, removing redundant formatting, 
        markdown symbols, surrounding quotes, or repeated speaker prefixes.
        """
        start_time = time.perf_counter()
        if not response:
            return ""

        cleaned = response.strip()

        # 1. Strip surrounding quotation marks if the model quoted its entire response
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1].strip()

        # 2. Normalize and strip bold speaker names (e.g., **Marcus**: hello -> Marcus: hello)
        cleaned = re.sub(r"^\*?\*?([A-Za-z]+)\*?\*?\s*:\s*", r"\1: ", cleaned)

        # 3. Strip general markdown formatting (e.g., **bold**, *italics*, `code`)
        cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
        cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
        cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
        cleaned = re.sub(r"__([^_]+)__", r"\1", cleaned)

        # 4. Remove list markers, bullets, and hash headers
        cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"^\s*\d+\.\s+", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"^\s*#+\s+", "", cleaned, flags=re.MULTILINE)

        # 5. Clean up duplicate spaces
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        latency = time.perf_counter() - start_time
        logger.info("response_parsed | latency: %.6fs | original_len: %d | cleaned_len: %d", 
                    latency, len(response), len(cleaned))
        return cleaned
