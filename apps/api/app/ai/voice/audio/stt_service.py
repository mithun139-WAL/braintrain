import os
import httpx
import logging
import time

logger = logging.getLogger("stt_service")

class STTService:
    def __init__(self, api_key: str, base_url: str, model: str):
        """
        Service to handle Speech-To-Text requests.
        
        :param api_key: The provider API key.
        :param base_url: The provider base URL.
        :param model: The transcription model to use.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def transcribe(self, wav_path: str) -> str:
        """
        Uploads a WAV file to the transcription provider.
        Measures transcription latency using time.perf_counter().
        Cleans up the temporary file afterward to prevent leaks.
        
        :param wav_path: Path to the WAV file.
        :return: Transcribed text, or empty string on error.
        """
        transcription = ""
        start_time = time.perf_counter()
        
        if not os.path.exists(wav_path):
            logger.error("WAV file path does not exist for transcription: %s", wav_path)
            return ""

        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                with open(wav_path, "rb") as f:
                    response = await client.post(
                        f"{self.base_url}/audio/transcriptions",
                        headers=headers,
                        files={"file": (wav_path, f, "audio/wav")},
                        data={
                            "model": self.model,
                            "response_format": "json",
                        },
                        timeout=30.0,
                    )
                if response.status_code == 200:
                    transcription = response.json().get("text", "").strip()
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    logger.info("transcription_completed | text: %s | latency: %.2fms", transcription[:120], latency_ms)
                else:
                    logger.error("STT provider API error %d: %s", response.status_code, response.text)
        except Exception as exc:
            logger.error("Failed to transcribe user audio: %s", exc)
        finally:
            try:
                os.remove(wav_path)
            except OSError as exc:
                logger.error("Failed to clean up WAV temp file: %s", exc)

        return transcription
