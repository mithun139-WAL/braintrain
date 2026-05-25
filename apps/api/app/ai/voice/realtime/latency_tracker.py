import time
import logging
from typing import Dict, List

logger = logging.getLogger("latency_tracker")

class LatencyTracker:
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.stage_starts: Dict[str, float] = {}
        self.rolling_metrics: Dict[str, List[float]] = {
            "stt": [],
            "policy": [],
            "prompt": [],
            "llm": [],
            "tts": [],
            "playback": [],
            "total": [],
        }

    def track_stage_start(self, stage_name: str) -> None:
        """Marks the start timestamp of a stage."""
        self.stage_starts[stage_name.lower()] = time.perf_counter()

    def track_stage_end(self, stage_name: str) -> float:
        """
        Marks the end timestamp of a stage, calculates duration,
        adds it to rolling metrics, and returns the duration in ms.
        """
        stage_key = stage_name.lower()
        start = self.stage_starts.pop(stage_key, None)
        if start is None:
            return 0.0
        
        duration_ms = (time.perf_counter() - start) * 1000.0
        
        if stage_key in self.rolling_metrics:
            self.rolling_metrics[stage_key].append(duration_ms)
            if len(self.rolling_metrics[stage_key]) > self.window_size:
                self.rolling_metrics[stage_key].pop(0)

        logger.info("latency_tracker | stage: %s | duration: %.2fms", stage_key, duration_ms)
        return duration_ms

    def get_avg(self, stage_name: str) -> float:
        """Returns the rolling average of a stage in ms."""
        values = self.rolling_metrics.get(stage_name.lower(), [])
        return sum(values) / len(values) if values else 0.0

    def get_metrics(self) -> Dict[str, float]:
        """Returns the rolling averages of all stages."""
        return {stage: self.get_avg(stage) for stage in self.rolling_metrics}
