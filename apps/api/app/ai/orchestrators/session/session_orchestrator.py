"""
Session Orchestrator — coordinates the session-layer control plane.

Sits above TurnOrchestrator and runs on every turn to produce a
SessionDirective that injects session-level steering into the turn decision.

Priority chain (highest wins):
    1. Recovery: candidate collapsed → RECOVERY_SUPPORT immediately
    2. Recovery: candidate in stumble → hold pressure, soft scaffold
    3. Pressure: issue pressure directive for current level
    4. Coverage: PIVOT / ZOOM_OUT / INTRODUCE_CONSTRAINT as needed
    5. Default: CONTINUE

The SessionDirective is attached to TurnDecision.metadata and consumed
by both the generation prompt builders and the analytics pipeline.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.ai.orchestrators.session.session_coverage_planner import (
    SessionCoveragePlanner,
    CoverageDirective,
    CoveragePlannerConfig,
    SteerAction,
)
from app.ai.orchestrators.session.pressure_escalation_engine import (
    PressureEscalationEngine,
    PressureDirective,
    PressureEscalationConfig,
    PressureLevel,
)
from app.ai.orchestrators.session.recovery_tracker import (
    RecoveryTracker,
    RecoverySnapshot,
    RecoveryState,
    StumbleCause,
)
from app.ai.orchestrators.contracts.interview_contracts import (
    InterviewDomain,
    InterviewerMood,
)

logger = logging.getLogger(__name__)


class SessionDirective(BaseModel):
    """
    The session-layer output consumed by TurnOrchestrator and prompt builders.

    This is attached to TurnDecision.metadata["session_directive"] so every
    downstream component has access to the full session-layer context.
    """

    # ── Steering ──────────────────────────────────────────────────────────────
    steer_action: SteerAction = SteerAction.CONTINUE
    current_area: Optional[str] = None
    target_area: Optional[str] = None

    # Pre-rendered bridge phrase for PIVOT / ZOOM_OUT — injected verbatim
    bridge_phrase: Optional[str] = None

    # For INTRODUCE_CONSTRAINT: the constraint scenario text
    constraint_scenario: Optional[str] = None

    # ── Pressure ──────────────────────────────────────────────────────────────
    pressure_level: int = 0                      # PressureLevel int value
    pressure_level_name: str = "WARM_UP"
    interviewer_mood: InterviewerMood = InterviewerMood.NEUTRAL
    pressure_instruction: str = ""
    adversarial_probe: Optional[str] = None       # set when pressure level = ADVERSARIAL

    # ── Recovery ──────────────────────────────────────────────────────────────
    recovery_state: str = RecoveryState.STABLE.value
    is_in_stumble: bool = False
    is_collapsed: bool = False
    recovery_snapshot: Optional[Dict[str, Any]] = None

    # ── Coverage snapshot ─────────────────────────────────────────────────────
    coverage_snapshot: Dict[str, float] = Field(default_factory=dict)
    uncovered_areas: list = Field(default_factory=list)

    # ── Meta ──────────────────────────────────────────────────────────────────
    decision_reason: str = ""
    session_turn: int = 0


class SessionOrchestratorConfig(BaseModel):
    """Top-level config knob for the session orchestrator."""
    coverage: CoveragePlannerConfig = Field(default_factory=CoveragePlannerConfig)
    pressure: PressureEscalationConfig = Field(default_factory=PressureEscalationConfig)


class SessionOrchestrator:
    """
    Session-level control plane.  One instance per session.

    Usage:
        orchestrator = SessionOrchestrator(session_id, domain)
        # ... in each turn:
        directive = orchestrator.evaluate(turn_number, transcript, ...)
        # attach directive to TurnDecision.metadata["session_directive"]
    """

    def __init__(
        self,
        session_id: str,
        domain: str = "backend",
        config: Optional[SessionOrchestratorConfig] = None,
    ) -> None:
        self.session_id = session_id
        self.domain = domain
        cfg = config or SessionOrchestratorConfig()

        self.coverage_planner = SessionCoveragePlanner(
            domain=domain,
            config=cfg.coverage,
        )
        self.pressure_engine = PressureEscalationEngine(
            config=cfg.pressure,
        )
        self.recovery_tracker = RecoveryTracker(session_id=session_id)

        self._turn_number: int = 0

        logger.info(
            "SessionOrchestrator initialised: session=%s domain=%s",
            session_id, domain,
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def evaluate(
        self,
        transcript: str,
        answer_quality: str,             # AnswerQuality.value
        performance_score: float,
        frustration_level: float,
        is_topic_fixation_active: bool = False,
        question_was_ambiguous: bool = False,
    ) -> SessionDirective:
        """
        Run the session-layer pipeline for one turn.

        Returns a SessionDirective to be merged into TurnDecision.metadata.
        """
        self._turn_number += 1
        turn = self._turn_number

        # ── 1. Recovery tracker ────────────────────────────────────────────────
        recovery_state = self.recovery_tracker.record_turn(
            turn_number=turn,
            answer_quality=answer_quality,
            transcript=transcript,
            is_topic_fixation_active=is_topic_fixation_active,
            is_under_pressure=self.pressure_engine.current_level >= PressureLevel.SKEPTICAL,
            question_was_ambiguous=question_was_ambiguous,
            performance_score=performance_score,
        )
        recovery_snapshot = self.recovery_tracker.get_snapshot()

        # ── 2. Pressure engine ─────────────────────────────────────────────────
        current_area = self.coverage_planner.record_turn(transcript, turn)
        pressure_dir = self.pressure_engine.update(
            turn_number=turn,
            candidate_score=performance_score,
            frustration_level=frustration_level,
            is_in_stumble=self.recovery_tracker.is_in_stumble,
            is_collapsed=self.recovery_tracker.is_collapsed,
            current_area=current_area,
        )

        # ── 3. Coverage planner ────────────────────────────────────────────────
        coverage_dir = self.coverage_planner.get_directive(turn)

        # ── 4. Priority synthesis ─────────────────────────────────────────────
        return self._synthesize(
            turn, recovery_state, recovery_snapshot, pressure_dir, coverage_dir
        )

    def get_recovery_snapshot(self) -> RecoverySnapshot:
        return self.recovery_tracker.get_snapshot()

    def get_coverage_summary(self) -> Dict[str, float]:
        return self.coverage_planner.get_coverage_summary()

    # ── Priority chain ────────────────────────────────────────────────────────

    def _synthesize(
        self,
        turn: int,
        recovery_state: RecoveryState,
        recovery_snapshot: RecoverySnapshot,
        pressure_dir: PressureDirective,
        coverage_dir: CoverageDirective,
    ) -> SessionDirective:

        base = SessionDirective(
            pressure_level=int(pressure_dir.pressure_level),
            pressure_level_name=pressure_dir.pressure_level.name,
            interviewer_mood=pressure_dir.interviewer_mood,
            pressure_instruction=pressure_dir.pressure_instruction,
            adversarial_probe=pressure_dir.adversarial_probe,
            recovery_state=recovery_state.value,
            is_in_stumble=self.recovery_tracker.is_in_stumble,
            is_collapsed=self.recovery_tracker.is_collapsed,
            recovery_snapshot=recovery_snapshot.model_dump(),
            coverage_snapshot=coverage_dir.coverage_snapshot,
            uncovered_areas=coverage_dir.uncovered_areas,
            session_turn=turn,
        )

        # ── Priority 1: Collapse → immediate recovery support ──────────────────
        if self.recovery_tracker.is_collapsed:
            base.steer_action = SteerAction.CONTINUE  # no pivot while collapsed
            base.interviewer_mood = InterviewerMood.SUPPORTIVE
            base.pressure_instruction = (
                "The candidate is struggling significantly. "
                "Be warm and scaffolding. Offer a concrete hint or simplify the question. "
                "Do NOT change topics — help them recover on the current one."
            )
            base.decision_reason = "candidate_collapsed_recovery_support"
            logger.info("SessionOrchestrator: RECOVERY_SUPPORT at turn %d", turn)
            return base

        # ── Priority 2: Active stumble → soften, don't pivot ──────────────────
        if self.recovery_tracker.is_in_stumble:
            base.steer_action = SteerAction.CONTINUE
            base.interviewer_mood = InterviewerMood.SUPPORTIVE
            base.pressure_instruction = (
                "The candidate is struggling on this question. "
                "Soften the follow-up — allow them to self-correct. "
                "Do not pile on or switch topics yet."
            )
            base.decision_reason = "active_stumble_hold"
            return base

        # ── Priority 3: Adversarial probe ─────────────────────────────────────
        if (
            pressure_dir.pressure_level == PressureLevel.ADVERSARIAL
            and pressure_dir.adversarial_probe
        ):
            base.steer_action = SteerAction.PRESSURE_PROBE
            base.current_area = coverage_dir.current_area
            base.decision_reason = f"adversarial_pressure:{pressure_dir.reason}"
            return base

        # ── Priority 4: Coverage pivot ─────────────────────────────────────────
        if coverage_dir.steer_action in (
            SteerAction.PIVOT_TO,
            SteerAction.ZOOM_OUT,
            SteerAction.INTRODUCE_CONSTRAINT,
        ):
            base.steer_action = coverage_dir.steer_action
            base.current_area = coverage_dir.current_area
            base.target_area = coverage_dir.target_area
            base.bridge_phrase = coverage_dir.bridge_phrase
            base.decision_reason = f"coverage:{coverage_dir.reason}"

            if coverage_dir.steer_action == SteerAction.INTRODUCE_CONSTRAINT:
                base.constraint_scenario = self.coverage_planner.next_constraint_scenario()

            logger.info(
                "SessionOrchestrator: %s %s → %s at turn %d",
                coverage_dir.steer_action.value,
                coverage_dir.current_area,
                coverage_dir.target_area,
                turn,
            )
            return base

        # ── Priority 5: Coverage complete ─────────────────────────────────────
        if coverage_dir.steer_action == SteerAction.COVERAGE_COMPLETE:
            base.steer_action = SteerAction.COVERAGE_COMPLETE
            base.decision_reason = "all_areas_covered"
            return base

        # ── Default: continue ─────────────────────────────────────────────────
        base.steer_action = SteerAction.CONTINUE
        base.current_area = coverage_dir.current_area
        base.decision_reason = f"continue:{coverage_dir.reason}"
        return base
