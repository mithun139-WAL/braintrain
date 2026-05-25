from typing import Dict, Any
from app.ai.voice.simulation.personality_profiles import PersonalityProfile
from app.ai.voice.simulation.interviewer_state import InterviewerState

class AdaptationEngine:
    @staticmethod
    def get_turn_adaptation(profile: PersonalityProfile, state: InterviewerState) -> Dict[str, Any]:
        """
        Dynamically adjusts speech-onset timeouts and interruption thresholds.
        """
        # If patience drops, we decrease silence tolerance (becoming quicker to speak/interrupt)
        adjusted_silence_tol = profile.silence_tolerance * (0.5 + 0.5 * state.patience_level)
        
        # Interruption frequency determines threshold sensitivity
        interruption_threshold = 200.0 - (profile.interruption_frequency * 80.0)
        if state.frustration_level > 0.6:
            # More aggressive interruption if frustrated
            interruption_threshold -= 20.0

        return {
            "silence_tolerance": max(0.5, min(3.0, adjusted_silence_tol)),
            "interruption_threshold": max(50.0, interruption_threshold)
        }

    @staticmethod
    def get_followup_adaptation(profile: PersonalityProfile, state: InterviewerState) -> Dict[str, Any]:
        """
        Determines target technical depth and followup depth.
        """
        # Under high skepticism, we drill deeper
        target_drill_depth = 1
        if profile.followup_aggressiveness > 0.7 or state.skepticism_index > 0.7:
            target_drill_depth = 3
        elif profile.followup_aggressiveness > 0.4:
            target_drill_depth = 2

        # Scale technical depth by candidate performance indicators
        target_tech_depth = profile.technical_depth
        if state.consecutive_vague_answers > 1:
            # Reduce technical difficulty to check basic understanding
            target_tech_depth = max(0.2, target_tech_depth - 0.2)

        return {
            "target_drill_depth": target_drill_depth,
            "target_tech_depth": target_tech_depth
        }

    @staticmethod
    def get_prompt_instruction(profile: PersonalityProfile, state: InterviewerState) -> str:
        """
        Generates system prompt directives matching the current emotional profile.
        """
        instructions = []
        instructions.append(f"Your persona is a {profile.archetype} named '{profile.name}'.")
        
        # Warmth modifiers
        if state.active_warmth > 0.7:
            instructions.append("Maintain an encouraging, warm tone. Acknowledge candidate responses supportively.")
        elif state.active_warmth < 0.3:
            instructions.append("Maintain a strict, direct, and slightly distant professional tone.")

        # Skepticism and Drilling
        if state.skepticism_index > 0.7:
            instructions.append("Actively challenge scaling assumptions, request concrete metrics, and probe distributed tradeoffs.")
        
        # Frustration/Patience modifiers
        if state.frustration_level > 0.7:
            instructions.append("Interject directly if answers are overly verbose. Do not let the candidate avoid answering specific questions.")

        return " ".join(instructions)
