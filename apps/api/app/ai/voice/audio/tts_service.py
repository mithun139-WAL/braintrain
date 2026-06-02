import logging
import time
import edge_tts

logger = logging.getLogger("tts_service")

class TTSService:
    def __init__(self, voice_map: dict[str, str] = None):
        """
        Service to handle Text-To-Speech generation.
        
        :param voice_map: Optional custom voice name mapping.
        """
        self.voice_map = voice_map or {
            "Marcus": "en-US-GuyNeural",
            "Sarah": "en-US-JennyNeural",
            "David": "en-US-ChristopherNeural",
            "Interviewer": "en-US-AriaNeural",
        }

    async def synthesize(self, text: str, voice: str) -> bytes:
        """
        Synthesizes speech text into MP3 bytes using Edge TTS.
        Measures TTS synthesis latency using time.perf_counter().
        
        :param text: The text to speak.
        :param voice: Speaker name (e.g. 'Marcus') or direct Edge TTS voice string.
        :return: MP3 audio bytes, or empty bytes on error.
        """
        start_time = time.perf_counter()
        logger.info("tts_generation_started | voice: %s | text: %s...", voice, text[:60])
        
        voice_name = self.voice_map.get(voice, voice)
        if not voice_name:
            voice_name = "en-US-AriaNeural"  # Fallback default

        mp3_chunks: list[bytes] = []
        try:
            communicate = edge_tts.Communicate(text, voice_name)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_chunks.append(chunk["data"])
        except Exception as exc:
            logger.error("TTS generation failed: %s", exc)
            return b""

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info("tts_generation_completed | chunks: %d | latency: %.2fms", len(mp3_chunks), latency_ms)
        
        return b"".join(mp3_chunks)
