import os
import logging
from typing import Dict, Optional
from app.ai.voice.simulation.personality_profiles import PersonalityProfile
from app.ai.voice.simulation.personality_loader import PersonalityLoader

logger = logging.getLogger("personality_registry")

class PersonalityRegistry:
    def __init__(self, personas_dir: str = "personas"):
        self.personas_dir = personas_dir
        self.profiles: Dict[str, PersonalityProfile] = {}
        self._load_default_profiles()

    def get_profile(self, name: str) -> PersonalityProfile:
        """
        Retrieves a loaded profile by key. Falls back to a default standard profile if not found.
        """
        # Clean name format
        key = name.lower().replace(" ", "_")
        if key in self.profiles:
            return self.profiles[key]

        # Try loading dynamically from directory
        profile = self._try_load_dynamic(key)
        if profile:
            self.profiles[key] = profile
            return profile

        # Fallback profile
        logger.warning("Profile '%s' not found in registry. Using standard fallback.", name)
        return self.profiles["standard_interviewer"]

    def register_profile(self, key: str, profile: PersonalityProfile) -> None:
        self.profiles[key.lower()] = profile

    def _load_default_profiles(self) -> None:
        """Loads static baseline profiles."""
        standard = PersonalityProfile(
            name="Standard Interviewer",
            archetype="Professional Coach",
            pacing_speed=1.0,
            interruption_frequency=0.4,
            silence_tolerance=1.0,
            skepticism_level=0.5,
            technical_depth=0.5,
            followup_aggressiveness=0.5,
            verbosity_tolerance=0.5,
            ambiguity_tolerance=0.5,
            pressure_intensity=0.5,
            conversational_warmth=0.6,
            acknowledgment_patterns=["Got it.", "Makes sense.", "Okay."]
        )
        self.profiles["standard_interviewer"] = standard

    def _try_load_dynamic(self, key: str) -> Optional[PersonalityProfile]:
        # Walk directories in search of key.yaml or key.json
        if not os.path.exists(self.personas_dir):
            return None

        for root, _, files in os.walk(self.personas_dir):
            for file in files:
                fname, ext = os.path.splitext(file)
                if fname.lower() == key and ext in [".yaml", ".yml", ".json"]:
                    filepath = os.path.join(root, file)
                    return PersonalityLoader.load_from_file(filepath)
        return None
