import logging

logger = logging.getLogger("metrics")

class RealtimeMetrics:
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.hesitations = []
        self.verbosities = []
        self.drifts = []

    def add_turn_metrics(self, hesitation: float, verbosity: float, drift: float) -> None:
        """Adds metrics for a single turn, preserving the rolling window size."""
        self.hesitations.append(hesitation)
        self.verbosities.append(verbosity)
        self.drifts.append(drift)

        if len(self.hesitations) > self.window_size:
            self.hesitations.pop(0)
            self.verbosities.pop(0)
            self.drifts.pop(0)

        logger.info(
            "metrics | rolling_size: %d | avg_hes: %.2f | avg_verb: %.2f | avg_drift: %.2f",
            len(self.hesitations),
            self.avg_hesitation,
            self.avg_verbosity,
            self.avg_drift,
        )

    @property
    def avg_hesitation(self) -> float:
        return sum(self.hesitations) / len(self.hesitations) if self.hesitations else 0.0

    @property
    def avg_verbosity(self) -> float:
        return sum(self.verbosities) / len(self.verbosities) if self.verbosities else 50.0

    @property
    def avg_drift(self) -> float:
        return sum(self.drifts) / len(self.drifts) if self.drifts else 0.0
