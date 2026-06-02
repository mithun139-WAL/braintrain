from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class PersonalityProfile:
    name: str
    archetype: str
    pacing_speed: float = 1.0           # Speech/turn speed multiplier (0.5 to 1.5)
    interruption_frequency: float = 0.5  # Probability/speed of interrupting (0.0 to 1.0)
    silence_tolerance: float = 1.0      # Seconds of silence tolerated before taking turn
    skepticism_level: float = 0.5       # Likelihood of questioning assumptions (0.0 to 1.0)
    technical_depth: float = 0.5        # Depth level of tech probes (0.0 to 1.0)
    followup_aggressiveness: float = 0.5 # Deep drill probability (0.0 to 1.0)
    verbosity_tolerance: float = 0.5    # Cut off wordy answers (0.0 to 1.0)
    ambiguity_tolerance: float = 0.5    # Clarification trigger threshold (0.0 to 1.0)
    pressure_intensity: float = 0.5     # Pressure scaling intensity (0.0 to 1.0)
    conversational_warmth: float = 0.5  # Tone warmth parameter (0.0 to 1.0)
    challenge_escalation: str = "Standard" # Escalation algorithm name
    acknowledgment_patterns: List[str] = field(default_factory=list)
    custom_prompts: Dict[str, str] = field(default_factory=dict)
