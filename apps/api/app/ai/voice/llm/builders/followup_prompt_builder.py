import logging
from typing import Optional
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.decisions.decision import ConversationDecision
from app.ai.voice.llm.prompt_manager import PromptManager
from app.ai.voice.policies.fact_grounding_policy import FactGroundingPolicy
from app.ai.voice.policies.domain_policy import DomainContext

logger = logging.getLogger("followup_prompt_builder")

class FollowupPromptBuilder:
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
        self.fact_grounding_policy: Optional[FactGroundingPolicy] = None
        self.domain_context: Optional[DomainContext] = None

    def set_fact_grounding_policy(self, policy: FactGroundingPolicy) -> None:
        self.fact_grounding_policy = policy

    def set_domain_context(self, context: DomainContext) -> None:
        self.domain_context = context

    def build_followup(self, state: InterviewState, decision: ConversationDecision) -> str:
        cache_key = f"prebuilt_followup_{state.session_id}"
        if self.prompt_manager.response_cache:
            cached_followup = self.prompt_manager.response_cache.get(cache_key)
            if cached_followup:
                logger.info("followup_prompt_builder | cache hit for speculative prefetch")
                return f"[PROBING DIRECTIVES:\n- {cached_followup}]"

        last_candidate_text = ""
        for msg in reversed(state.conversation.messages):
            if msg.role in ("Candidate", "user"):
                last_candidate_text = msg.content
                break

        if not last_candidate_text:
            return ""

        text_lower = last_candidate_text.lower()
        explicit_facts = []
        if self.fact_grounding_policy:
            explicit_facts = self.fact_grounding_policy.registry.get_explicit_facts()

        directives = []

        if explicit_facts:
            grounded_directives = []
            for fact in explicit_facts:
                fact_words = fact.claim.lower().split()
                if any(w in text_lower for w in fact_words if len(w) > 3):
                    if fact.fact_type == "ownership":
                        grounded_directives.append(
                            f"The candidate explicitly stated they {fact.claim}. "
                            f"Probe their specific approach, challenges, and tradeoffs."
                        )
                    else:
                        grounded_directives.append(
                            f"The candidate mentioned {fact.claim}. "
                            f"Ask about their specific role and involvement. "
                            f"Do NOT assume they designed or architected it."
                        )
            if grounded_directives:
                directives.extend(grounded_directives)

        if "caching" in text_lower or "redis" in text_lower or "memcached" in text_lower:
            directives.append(
                "GROUNDED FOLLOWUP: The candidate mentioned caching. Ask about their specific "
                "experience - what invalidation strategy they used, what problems they solved. "
                "Do NOT assume they designed the caching layer."
            )

        if "scaling" in text_lower or "scale" in text_lower or "distributed" in text_lower:
            directives.append(
                "GROUNDED FOLLOWUP: The candidate mentioned scaling. Ask about their specific "
                "role in scaling - what they personally observed, measured, or contributed. "
                "Do NOT assume they designed the distributed system."
            )

        if "optimiz" in text_lower or "performance" in text_lower or "latency" in text_lower:
            directives.append(
                "GROUNDED FOLLOWUP: The candidate mentioned performance. Ask what specific "
                "optimizations they performed or were involved in. Do NOT assume ownership."
            )

        if "database" in text_lower or "db" in text_lower or "sql" in text_lower or "postgres" in text_lower:
            directives.append(
                "GROUNDED FOLLOWUP: The candidate mentioned databases. Ask about their specific "
                "interaction - what queries they wrote, what schema they worked with. "
                "Do NOT assume they designed the database architecture."
            )

        topic_followup = self.prompt_manager.get_followup_prompt(state.conversation.current_topic)
        if topic_followup:
            directives.append(topic_followup)

        if decision.metadata and decision.metadata.get("followup_context"):
            directives.append(decision.metadata["followup_context"])

        if not directives:
            return ""

        domain_instruction = ""
        if self.domain_context and self.domain_context.restricted_topics:
            restricted = ", ".join(self.domain_context.restricted_topics)
            domain_instruction = (
                f"\nDOMAIN CONSTRAINT: You are conducting a {self.domain_context.primary_domain.value} interview. "
                f"Do NOT probe into: {restricted}. Stay within domain scope."
            )
            directives.append(domain_instruction)

        full_followup = "[PROBING DIRECTIVES:\n" + "\n".join(f"- {d}" for d in directives) + "]"
        logger.info("followup_prompt_created | count: %d", len(directives))
        return full_followup
