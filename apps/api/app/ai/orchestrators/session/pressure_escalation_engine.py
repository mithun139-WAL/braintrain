"""
Pressure Escalation Engine — session-level interview pressure curve manager.

Responsibility:
    Manage a pressure level (0–4) across the session timeline, ramp it
    gradually as the session progresses, spike it for adversarial probes,
    and de-escalate when the candidate shows recovery signals.

Pressure levels:
    0  Warm-up      — open-ended, supportive framing
    1  Probing      — follow-up on claims, ask for evidence/metrics
    2  Skeptical    — challenge assumptions, "why not X?"
    3  Adversarial  — contradictions, tight time pressure, interruptions
    4  Recovery     — supportive scaffolding after a stumble/collapse

Design principles:
    • Max ramp rate: +1 level per 3 turns (never jump 0→3).
    • De-escalation to L4 (recovery) is instant on COLLAPSED signal.
    • Pressure recovers from L4 → L1 over 3 turns once candidate stabilises.
    • Level 3 is capped to one adversarial probe per area — prevents harassment.
"""
from __future__ import annotations

import logging
from enum import IntEnum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, PrivateAttr

from app.ai.orchestrators.contracts.interview_contracts import InterviewerMood

logger = logging.getLogger(__name__)


class PressureLevel(IntEnum):
    WARM_UP     = 0
    PROBING     = 1
    SKEPTICAL   = 2
    ADVERSARIAL = 3
    RECOVERY    = 4


# ── Pressure → InterviewerMood mapping ────────────────────────────────────────
_PRESSURE_TO_MOOD: Dict[int, InterviewerMood] = {
    PressureLevel.WARM_UP:     InterviewerMood.SUPPORTIVE,
    PressureLevel.PROBING:     InterviewerMood.INQUISITIVE,
    PressureLevel.SKEPTICAL:   InterviewerMood.SKEPTICAL,
    PressureLevel.ADVERSARIAL: InterviewerMood.SKEPTICAL,
    PressureLevel.RECOVERY:    InterviewerMood.SUPPORTIVE,
}

# ── Pressure → generation instruction ─────────────────────────────────────────
_PRESSURE_INSTRUCTIONS: Dict[int, str] = {
    PressureLevel.WARM_UP: (
        "Ask in a warm, open-ended way. Give the candidate space to think out loud. "
        "No challenging follow-ups yet."
    ),
    PressureLevel.PROBING: (
        "Probe the candidate's claims. Ask for specifics: numbers, timelines, outcomes. "
        "Be curious but not confrontational."
    ),
    PressureLevel.SKEPTICAL: (
        "Challenge the candidate's approach. Suggest an alternative and ask why they didn't choose it. "
        "Express mild skepticism — 'Have you considered X instead?'. Keep it professional."
    ),
    PressureLevel.ADVERSARIAL: (
        "Apply direct pressure. Point out a potential flaw in their reasoning or design. "
        "Be terse and specific. You can say 'That concerns me — here's why...' "
        "Do NOT be hostile, but be clearly challenging. One sharp question only."
    ),
    PressureLevel.RECOVERY: (
        "The candidate is struggling. Shift to a supportive, scaffolding tone. "
        "Offer a partial hint or reframe the question at a simpler level. "
        "Help them recover their footing before continuing."
    ),
}

# ── Adversarial probe templates ────────────────────────────────────────────────
_ADVERSARIAL_PROBES: List[str] = [
    "That sounds reasonable, but I'm skeptical. What's the failure mode you're most worried about?",
    "Walk me through what happens when that assumption breaks down under production load.",
    "You mentioned {topic} — but a lot of teams have moved away from that. What makes you confident it's the right call here?",
    "I'm not convinced this scales. Where does your design break at 100x traffic?",
    "That's one approach. Why didn't you use {alternative}? What specifically ruled it out?",
]

# ── Area alternatives for adversarial probes ──────────────────────────────────
_AREA_ALTERNATIVES: Dict[str, str] = {
    "caching":         "a write-through cache instead of cache-aside",
    "data_layer":      "a NoSQL store instead of a relational DB",
    "api_design":      "GraphQL instead of REST",
    "async_processing":"synchronous processing with a queue-based retry",
    "scalability":     "vertical scaling before going distributed",
    "reliability":     "a simpler retry loop instead of circuit breaking",
}


class PressureDirective(BaseModel):
    """Output of the pressure engine for a single turn."""

    pressure_level: PressureLevel
    interviewer_mood: InterviewerMood
    pressure_instruction: str
    adversarial_probe: Optional[str] = None   # set at level 3
    reason: str = ""


class PressureEscalationConfig(BaseModel):
    """Tunable thresholds for pressure escalation."""

    # Turns before first ramp-up (let candidate warm up)
    ramp_start_turn: int = 4

    # How many turns must pass before level can increase by 1
    turns_per_level_increase: int = 3

    # Performance score below which pressure drops (struggling)
    struggling_score_threshold: float = 40.0

    # Frustration level above which we de-escalate to recovery
    frustration_threshold: float = 0.65

    # Number of turns at level 3 before forced back-off
    max_adversarial_turns: int = 1

    # After recovery, ramp back to this base level
    post_recovery_base_level: PressureLevel = PressureLevel.PROBING


class PressureEscalationEngine:
    """
    Manages the pressure curve across the session.

    Instantiate once per session.  Call update() after every turn to get the
    pressure directive for the NEXT turn.
    """

    def __init__(self, config: Optional[PressureEscalationConfig] = None) -> None:
        self.config = config or PressureEscalationConfig()
        self._current_level: PressureLevel = PressureLevel.WARM_UP
        self._turns_at_current_level: int = 0
        self._total_turns: int = 0
        self._adversarial_turns_used: int = 0
        self._in_recovery: bool = False
        self._recovery_turns: int = 0
        self._last_adversarial_area: Optional[str] = None

        logger.info("PressureEscalationEngine initialised at level WARM_UP")

    # ── Public API ─────────────────────────────────────────────────────────────

    def update(
        self,
        turn_number: int,
        candidate_score: float,
        frustration_level: float,
        is_in_stumble: bool,
        is_collapsed: bool,
        current_area: Optional[str] = None,
    ) -> PressureDirective:
        """
        Compute the pressure directive for the current turn based on session state.

        Call this once per turn before generating the interviewer response.
        """
        self._total_turns += 1
        self._turns_at_current_level += 1

        # ── Collapse: instant de-escalation to RECOVERY ────────────────────────
        if is_collapsed:
            if self._current_level != PressureLevel.RECOVERY:
                logger.info(
                    "PressureEngine: COLLAPSE detected — de-escalating to RECOVERY "
                    "(was level %d)", self._current_level
                )
                self._current_level = PressureLevel.RECOVERY
                self._turns_at_current_level = 0
                self._in_recovery = True
                self._recovery_turns = 0
            self._recovery_turns += 1
            return self._make_directive(current_area, reason="candidate_collapsed")

        # ── Recovery arc: count turns, ramp back up when stable ───────────────
        if self._in_recovery:
            if not is_in_stumble and candidate_score >= self.config.struggling_score_threshold:
                self._recovery_turns += 1
                if self._recovery_turns >= 3:
                    # Candidate stabilised — return to base probing level
                    self._current_level = self.config.post_recovery_base_level
                    self._turns_at_current_level = 0
                    self._in_recovery = False
                    self._recovery_turns = 0
                    logger.info("PressureEngine: recovery complete — resuming at PROBING")
            return self._make_directive(current_area, reason="recovery_arc")

        # ── High frustration: de-escalate one level ───────────────────────────
        if frustration_level >= self.config.frustration_threshold and self._current_level > PressureLevel.PROBING:
            self._current_level = PressureLevel(max(int(self._current_level) - 1, PressureLevel.PROBING))
            self._turns_at_current_level = 0
            logger.info(
                "PressureEngine: high frustration (%.2f) — de-escalated to level %d",
                frustration_level, self._current_level,
            )
            return self._make_directive(current_area, reason=f"high_frustration:{frustration_level:.2f}")

        # ── Struggling performance: hold level ────────────────────────────────
        if candidate_score < self.config.struggling_score_threshold:
            return self._make_directive(current_area, reason=f"holding_struggling_score:{candidate_score:.0f}")

        # ── Natural ramp-up ────────────────────────────────────────────────────
        if (
            self._total_turns >= self.config.ramp_start_turn
            and self._turns_at_current_level >= self.config.turns_per_level_increase
            and self._current_level < PressureLevel.ADVERSARIAL
        ):
            # Cap adversarial if already used
            next_level = PressureLevel(int(self._current_level) + 1)
            if next_level == PressureLevel.ADVERSARIAL and (
                self._adversarial_turns_used >= self.config.max_adversarial_turns
                or self._last_adversarial_area == current_area
            ):
                # Skip adversarial for this area / already used
                return self._make_directive(current_area, reason="adversarial_cap_hold")

            self._current_level = next_level
            self._turns_at_current_level = 0
            logger.info(
                "PressureEngine: ramped to level %d at turn %d",
                self._current_level, turn_number,
            )

        return self._make_directive(current_area, reason="natural_progression")

    @property
    def current_level(self) -> PressureLevel:
        return self._current_level

    def get_level_name(self) -> str:
        return self._current_level.name

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _make_directive(self, current_area: Optional[str], reason: str) -> PressureDirective:
        level = self._current_level
        adversarial_probe: Optional[str] = None

        if level == PressureLevel.ADVERSARIAL:
            adversarial_probe = self._pick_adversarial_probe(current_area)
            self._adversarial_turns_used += 1
            self._last_adversarial_area = current_area

        return PressureDirective(
            pressure_level=level,
            interviewer_mood=_PRESSURE_TO_MOOD[level],
            pressure_instruction=_PRESSURE_INSTRUCTIONS[level],
            adversarial_probe=adversarial_probe,
            reason=reason,
        )

    def _pick_adversarial_probe(self, area: Optional[str]) -> str:
        import random
        probe = random.choice(_ADVERSARIAL_PROBES)
        alternative = _AREA_ALTERNATIVES.get(area or "", "a different approach")
        topic_label = (area or "that choice").replace("_", " ")
        return probe.format(topic=topic_label, alternative=alternative)
