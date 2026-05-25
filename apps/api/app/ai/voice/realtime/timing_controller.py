import logging
from typing import Any

logger = logging.getLogger("timing_controller")

class TimingController:
    def __init__(self):
        pass

    def calculate_response_delay(self, decision: Any, signals: Any) -> float:
        """
        Calculates conversational pause delay (in seconds) to mimic human rhythm.
        - Thoughtful delay (0.8s - 1.5s) for technical followups or hard difficulties.
        - Fast transition (0.2s - 0.4s) for empty short inputs or simple prompts.
        - Neutral pacing (0.5s - 0.8s) for standard turns.
        """
        action = decision.action.value
        
        # 1. Base delays on actions
        if action == "ASK_CLARIFICATION":
            base_delay = 0.3
        elif action == "ASK_FOLLOWUP":
            base_delay = 0.9
        elif action == "MOVE_TOPIC":
            base_delay = 1.2
        elif action == "ENCOURAGE":
            base_delay = 0.4
        else:
            base_delay = 0.6

        # 2. Adjust based on behavioral signals and pressure
        if signals:
            # Low confidence candidates get gentler, slightly slower responses (thoughtful pause)
            if signals.confidence_score < 40.0:
                base_delay += 0.2
            
            # High pressure pacing is slightly sharper and faster
            if signals.pressure_signal > 75.0:
                base_delay = max(0.2, base_delay - 0.15)

        logger.info(
            "timing_controller | calculated delay: %.2fs | action: %s",
            base_delay,
            action,
        )
        return base_delay
