import logging

logger = logging.getLogger("panel_manager")

class PanelManager:
    def __init__(self, voice_map: dict[str, str] = None):
        """
        Coordinates panel interviewer identity mapping and speaking voices.
        """
        self.voice_map = voice_map or {
            "Marcus": "en-US-GuyNeural",
            "Sarah": "en-US-JennyNeural",
            "David": "en-US-ChristopherNeural",
            "Interviewer": "en-US-AriaNeural",
        }
        self.panelists = ["Marcus", "Sarah", "David"]

    def select_speaker(self, text: str, question_sequence: int, is_panel_mode: bool) -> str:
        """
        Selects the active speaker's name based on response content or turn index.
        
        :param text: The raw text response containing speaker identities.
        :param question_sequence: Current turn index.
        :param is_panel_mode: True if panel mode is enabled.
        :return: Selected speaker string.
        """
        if not is_panel_mode:
            logger.debug("panel_speaker_selected | mode: single | speaker: Interviewer")
            return "Interviewer"

        lower_text = text.lower().strip()
        matched_panelist = None
        for p in self.panelists:
            prefix_options = [
                p.lower() + ":",
                p.lower() + " here:",
                "this is " + p.lower() + ":",
                "this is " + p.lower() + " here:"
            ]
            if any(lower_text.startswith(opt) for opt in prefix_options):
                matched_panelist = p
                break

        if matched_panelist:
            speaker = matched_panelist
        else:
            # Fallback to round-robin mapping based on turn sequence index
            speaker = self.panelists[question_sequence % 3]

        logger.info("panel_speaker_selected | mode: panel | speaker: %s", speaker)
        return speaker

    def get_voice(self, speaker: str) -> str:
        """Retrieves the mapped Edge TTS neural voice string for a speaker."""
        return self.voice_map.get(speaker, "en-US-AriaNeural")

    def format_response(self, text: str, speaker: str, is_panel_mode: bool) -> str:
        """
        Strips speaker introduction prefixes from generated audio text.
        
        :param text: Raw answer text.
        :param speaker: Active speaker name.
        :param is_panel_mode: True if panel mode is active.
        :return: Trimmed text content.
        """
        if not is_panel_mode:
            return text

        lower_text = text.lower().strip()
        prefix = speaker.lower() + ":"
        if lower_text.startswith(prefix):
            colon_idx = text.find(":")
            if colon_idx != -1:
                return text[colon_idx + 1:].strip()
        return text
