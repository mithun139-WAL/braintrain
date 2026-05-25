import time
import logging
from typing import Optional
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.decisions.decision import ConversationDecision
from app.ai.voice.policies.response_policy import ResponsePolicy
from app.ai.voice.policies.fact_grounding_policy import FactGroundingPolicy
from app.ai.voice.llm.prompt_manager import PromptManager
from app.ai.voice.llm.builders.system_prompt_builder import SystemPromptBuilder
from app.ai.voice.llm.builders.interview_prompt_builder import InterviewPromptBuilder
from app.ai.voice.llm.builders.followup_prompt_builder import FollowupPromptBuilder
from app.ai.voice.llm.builders.clarification_prompt_builder import ClarificationPromptBuilder
from app.ai.voice.llm.response_generator import ResponseGenerator
from app.ai.voice.llm.response_parser import ResponseParser
from app.ai.voice.llm.formatters.speaker_formatter import SpeakerFormatter
from app.ai.voice.llm.formatters.response_formatter import ResponseFormatter

logger = logging.getLogger("interviewer")

class Interviewer:
    def __init__(
        self,
        prompt_manager: PromptManager,
        system_prompt_builder: SystemPromptBuilder,
        interview_prompt_builder: InterviewPromptBuilder,
        followup_prompt_builder: FollowupPromptBuilder,
        clarification_prompt_builder: ClarificationPromptBuilder,
        response_generator: ResponseGenerator,
        response_parser: ResponseParser,
        speaker_formatter: SpeakerFormatter,
        response_formatter: ResponseFormatter,
        response_policy: ResponsePolicy,
    ):
        self.prompt_manager = prompt_manager
        self.system_prompt_builder = system_prompt_builder
        self.interview_prompt_builder = interview_prompt_builder
        self.followup_prompt_builder = followup_prompt_builder
        self.clarification_prompt_builder = clarification_prompt_builder
        self.response_generator = response_generator
        self.response_parser = response_parser
        self.speaker_formatter = speaker_formatter
        self.response_formatter = response_formatter
        self.response_policy = response_policy
        self.fact_grounding_policy: Optional[FactGroundingPolicy] = None

    def set_fact_grounding_policy(self, policy: FactGroundingPolicy) -> None:
        self.fact_grounding_policy = policy
        self.system_prompt_builder.set_fact_grounding_policy(policy)
        self.interview_prompt_builder.set_fact_grounding_policy(policy)
        self.followup_prompt_builder.set_fact_grounding_policy(policy)

    def set_domain_context(self, context) -> None:
        self.system_prompt_builder.set_domain_context(context)
        self.followup_prompt_builder.set_domain_context(context)

    async def respond(self, state: InterviewState, decision: ConversationDecision) -> dict:
        start_time = time.perf_counter()

        tone = self.response_policy.select_tone(state)
        system_prompt = self.system_prompt_builder.build(state, decision)

        messages = [{"role": "system", "content": system_prompt}]

        for msg in state.conversation.messages:
            role = msg.role
            if role in ("panelist", "Interviewer", "Marcus", "Sarah", "David"):
                role = "assistant"
            elif role == "Candidate":
                role = "user"

            messages.append({
                "role": role,
                "content": msg.content
            })

        interview_prompt = self.interview_prompt_builder.build(state, decision, tone)

        followup_prompt = self.followup_prompt_builder.build_followup(state, decision)
        if followup_prompt:
            logger.info("followup_prompt_created | injecting followup instruction")

        clarification_prompt = self.clarification_prompt_builder.build_clarification(state)
        if clarification_prompt:
            logger.info("clarification_prompt_created | injecting clarification instruction")

        directives = [interview_prompt]
        if followup_prompt:
            directives.append(followup_prompt)
        if clarification_prompt:
            directives.append(clarification_prompt)

        messages.append({
            "role": "system",
            "content": "\n\n".join(directives)
        })

        raw_response = await self.response_generator.generate(messages)

        if not raw_response:
            raw_response = (
                "I appreciate your response. Let me ask you another question. "
                "Can you describe a challenging situation you faced in a previous "
                "role and how you resolved it?"
            )

        parsed_response = self.response_parser.parse(raw_response)
        formatted_text = self.response_formatter.format_response(parsed_response)

        speaker_name, clean_text, voice_name = self.speaker_formatter.format_speaker(
            formatted_text,
            state.conversation.turn_count,
            state.panel_mode
        )

        total_latency = time.perf_counter() - start_time
        logger.info(
            "interviewer_respond_completed | speaker: %s | voice: %s | total_latency: %.3fs",
            speaker_name,
            voice_name,
            total_latency
        )

        return {
            "raw_text": raw_response,
            "clean_text": clean_text,
            "speaker_name": speaker_name,
            "voice_name": voice_name,
        }
