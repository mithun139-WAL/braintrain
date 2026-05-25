import logging
from typing import Optional
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.decisions.decision import ConversationDecision
from app.ai.voice.llm.prompt_manager import PromptManager
from app.ai.voice.policies.fact_grounding_policy import FactGroundingPolicy

logger = logging.getLogger("interview_prompt_builder")

class InterviewPromptBuilder:
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
        self.fact_grounding_policy: Optional[FactGroundingPolicy] = None

    def set_fact_grounding_policy(self, policy: FactGroundingPolicy) -> None:
        self.fact_grounding_policy = policy

    def build(self, state: InterviewState, decision: ConversationDecision, tone: str) -> str:
        parts = []

        # 1. State details (Layer 2)
        topic = state.conversation.current_topic or "General"
        parts.append(
            f"[SESSION STATE: Topic={topic}, Difficulty={state.difficulty}, "
            f"Adaptive={state.adaptive_enabled}, TurnCount={state.conversation.turn_count}]"
        )

        # 2. Conversational Decision (Layer 4)
        parts.append(
            f"[DECISION DIRECTIVE: Action={decision.action.value}, Reason={decision.reason}, "
            f"RequestedTone={tone}]"
        )

        # 3. Behavioral Objective (Layer 5)
        if decision.action.value == "END_INTERVIEW":
            parts.append("[BEHAVIOR DIRECTIVE: The interview time is up. You must gracefully wrap up the interview and say goodbye. DO NOT ask any further questions of any kind.]")
        elif decision.action.value == "WRAP_UP_INTERVIEW":
            parts.append(
                "[BEHAVIOR DIRECTIVE: The interview is ending in a few minutes. Do NOT ask any more technical or topic-related questions. "
                "Instead, inform the candidate that you are wrapping up and ask if they have any final questions for you. "
                "If they have a question, answer it concisely. If they say no, gracefully end the conversation.]"
            )
        elif decision.action.value == "MOVE_TOPIC":
            parts.append("[BEHAVIOR DIRECTIVE: You MUST move to a completely new topic now. Do NOT ask any more follow-up questions about the current topic. Briefly acknowledge the candidate's answer, and then ask a new question about a different technical area.]")
        else:
            behavioral_instruction = self.prompt_manager.get_behavioral_prompt(tone)
            if behavioral_instruction:
                parts.append(f"[BEHAVIOR DIRECTIVE: {behavioral_instruction}]")

        # 4. Behavioral Signals and Pressure
        signals = getattr(state, "behavioral_signals", None)
        pressure_level = getattr(state, "pressure_level", "NORMAL")
        if signals:
            parts.append(
                f"[CANDIDATE BEHAVIOR STATE: Hesitation={signals.hesitation_score:.1f}, "
                f"Confidence={signals.confidence_score:.1f}, Verbosity={signals.verbosity_score:.1f}, "
                f"TopicDrift={signals.topic_drift_score:.1f}, PressureLevel={pressure_level}]"
            )

            if signals.confidence_score < 40.0:
                parts.append("[CANDIDATE STATE DIRECTIVE: Candidate appears uncertain. Maintain supportive but professional tone. Acknowledge and guide gently.]")
            elif signals.confidence_score > 75.0:
                parts.append("[CANDIDATE STATE DIRECTIVE: Candidate demonstrates strong technical confidence. Increase probing depth and challenge their design assumptions.]")
        else:
            parts.append(f"[CANDIDATE BEHAVIOR STATE: Confidence={state.candidate.confidence_score:.1f}, PressureLevel={pressure_level}]")

        # 5. Explicit candidate facts for grounded followups
        if self.fact_grounding_policy:
            grounding_directives = self.fact_grounding_policy.get_grounding_directives()
            if grounding_directives:
                parts.append(f"\n{grounding_directives}")

        full_prompt = "\n".join(parts)
        logger.debug("interview_prompt_built | tone: %s | pressure: %s", tone, pressure_level)
        return full_prompt
