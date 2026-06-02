import logging
from typing import Optional, List
from app.ai.voice.conversation.fact_registry import FactRegistry
from app.ai.voice.conversation.fact_validator import FactValidator

logger = logging.getLogger("fact_grounding_policy")

CLARIFICATION_FIRST_TEMPLATES = [
    "You mentioned {fact}. What specifically was your role in that?",
    "You mentioned {fact}. Can you elaborate on what you worked on?",
    "You brought up {fact}. Could you tell me more about your involvement?",
    "I'd like to hear more about {fact}. What part of that did you handle?",
]

class FactGroundingPolicy:
    def __init__(self, registry: "FactRegistry"):
        self.registry = registry
        self.validator = FactValidator(registry)

    def validate_followup(self, followup_text: str) -> bool:
        return self.validator.validate_followup(followup_text)

    def get_grounding_directives(self) -> str:
        explicit_facts = self.registry.get_explicit_facts()
        if not explicit_facts:
            return ""

        parts = [
            "EXPLICIT_CANDIDATE_FACTS:",
        ]
        for fact in explicit_facts:
            parts.append(f"- {fact.claim} ({fact.fact_type})")

        parts.extend([
            "",
            "GROUNDING RULES:",
            "- ONLY ask followups grounded in the explicit facts listed above.",
            "- Never assume ownership, leadership, implementation, deployment,",
            "  or architecture responsibility unless the candidate explicitly stated it",
            "  with ownership language (e.g. 'I designed', 'I built', 'I architected').",
            "- If the candidate said 'I worked with X' or 'the team used X':",
            "  ask about their specific role or involvement.",
            "  Do NOT ask 'How did you design X?' or 'Tell me about your architecture.'",
            "- Prefer clarification-first questions when ownership is unclear.",
            "- Invalid example: 'Tell me about the backend architecture you designed.'",
            "- Valid example: 'You mentioned working with Redis. What part of that work",
            "  were you personally responsible for?'",
        ])

        return "\n".join(parts)

    def get_clarification_prompt(self, fact_claim: str) -> str:
        import random
        template = random.choice(CLARIFICATION_FIRST_TEMPLATES)
        return template.format(fact=fact_claim)

    def is_hallucinated(self, followup_text: str) -> bool:
        return not self.validator.validate_followup(followup_text)

    def get_rejection_reason(self, followup_text: str) -> Optional[str]:
        return self.validator.get_rejection_reason(followup_text)
