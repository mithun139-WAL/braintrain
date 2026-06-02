"""
Cross-Round Memory Manager — tracks candidate performance across rounds.

Enables realistic interview progression where later rounds can reference
earlier round signals.
"""
from typing import Any


class JourneyMemoryManager:
    def __init__(self):
        self.round_memories: dict[str, dict] = {}
        self.cumulative: dict[str, Any] = {
            "weaknesses": [],
            "strengths": [],
            "unresolved_topics": [],
            "confidence_drops": [],
            "recurring_mistakes": [],
            "strong_signals": [],
            "topic_coverage": {},
        }

    def record_round(
        self,
        round_name: str,
        signals: dict,
    ) -> None:
        memory = {
            "round_name": round_name,
            "signals": signals,
        }
        self.round_memories[round_name] = memory

        if signals.get("weaknesses"):
            self.cumulative["weaknesses"].extend(signals["weaknesses"])
        if signals.get("strengths"):
            self.cumulative["strengths"].extend(signals["strengths"])
        if signals.get("unresolved_topics"):
            self.cumulative["unresolved_topics"].extend(signals["unresolved_topics"])
        if signals.get("confidence_drops"):
            self.cumulative["confidence_drops"].extend(signals["confidence_drops"])
        if signals.get("recurring_mistakes"):
            self.cumulative["recurring_mistakes"].extend(signals["recurring_mistakes"])
        if signals.get("strong_signals"):
            self.cumulative["strong_signals"].extend(signals["strong_signals"])

        coverage = signals.get("topic_coverage", {})
        for topic, status in coverage.items():
            if topic not in self.cumulative["topic_coverage"]:
                self.cumulative["topic_coverage"][topic] = status
            elif status == "weak" and self.cumulative["topic_coverage"][topic] != "weak":
                self.cumulative["topic_coverage"][topic] = "mixed"

    def get_cross_round_context(self, current_round: str) -> str:
        if not self.cumulative["weaknesses"] and not self.cumulative["strengths"]:
            return "This is the first round. No prior signals to reference."

        context_parts = []

        if self.cumulative["strengths"]:
            top_strengths = list(set(self.cumulative["strengths"]))[:3]
            context_parts.append(
                f"Strong areas from previous rounds: {', '.join(top_strengths)}."
            )

        if self.cumulative["weaknesses"]:
            key_weaknesses = list(set(self.cumulative["weaknesses"]))[:3]
            context_parts.append(
                f"Areas to probe deeper: {', '.join(key_weaknesses)}."
            )

        if self.cumulative["unresolved_topics"]:
            unresolved = list(set(self.cumulative["unresolved_topics"]))[:2]
            context_parts.append(
                f"Earlier you mentioned {unresolved[0].lower() if unresolved else 'some topics'} — we should revisit that."
            )

        if self.cumulative["confidence_drops"]:
            context_parts.append(
                "The candidate showed hesitation on certain topics. Probe for genuine understanding."
            )

        return "\n".join(context_parts) if context_parts else "No significant cross-round signals."

    def get_round_reference(self, round_name: str) -> str | None:
        memory = self.round_memories.get(round_name)
        if not memory:
            return None
        signals = memory.get("signals", {})
        notes = signals.get("interviewer_notes", "")
        return notes if notes else None

    def get_weakness_continuity_prompt(self, current_round: str) -> str:
        weaknesses = list(set(self.cumulative.get("weaknesses", [])))[:2]
        if not weaknesses:
            return ""
        return (
            f"Continuity note: In earlier rounds, the candidate showed "
            f"potential gaps in: {', '.join(weaknesses)}. "
            f"Consider revisiting if relevant to this round."
        )

    def get_strength_continuity_prompt(self, current_round: str) -> str:
        strengths = list(set(self.cumulative.get("strengths", [])))[:2]
        if not strengths:
            return ""
        return (
            f"Continuity note: The candidate demonstrated strength in: "
            f"{', '.join(strengths)}. You can reference this."
        )

    def get_memory_summary(self) -> dict:
        return {
            "rounds_completed": list(self.round_memories.keys()),
            "cumulative_weaknesses": list(set(self.cumulative["weaknesses"])),
            "cumulative_strengths": list(set(self.cumulative["strengths"])),
            "confidence_drops_detected": len(self.cumulative["confidence_drops"]),
            "recurring_mistakes": list(set(self.cumulative["recurring_mistakes"])),
            "topic_coverage": self.cumulative["topic_coverage"],
        }


_journey_memory_store: dict[str, JourneyMemoryManager] = {}


def get_journey_memory(journey_id: str) -> JourneyMemoryManager:
    if journey_id not in _journey_memory_store:
        _journey_memory_store[journey_id] = JourneyMemoryManager()
    return _journey_memory_store[journey_id]


def clear_journey_memory(journey_id: str) -> None:
    _journey_memory_store.pop(journey_id, None)
