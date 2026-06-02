from dataclasses import dataclass

@dataclass
class BehavioralSignals:
    hesitation_score: float = 0.0
    confidence_score: float = 50.0
    verbosity_score: float = 50.0
    topic_drift_score: float = 0.0
    response_pacing_score: float = 50.0
    clarity_signal: float = 50.0
    pressure_signal: float = 50.0
