import logging
from typing import List, Dict, Optional
from app.ai.voice.conversation.candidate_claims import CandidateClaim

logger = logging.getLogger("fact_registry")

class FactRegistry:
    def __init__(self):
        self._facts: Dict[str, CandidateClaim] = {}
        self._turn_counter: int = 0

    def next_turn(self) -> int:
        self._turn_counter += 1
        return self._turn_counter

    def add_fact(self, claim: CandidateClaim) -> None:
        self._facts[claim.fact_id] = claim
        logger.info(
            "fact_added | id: %s | type: %s | claim: %s | confidence: %s",
            claim.fact_id, claim.fact_type, claim.claim, claim.confidence,
        )

    def get_explicit_facts(self) -> List[CandidateClaim]:
        return [f for f in self._facts.values() if f.confidence == "explicit"]

    def get_facts_by_topic(self, topic: str) -> List[CandidateClaim]:
        topic_lower = topic.lower()
        return [
            f for f in self._facts.values()
            if topic_lower in f.subject.lower() or topic_lower in f.claim.lower()
        ]

    def get_facts_by_type(self, fact_type: str) -> List[CandidateClaim]:
        return [f for f in self._facts.values() if f.fact_type == fact_type]

    def get_all_facts(self) -> List[CandidateClaim]:
        return list(self._facts.values())

    def validate_claim(self, claim_text: str) -> bool:
        claim_lower = claim_text.lower()
        for fact in self.get_explicit_facts():
            if any(word in claim_lower for word in fact.claim.lower().split()):
                return True
        return False

    def has_explicit_fact(self, subject: str, claim_fragment: str) -> bool:
        fragment_lower = claim_fragment.lower()
        for fact in self.get_explicit_facts():
            if subject.lower() in fact.subject.lower() and fragment_lower in fact.claim.lower():
                return True
        return False

    def format_explicit_facts_for_prompt(self) -> str:
        facts = self.get_explicit_facts()
        if not facts:
            return ""
        lines = []
        for f in facts:
            lines.append(f"- Candidate {f.claim} (type: {f.fact_type}, subject: {f.subject})")
        return "\n".join(lines)

    def clear(self) -> None:
        self._facts.clear()
        self._turn_counter = 0
