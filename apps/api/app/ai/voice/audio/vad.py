from dataclasses import dataclass
import numpy as np

@dataclass
class VADResult:
    is_speaking: bool
    speech_started: bool
    speech_ended: bool
    rms: float

class VoiceActivityDetector:
    def __init__(
        self,
        threshold: float = 200.0,
        silence_timeout: float = 0.8,
        sample_width: int = 2,
    ):
        """
        Voice Activity Detector utilizing RMS calculation.
        
        :param threshold: RMS energy threshold to trigger voice detection.
        :param silence_timeout: Time in seconds of consecutive silence to trigger speech stop.
        :param sample_width: Bytes per sample (2 for 16-bit PCM).
        """
        self.threshold = threshold
        self.silence_timeout = silence_timeout
        self.sample_width = sample_width
        self.reset()

    def reset(self) -> None:
        self.speaking = False
        self.silence_duration = 0.0

    def process_frame(
        self,
        frame_data: bytes,
        sample_rate: int = 16000,
        num_channels: int = 1,
    ) -> VADResult:
        samples = np.frombuffer(frame_data, dtype=np.int16)
        if len(samples) == 0:
            return VADResult(
                is_speaking=self.speaking,
                speech_started=False,
                speech_ended=False,
                rms=0.0,
            )

        rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))
        speech_started = False
        speech_ended = False

        if rms > self.threshold:
            if not self.speaking:
                speech_started = True
                self.speaking = True
            self.silence_duration = 0.0
        else:
            if self.speaking:
                # Calculate duration of the silent frame in seconds
                frame_duration = len(frame_data) / (sample_rate * self.sample_width * num_channels)
                self.silence_duration += frame_duration
                if self.silence_duration >= self.silence_timeout:
                    speech_ended = True
                    self.speaking = False
                    self.silence_duration = 0.0

        return VADResult(
            is_speaking=self.speaking,
            speech_started=speech_started,
            speech_ended=speech_ended,
            rms=rms,
        )
