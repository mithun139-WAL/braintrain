import re
import logging
from typing import Optional
from app.ai.voice.conversation.fact_registry import FactRegistry

logger = logging.getLogger("fact_validator")

ARCHITECTURE_ASSUMPTION_PATTERNS = [
    r"(how|what|describe|explain).*(design|architectur|build|implement).*(backend|system|distributed|infrastructure|platform|service)",
    r"(how|what).*(architectur|design).*(decision|choice|tradeoff|approach)",
    r"tell me about the (backend|system|distributed|infrastructure).*(design|architecture|you designed|you built|you implemented)",
    r"walk me through your (backend|system|infrastructure).*(design|architecture)",
    r"(why|how).*(you|did you).*(choose|select|decide).*(technology|stack|framework|architecture)",
    r"(what|which).*(architecture|design).*(pattern|principle).*(did you use|do you use|have you used)",
    r"(how|what).*(does|did).*(your|the).*(system|platform|application).*(scale|handle|process|manage)",
]

def _contains_architecture_assumption(text: str) -> bool:
    text_lower = text.lower()
    for pattern in ARCHITECTURE_ASSUMPTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False

class FactValidator:
    def __init__(self, registry: "FactRegistry"):
        self.registry = registry

    def validate_followup(self, followup_text: str) -> bool:
        if not self._contains_fact_reference(followup_text):
            if _contains_architecture_assumption(followup_text):
                logger.warning("fact_validator | REJECTED: architecture assumption without explicit fact: %s", followup_text[:80])
                return False
            return True

        if _contains_architecture_assumption(followup_text):
            for fact in self.registry.get_explicit_facts():
                if fact.fact_type == "ownership" and fact.confidence == "explicit":
                    return True
            logger.warning("fact_validator | REJECTED: architecture assumption without ownership claim: %s", followup_text[:80])
            return False

        return True

    def _contains_fact_reference(self, text: str) -> bool:
        text_lower = text.lower()
        for fact in self.registry.get_explicit_facts():
            words = fact.claim.lower().split()
            if any(len(w) > 3 and w in text_lower for w in words):
                return True
        return False

    def get_rejection_reason(self, followup_text: str) -> Optional[str]:
        if _contains_architecture_assumption(followup_text):
            for fact in self.registry.get_explicit_facts():
                if fact.fact_type == "ownership" and fact.confidence == "explicit":
                    return None
            return "architecture_assumption_without_ownership"

        if not self._contains_fact_reference(followup_text):
            excessive_assumption = _contains_architecture_assumption(followup_text)
            if excessive_assumption:
                return "ungrounded_architecture_question"

        return None
