import random
from typing import List
from app.ai.voice.simulation.personality_profiles import PersonalityProfile
from app.ai.voice.simulation.interviewer_state import InterviewerState

class RealismEngine:
    @staticmethod
    def calculate_thinking_pause(profile: PersonalityProfile, state: InterviewerState) -> float:
        """
        Calculates a dynamic delay duration in seconds before speaking to simulate human thinking.
        Pacing speed, frustration, and skepticism dictate the timing.
        """
        # Base pause: 0.4 seconds
        base_pause = 0.4 / max(0.5, profile.pacing_speed)
        
        # High frustration decreases thinking delay
        frustration_factor = 1.0 - (state.frustration_level * 0.5)
        
        # Skepticism slightly increases thinking delay (simulates critical evaluation)
        skepticism_factor = 1.0 + (state.skepticism_index * 0.4)

        pause = base_pause * frustration_factor * skepticism_factor
        # Random jitter
        jitter = random.uniform(-0.1, 0.1)
        
        return max(0.2, min(2.0, pause + jitter))

    @staticmethod
    def inject_conversational_filler(text: str, profile: PersonalityProfile, state: InterviewerState) -> str:
        """
        Prepends a realistic verbal filler/acknowledgement matching the interviewer's style.
        """
        if not text or len(text) < 10:
            return text

        # Highly warm or patient interviewers use welcoming acknowledgements
        if state.active_warmth > 0.7 and random.random() < 0.4:
            fillers = ["Perfect.", "Great explanation.", "Got it, that makes sense.", "Understood."]
            return f"{random.choice(fillers)} {text}"

        # Skeptical or distant architects use critical transitions
        if state.skepticism_index > 0.6 and random.random() < 0.5:
            if profile.acknowledgment_patterns:
                prefix = random.choice(profile.acknowledgment_patterns)
                # Avoid doubling up if prefix is already at the start
                if not text.lower().startswith(prefix.split()[0].lower()):
                    return f"{prefix} {text}"
            else:
                fillers = ["Hmm, okay.", "Right.", "Understood, but..."]
                return f"{random.choice(fillers)} {text}"

        # Frustrated/impatient interviewers jump straight to query without padding
        if state.frustration_level > 0.6:
            return text

        # Default standard filler injection
        if random.random() < 0.25:
            fillers = ["Alright.", "Hmm.", "Okay."]
            return f"{random.choice(fillers)} {text}"

        return text
