import logging

logger = logging.getLogger("pressure_engine")

class PressureEngine:
    def adjust_pressure(self, confidence_score: float, hesitation_score: float) -> str:
        """
        Dynamically adjusts interviewer pressure level: LOW, NORMAL, or HIGH.
        """
        # If candidate is struggling (low confidence or high hesitation) -> reduce pressure
        if confidence_score < 40.0 or hesitation_score > 50.0:
            pressure = "LOW"
        # If candidate is very strong (high confidence and low hesitation) -> escalate pressure to challenge them
        elif confidence_score > 75.0 and hesitation_score < 20.0:
            pressure = "HIGH"
        else:
            pressure = "NORMAL"

        logger.info(
            "pressure_engine | confidence: %.2f | hesitation: %.2f | pressure_level: %s",
            confidence_score,
            hesitation_score,
            pressure,
        )
        return pressure
