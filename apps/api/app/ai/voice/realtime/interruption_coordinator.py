import logging
from typing import Any

logger = logging.getLogger("interruption_coordinator")

class InterruptionCoordinator:
    def __init__(self):
        self.is_interrupted = False

    def can_interrupt(self, state: Any, signals: Any) -> bool:
        """
        Determines if the interviewer is eligible to interrupt the candidate.
        Ensures we only barge in when candidate is rambling or drift is high.
        """
        if not signals:
            return False

        # Ramble checking
        if signals.verbosity_score > 75.0:
            logger.info("interruption_coordinator | candidate rambling | interruption allowed")
            return True

        # Complete topic drift
        if signals.topic_drift_score > 80.0:
            logger.info("interruption_coordinator | candidate topic drift high | interruption allowed")
            return True

        return False

    def schedule_interrupt(self) -> None:
        """Sets the active interruption flag."""
        self.is_interrupted = True
        logger.debug("interruption_coordinator | interruption scheduled")

    def cancel_interrupt(self) -> None:
        """Clears the active interruption flag."""
        self.is_interrupted = False
        logger.debug("interruption_coordinator | interruption cleared")
