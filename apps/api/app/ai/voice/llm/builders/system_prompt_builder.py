import logging
from typing import Optional
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.decisions.decision import ConversationDecision
from app.ai.voice.llm.prompt_manager import PromptManager
from app.ai.voice.policies.fact_grounding_policy import FactGroundingPolicy
from app.ai.voice.policies.domain_policy import DomainContext

logger = logging.getLogger("system_prompt_builder")

class SystemPromptBuilder:
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
        self.fact_grounding_policy: Optional[FactGroundingPolicy] = None
        self.domain_context: Optional[DomainContext] = None

    def set_fact_grounding_policy(self, policy: FactGroundingPolicy) -> None:
        self.fact_grounding_policy = policy

    def set_domain_context(self, context: DomainContext) -> None:
        self.domain_context = context

    def build(self, state: InterviewState, decision: ConversationDecision) -> str:
        is_panel = state.panel_mode
        base_system = self.prompt_manager.get_system_prompt(is_panel=is_panel)

        builder_parts = [base_system]

        if is_panel:
            builder_parts.append("\nPanel Profiles:")
            for panelist in ["Marcus", "Sarah", "David"]:
                profile = self.prompt_manager.get_panel_prompt(panelist)
                if profile:
                    builder_parts.append(f"- {panelist}: {profile}")

            active_speaker = decision.metadata.get("active_speaker") if decision.metadata else None
            if active_speaker:
                persona = self.prompt_manager.get_panel_prompt(active_speaker)
                builder_parts.append(
                    f"\nFor this turn, you MUST act and speak as {active_speaker}. "
                    f"Embody their profile: {persona}. "
                    f"Ensure you prefix your answer with '{active_speaker}: '."
                )
        else:
            interviewer_profile = self.prompt_manager.get_interview_prompt()
            if interviewer_profile:
                builder_parts.append(f"\nYour Profile:\n{interviewer_profile}")

        if self.domain_context:
            builder_parts.append(f"\n{self.domain_context.format_domain_instructions()}")

        full_prompt = "\n".join(builder_parts)
        logger.debug("system_prompt_built | panel: %s", is_panel)
        return full_prompt
