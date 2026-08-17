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

    # Alternate transition styles for moving to a new planned topic — varied
    # across the session (keyed off topic_switches) so the interviewer doesn't
    # always say "Great, next let's talk about X."
    _TRANSITION_STYLES = [
        "Use a clean pivot, e.g. 'Let's switch gears and talk about {label}.'",
        "Thread the transition: briefly connect something the candidate just said to {label} before asking your next question.",
        "Take a natural pause, briefly acknowledge their answer, then move directly into a question about {label}.",
    ]

    def _move_topic_directive(self, state: InterviewState, next_label: Optional[str]) -> str:
        switches = getattr(state.candidate, "topic_switches", 0)
        style = self._TRANSITION_STYLES[switches % len(self._TRANSITION_STYLES)]
        label_text = next_label or "a different topic area"
        style_text = style.format(label=label_text)
        target = f"the next planned topic ({next_label})" if next_label else "a different topic area"
        return (
            f"[BEHAVIOR DIRECTIVE: You MUST move on to {target} now. Do NOT ask any more follow-up "
            f"questions about the current topic. Do NOT reply to or probe the candidate's last answer's technical details. "
            f"Immediately pivot. {style_text}]"
        )

    def build(self, state: InterviewState, decision: ConversationDecision, tone: str, rag_context: str = "") -> str:
        parts = []

        # 1. State details (Layer 2)
        topic = state.conversation.current_topic or "General"
        plan = getattr(state.conversation, "plan", None)
        active_topic = plan.current().label if (plan and plan.current()) else topic
        category = getattr(state, "interview_category", "GENERAL")
        minutes_remaining = getattr(state, "minutes_remaining", 15.0)
        parts.append(
            f"[SESSION STATE: Topic={topic}, ActiveTopic={active_topic}, Category={category}, Difficulty={state.difficulty}, "
            f"Adaptive={state.adaptive_enabled}, TurnCount={state.conversation.turn_count}, "
            f"MinutesRemaining={minutes_remaining:.1f}]"
        )

        if category == "CODING":
            parts.append(
                "[FORMATTING DIRECTIVE: This is a Coding Snippet interview session. "
                "For every technical question you ask, you MUST present a code snippet on the screen. "
                "Write the code snippet inside standard Markdown code blocks (e.g. ```python ... ```). "
                "You MUST enclose the entire code snippet and any technical code block inside a single Markdown code block. "
                "You must output BOTH the conversational spoken text AND the Markdown code block in your single response. "
                "The system will automatically filter out the Markdown code block so it will NOT be spoken to the candidate. "
                "Therefore, write the code block fully, and keep your conversational spoken text natural (e.g., 'Take a look at the code snippet on your screen. It implements a cache decorator. What is its output?'). "
                "Do NOT ask the candidate to write code verbally or dictate code blocks to you.]"
            )
        elif category == "DSA":
            parts.append(
                "[FORMATTING DIRECTIVE: This is a DSA coding challenge session. "
                "You MUST present the challenge description, input/output examples, and constraints clearly. "
                "You MUST enclose the entire DSA challenge, description, examples, and constraints inside a single Markdown block (e.g. ```markdown ... ```). "
                "Do NOT write any challenge details or constraints outside the code block. "
                "You must output BOTH the conversational spoken text AND the Markdown challenge block in your single response. "
                "The system will automatically filter out the Markdown block so it will NOT be spoken to the candidate. "
                "Therefore, write the Markdown challenge details fully inside the block, and keep your conversational spoken text simple (e.g., 'I've displayed a DSA challenge on your screen. Take a look and talk me through your approach.').]"
            )
        elif category == "SYSTEM_DESIGN":
            parts.append(
                "[FORMATTING DIRECTIVE: This is a System Design interview. Ask the candidate to design a high-level "
                "architecture for a scenario. They may describe it in text or attach diagrams. Interrogate their "
                "bottlenecks, databases, load balancing, and scaling strategies.]"
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
            next_label = (decision.metadata or {}).get("next_topic_label")
            parts.append(self._move_topic_directive(state, next_label))
        elif decision.action.value == "PIVOT_TOPIC":
            topic_label = (decision.metadata or {}).get("topic_label", topic)
            parts.append(
                f"[BEHAVIOR DIRECTIVE: Ask about a different angle/dimension of the topic ({topic_label}) now. "
                f"Do NOT repeat the same kind of follow-up you just asked. Do NOT continue drilling into the "
                f"technical details of the candidate's last answer. Pivot the conversation to a new aspect of {topic_label}.]"
            )
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

        # 6. RAG Grounding Context (Layer 6)
        if rag_context:
            parts.append(f"\n[KNOWLEDGE BASE GROUNDING CONTEXT:\n{rag_context}\n]")

        full_prompt = "\n".join(parts)
        logger.debug("interview_prompt_built | tone: %s | pressure: %s", tone, pressure_level)
        return full_prompt
