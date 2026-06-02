import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("strategic_engine")

CLARIFICATION_KEYWORDS = [
    "clarify", "assumption", "constraints", "scale", "user base",
    "load", "traffic", "qps", "read or write", "storage requirements",
    "budget", "latency target", "availability", "slas"
]

TRADEOFF_KEYWORDS = [
    "tradeoff", "compromise", "on the other hand", "however", "cost of",
    "cap theorem", "consistency vs", "latency vs", "read vs write",
    "cpu vs memory", "simplifies", "complex", "scalable but", "bottleneck"
]

DECOMPOSITION_KEYWORDS = [
    "decompose", "break down", "components", "architecture", "microservices",
    "layers", "database layer", "cache layer", "client-server", "modular"
]

PRIORITY_KEYWORDS = [
    "first", "priority", "critical path", "mvp", "core constraint",
    "most important", "baseline", "bottleneck"
]

class StrategicThinkingEngine:
    """
    StrategicThinkingEngine evaluates the reasoning quality of interview responses.
    Checks logical reasoning path, requirement clarification, tradeoff analysis,
    problem decomposition, decision quality, and priority ordering.
    """

    def __init__(self):
        pass

    def analyze_reasoning_path(self, text: str) -> Dict[str, Any]:
        """
        Evaluate if candidate follows a mature problem-solving flow:
        Clarification/Requirements -> Decomposition -> Design options/tradeoffs -> Decision.
        """
        text_lower = text.lower()
        
        # Check indices of key sections to see if they occurred in the correct order
        clarify_idx = next((text_lower.find(kw) for kw in CLARIFICATION_KEYWORDS if kw in text_lower), -1)
        decomp_idx = next((text_lower.find(kw) for kw in DECOMPOSITION_KEYWORDS if kw in text_lower), -1)
        tradeoff_idx = next((text_lower.find(kw) for kw in TRADEOFF_KEYWORDS if kw in text_lower), -1)
        
        score = 50.0  # Base score
        sequence = []
        
        if clarify_idx != -1:
            score += 15.0
            sequence.append("clarification")
        if decomp_idx != -1:
            score += 15.0
            sequence.append("decomposition")
        if tradeoff_idx != -1:
            score += 20.0
            sequence.append("tradeoffs")

        # Order evaluation: Clarification should happen BEFORE decomposition and tradeoffs
        is_order_correct = True
        if clarify_idx != -1 and decomp_idx != -1 and clarify_idx > decomp_idx:
            is_order_correct = False
            score -= 10.0  # Penalty for premature decomposition
        if decomp_idx != -1 and tradeoff_idx != -1 and decomp_idx > tradeoff_idx:
            is_order_correct = False
            score -= 10.0  # Penalty for discussing tradeoffs before decomposition

        score = min(100.0, max(0.0, score))

        return {
            "reasoning_path_score": round(score, 1),
            "sequence": sequence,
            "is_order_correct": is_order_correct,
            "has_premature_implementation": clarify_idx == -1 and decomp_idx != -1
        }

    def detect_missing_clarification(self, question: str, answer_transcript: str) -> Dict[str, Any]:
        """
        Evaluate if candidate gathered requirements or made unstated assumptions.
        System design questions require clarification.
        """
        text_lower = answer_transcript.lower()
        matches = [kw for kw in CLARIFICATION_KEYWORDS if kw in text_lower]
        
        # If question contains "design" or "scale" and answer has 0 clarifications, it's missing
        is_system_design = any(w in question.lower() for w in ["design", "architecture", "scale", "system"])
        missing_clarification = is_system_design and len(matches) == 0

        score = 100.0 - (50.0 if missing_clarification else max(0, 30.0 - len(matches) * 10.0))

        return {
            "clarification_score": round(score, 1),
            "missing_clarification": missing_clarification,
            "clarification_matches": matches
        }

    def detect_tradeoff_thinking(self, text: str) -> Dict[str, Any]:
        """
        Detect tradeoff and pros/cons analysis.
        """
        text_lower = text.lower()
        matches = [kw for kw in TRADEOFF_KEYWORDS if kw in text_lower]
        
        # Score based on keyword counts
        score = min(100.0, len(matches) * 20.0)
        
        return {
            "tradeoff_score": round(score, 1),
            "has_tradeoff_thinking": len(matches) >= 2,
            "tradeoff_matches": list(set(matches))
        }

    def analyze_problem_decomposition(self, text: str) -> Dict[str, Any]:
        """
        Score how modularly candidate breaks down the system.
        """
        text_lower = text.lower()
        matches = [kw for kw in DECOMPOSITION_KEYWORDS if kw in text_lower]
        
        score = min(100.0, len(matches) * 25.0)
        
        return {
            "decomposition_score": round(score, 1),
            "decomposition_matches": list(set(matches))
        }

    def analyze_decision_quality(self, text: str) -> Dict[str, Any]:
        """
        Evaluate decision justification (risk analysis, simplicity vs complexity).
        """
        text_lower = text.lower()
        
        # Decisions are justified when tradeoff thinking is paired with priority keyword
        has_justification = any(tw in text_lower for tw in TRADEOFF_KEYWORDS) and any(pk in text_lower for pk in PRIORITY_KEYWORDS)
        
        score = 80.0 if has_justification else 40.0
        # Boost for length / complexity
        if len(text.split()) > 100:
            score += 10.0
            
        score = min(100.0, score)

        return {
            "decision_quality_score": round(score, 1),
            "is_decision_justified": has_justification
        }

    def detect_assumption_failures(self, text: str) -> bool:
        """
        Returns True if candidate specifies unvalidated assumptions without stating them.
        Heuristic: statements with high certainty ("must be", "we will just use", "always") 
        without any clarification keywords.
        """
        text_lower = text.lower()
        has_high_certainty = any(p in text_lower for p in ["just use", "obviously", "always", "must be"])
        has_clarification = any(ck in text_lower for ck in CLARIFICATION_KEYWORDS)
        
        return has_high_certainty and not has_clarification

    def analyze_priority_ordering(self, text: str) -> float:
        """
        Checks if candidate prioritizes constraints/MVP before design details.
        """
        text_lower = text.lower()
        priority_idx = next((text_lower.find(kw) for kw in PRIORITY_KEYWORDS if kw in text_lower), -1)
        detail_idx = next((text_lower.find(kw) for kw in ["database", "schema", "code", "index", "api"] if kw in text_lower), -1)
        
        if priority_idx != -1 and (detail_idx == -1 or priority_idx < detail_idx):
            return 100.0
        elif priority_idx != -1:
            return 70.0
        return 40.0

    def get_thinking_pattern_profile(self, text: str) -> str:
        """
        Identify candidate thinking profile:
        - "reactive": no clarification, jumps directly to code/details.
        - "structured": follows STAR/PREP structure cleanly.
        - "systems": strong decomposition and tradeoff analysis.
        - "detail-first": discusses implementation details before priorities.
        - "framework_memorizer": uses high-level boilerplate words without tradeoff reasoning.
        """
        text_lower = text.lower()
        
        path = self.analyze_reasoning_path(text)
        tradeoffs = self.detect_tradeoff_thinking(text)
        decomp = self.analyze_problem_decomposition(text)
        
        if path["has_premature_implementation"]:
            return "reactive"
        elif tradeoffs["has_tradeoff_thinking"] and decomp["decomposition_score"] >= 50:
            return "systems"
        elif path["reasoning_path_score"] >= 70:
            return "structured"
        
        # Default fallbacks
        if len(re.findall(r'\b(react|angular|vue|nextjs|fastapi|redis|postgres)\b', text_lower)) >= 3 and tradeoffs["tradeoff_score"] < 30:
            return "framework_memorizer"
            
        return "detail-first"
