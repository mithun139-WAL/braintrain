import logging

logger = logging.getLogger("speaker_formatter")

class SpeakerFormatter:
    def __init__(self, voice_map: dict[str, str] = None):
        self.panelists = ["Marcus", "Sarah", "David"]
        self.voice_map = voice_map or {
            "Marcus": "en-US-GuyNeural",
            "Sarah": "en-US-JennyNeural",
            "David": "en-US-ChristopherNeural",
            "Interviewer": "en-US-AriaNeural",
        }

    def format_speaker(self, text: str, current_sequence: int, is_panel_mode: bool) -> tuple[str, str, str]:
        """
        Determines the speaker name, returns the clean text with speaker prefix removed,
        and provides the mapped TTS voice.
        
        :return: A tuple of (speaker_name, clean_text, tts_voice)
        """
        if not is_panel_mode:
            voice = self.voice_map.get("Interviewer", "en-US-AriaNeural")
            return "Interviewer", text, voice

        lower_text = text.lower().strip()
        matched_speaker = None
        clean_text = text

        for p in self.panelists:
            prefix_options = [
                p.lower() + ":",
                p.lower() + " here:",
                "this is " + p.lower() + ":",
                "this is " + p.lower() + " here:"
            ]
            for opt in prefix_options:
                if lower_text.startswith(opt):
                    matched_speaker = p
                    # Find colon index to extract the actual speech content
                    colon_idx = text.find(":")
                    if colon_idx != -1:
                        clean_text = text[colon_idx + 1:].strip()
                    break
            if matched_speaker:
                break

        # Fallback to round robin mapping if no explicit speaker prefix was matched
        if not matched_speaker:
            matched_speaker = self.panelists[current_sequence % 3]

        voice = self.voice_map.get(matched_speaker, "en-US-AriaNeural")
        logger.info("speaker_formatter | speaker: %s | voice: %s", matched_speaker, voice)
        return matched_speaker, clean_text, voice
