from typing import Dict, Any, List
from app.ai.voice.memory.memory_types import MemoryType
from app.ai.voice.state.interview_state import InterviewState

class RetrievalPolicies:
    @staticmethod
    def get_policy_context(state: InterviewState) -> Dict[str, Any]:
        """
        Determines the interview context from the InterviewState.
        """
        # Guess phase based on current turn number or mode
        phase = "INTRO"
        turn_count = state.conversation.turn_count
        
        # Simple heuristic mapping turn count to phase
        if turn_count > 12:
            phase = "PRESSURE_ROUND"
        elif turn_count > 5:
            phase = "SYSTEM_DESIGN"
        else:
            phase = "INTRO"

        # Check if adaptive pressure is high
        stress_level = "NORMAL"
        if hasattr(state, "pressure_level") and state.pressure_level:
            stress_level = state.pressure_level
        elif hasattr(state, "behavioral_signals") and state.behavioral_signals:
            if state.behavioral_signals.pressure_signal > 70.0:
                stress_level = "HIGH"

        return {
            "interview_phase": phase,
            "current_topic": state.conversation.current_topic or "general",
            "stress_level": stress_level,
            "difficulty": state.difficulty
        }

    @staticmethod
    def get_query_filters(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns filters (allowed memory types, min importance) based on the context.
        """
        phase = context.get("interview_phase", "")
        stress_level = context.get("stress_level", "")
        
        allowed_types = [MemoryType.SEMANTIC, MemoryType.EPISODIC, MemoryType.BEHAVIORAL]
        min_importance = 0.3
        limit = 3

        if phase == "PRESSURE_ROUND" or stress_level == "HIGH":
            # Focus on behavioral characteristics (stress patterns, hesitations)
            allowed_types = [MemoryType.BEHAVIORAL, MemoryType.EPISODIC]
            min_importance = 0.5
            limit = 2
        elif phase == "INTRO":
            # Focus on semantic skills and background
            allowed_types = [MemoryType.SEMANTIC]
            min_importance = 0.4
            limit = 3

        return {
            "allowed_types": allowed_types,
            "min_importance": min_importance,
            "limit": limit
        }
