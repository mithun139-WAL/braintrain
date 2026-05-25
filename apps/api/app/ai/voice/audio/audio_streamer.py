import asyncio
import logging
import time
import miniaudio
from livekit import rtc

logger = logging.getLogger("audio_streamer")

class AudioStreamer:
    def __init__(self, audio_source: rtc.AudioSource):
        """
        Streamer that decodes MP3 bytes and captures them as PCM audio frames.
        
        :param audio_source: LiveKit RTC AudioSource.
        """
        self.audio_source = audio_source
        self._is_streaming = False

    async def stream_mp3(self, mp3_bytes: bytes, stop_check_func=None) -> None:
        """
        Decodes MP3 bytes to 24kHz mono 16-bit PCM and streams them in 20ms chunks.
        Measures decode latency and streaming performance.
        
        :param mp3_bytes: MP3 audio bytes.
        :param stop_check_func: Optional callback returning True/False to monitor interruption.
        """
        if not mp3_bytes:
            return

        start_decode = time.perf_counter()
        
        try:
            decoded = miniaudio.decode(
                mp3_bytes,
                output_format=miniaudio.SampleFormat.SIGNED16,
                nchannels=1,
                sample_rate=24000,
            )
            pcm_data: bytes = decoded.samples.tobytes()
        except Exception as exc:
            logger.error("TTS audio decode failed: %s", exc)
            return

        decode_latency_ms = (time.perf_counter() - start_decode) * 1000
        logger.info("audio_streaming_started | size: %d bytes | decode latency: %.2fms", len(pcm_data), decode_latency_ms)

        sample_rate = 24000
        num_channels = 1
        chunk_duration = 0.020  # 20 ms
        bytes_per_chunk = int(sample_rate * chunk_duration) * 2 * num_channels  # 960 bytes
        offset = 0

        self._is_streaming = True
        try:
            while self._is_streaming and offset < len(pcm_data):
                # Verify if playback has been cancelled or agent is stopping
                if stop_check_func and not stop_check_func():
                    logger.info("Audio streaming interrupted by coordinator.")
                    break

                chunk = pcm_data[offset:offset + bytes_per_chunk]
                samples_per_channel = len(chunk) // (2 * num_channels)
                frame = rtc.AudioFrame(chunk, sample_rate, num_channels, samples_per_channel)
                await self.audio_source.capture_frame(frame)
                await asyncio.sleep(chunk_duration)
                offset += bytes_per_chunk
        except Exception as exc:
            logger.error("Error streaming PCM chunks: %s", exc)
        finally:
            self._is_streaming = False
            logger.info("audio_streaming_completed")
