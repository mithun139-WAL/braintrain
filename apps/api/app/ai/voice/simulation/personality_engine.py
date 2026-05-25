import logging
from typing import Dict, Any, Tuple
from app.ai.voice.simulation.personality_profiles import PersonalityProfile
from app.ai.voice.simulation.interviewer_state import InterviewerState
from app.ai.voice.simulation.personality_registry import PersonalityRegistry
from app.ai.voice.simulation.adaptation_engine import AdaptationEngine
from app.ai.voice.simulation.realism_engine import RealismEngine

logger = logging.getLogger("personality_engine")

class PersonalityEngine:
    def __init__(self, personas_dir: str = "personas"):
        self.registry = PersonalityRegistry(personas_dir)
        self.active_profile: PersonalityProfile = self.registry.get_profile("standard_interviewer")
        self.active_state = InterviewerState(
            initial_warmth=self.active_profile.conversational_warmth,
            initial_skepticism=self.active_profile.skepticism_level
        )

    def select_persona(self, persona_name: str) -> None:
        """
        Loads and activates a new persona profile. Resets current states.
        """
        self.active_profile = self.registry.get_profile(persona_name)
        self.active_state = InterviewerState(
            initial_warmth=self.active_profile.conversational_warmth,
            initial_skepticism=self.active_profile.skepticism_level
        )
        logger.info("Activated interviewer persona: %s (%s)", self.active_profile.name, self.active_profile.archetype)

    def process_user_turn(self, topic_drift: float, hesitation: float, verbosity: float) -> Tuple[Dict[str, Any], str]:
        """
        Processes candidate metrics to adapt interviewer state and retrieve adapted parameters.
        Returns:
            (adapted_parameters, prompt_instructions)
        """
        # 1. Update dynamic warmth, patience, frustration
        self.active_state.adjust_impressions(topic_drift, hesitation, verbosity)

        # 2. Get turn & pacing adaptations
        turn_params = AdaptationEngine.get_turn_adaptation(self.active_profile, self.active_state)
        followup_params = AdaptationEngine.get_followup_adaptation(self.active_profile, self.active_state)

        adapted_params = {**turn_params, **followup_params}

        # 3. Retrieve adjusted prompt directives
        prompt_instruction = AdaptationEngine.get_prompt_instruction(self.active_profile, self.active_state)

        return adapted_params, prompt_instruction

    def format_interviewer_speech(self, text: str) -> str:
        """
        Prepares output response content with verbal fillers matching active state.
        """
        return RealismEngine.inject_conversational_filler(text, self.active_profile, self.active_state)

    def get_thinking_delay(self) -> float:
        """
        Calculates pause duration to simulate human thinking.
        """
        return RealismEngine.calculate_thinking_pause(self.active_profile, self.active_state)
