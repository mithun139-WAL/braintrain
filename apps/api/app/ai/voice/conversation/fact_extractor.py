import re
import logging
from typing import List, Optional
from app.ai.voice.conversation.candidate_claims import CandidateClaim

logger = logging.getLogger("fact_extractor")

OWNERSHIP_VERBS = {
    "i worked on", "i built", "i designed", "i developed", "i implemented",
    "i created", "i architected", "i led", "i owned", "i was responsible for",
    "i managed", "i shipped", "i delivered", "i deployed", "i authored",
    "i wrote", "i configured", "i maintained", "i optimized",
    "i refactored", "i migrated", "i integrated", "i set up",
    "i was the lead", "i spearheaded", "i drove", "i initiated",
}

EXPERIENCE_VERBS = {
    "i used", "i worked with", "i have experience with", "i know",
    "i am familiar with", "i have used", "i have worked on",
    "i have been using", "i have experience in", "i am experienced in",
    "i learned", "i studied", "i explored", "i tried", "i experimented with",
    "i was involved in", "i participated in", "i contributed to",
    "the team used", "we used", "we worked on", "we built",
}

UNCERTAIN_PHRASES = {
    "i think", "i believe", "maybe", "possibly", "probably",
    "i guess", "not sure", "i don't know", "i am not sure",
    "if i recall", "as far as i know", "i might have",
}

FORBIDDEN_INFERENCE_PATTERNS = [
    r"\bdesigned\b.*architecture",
    r"\barchitected\b",
    r"\bwas responsible for\b",
    r"\bled (the |a |an )?(team|project|initiative)",
    r"\bowned\b.*(system|service|platform|infrastructure)",
    r"\b(senior|lead|principal|head)\b.*(engineer|architect|developer)",
    r"\bdrove\b.*(architecture|design|strategy)",
]

def _is_forbidden_inference(text: str) -> bool:
    text_lower = text.lower()
    for pattern in FORBIDDEN_INFERENCE_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False

class FactExtractor:
    def __init__(self, registry: "FactRegistry"):
        self.registry = registry

    def extract_from_turn(self, text: str) -> List[CandidateClaim]:
        text_lower = text.lower().strip()
        claims = []

        if _is_forbidden_inference(text):
            logger.warning("fact_extractor | forbidden inference pattern detected in: %s", text[:80])
            return []

        detected_ownership = False
        for verb in OWNERSHIP_VERBS:
            if verb in text_lower:
                claim_text = self._extract_claim_after(text, verb)
                if claim_text:
                    subject = self._extract_subject(claim_text)
                    claims.append(CandidateClaim.create(
                        fact_type="ownership",
                        subject=subject,
                        claim=claim_text,
                        confidence="explicit",
                        source_turn_id=self.registry.next_turn(),
                    ))
                    detected_ownership = True
                break

        if not detected_ownership:
            for verb in EXPERIENCE_VERBS:
                if verb in text_lower:
                    claim_text = self._extract_claim_after(text, verb)
                    if claim_text:
                        subject = self._extract_subject(claim_text)
                        confidence = self._determine_confidence(text_lower)
                        claims.append(CandidateClaim.create(
                            fact_type="experience",
                            subject=subject,
                            claim=claim_text,
                            confidence=confidence,
                            source_turn_id=self.registry.next_turn(),
                        ))
                    break

        for claim in claims:
            self.registry.add_fact(claim)
            logger.info("fact_extracted | type: %s | confidence: %s | claim: %s", claim.fact_type, claim.confidence, claim.claim)

        return claims

    def _extract_claim_after(self, text: str, verb: str) -> Optional[str]:
        text_lower = text.lower()
        idx = text_lower.find(verb)
        if idx == -1:
            return None
        after = text[idx + len(verb):].strip()
        after = re.sub(r'^[,:\s]+', '', after)
        sentences = re.split(r'[.?!]', after)
        if sentences:
            return sentences[0].strip()
        return None

    def _extract_subject(self, claim_text: str) -> str:
        words = claim_text.split()
        if not words:
            return "general"
        tech_keywords = [
            "redis", "kafka", "docker", "kubernetes", "aws", "gcp", "azure",
            "react", "angular", "vue", "node", "python", "java", "go", "rust",
            "postgres", "mysql", "mongodb", "elasticsearch", "graphql", "rest",
            "api", "microservice", "frontend", "backend", "database", "cache",
            "ci/cd", "pipeline", "testing", "deployment", "monitoring",
        ]
        for kw in tech_keywords:
            if kw in claim_text.lower():
                return kw
        return words[0] if words else "general"

    def _determine_confidence(self, text_lower: str) -> str:
        for phrase in UNCERTAIN_PHRASES:
            if phrase in text_lower:
                return "uncertain"
        return "explicit"
