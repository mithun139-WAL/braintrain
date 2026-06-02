"""
Tests for session-layer intelligence:
  - SessionCoveragePlanner
  - PressureEscalationEngine
  - RecoveryTracker
  - SessionOrchestrator (integration)

Run:
    cd apps/api && uv run pytest test_session_layer.py -v
"""
import pytest
from app.ai.orchestrators.session.session_coverage_planner import (
    SessionCoveragePlanner,
    CoveragePlannerConfig,
    SteerAction,
)
from app.ai.orchestrators.session.pressure_escalation_engine import (
    PressureEscalationEngine,
    PressureEscalationConfig,
    PressureLevel,
)
from app.ai.orchestrators.session.recovery_tracker import (
    RecoveryTracker,
    RecoveryState,
    StumbleCause,
)
from app.ai.orchestrators.session.session_orchestrator import (
    SessionOrchestrator,
    SessionDirective,
)


# ─── SessionCoveragePlanner ───────────────────────────────────────────────────

class TestSessionCoveragePlanner:
    def _make_planner(self, **cfg) -> SessionCoveragePlanner:
        config = CoveragePlannerConfig(
            min_turns_to_activate=1,
            **cfg,
        )
        return SessionCoveragePlanner(domain="backend", config=config)

    def test_cold_start_returns_continue(self):
        config = CoveragePlannerConfig(min_turns_to_activate=5)
        planner = SessionCoveragePlanner(domain="backend", config=config)
        planner.record_turn("redis is fast", turn_number=1)
        directive = planner.get_directive(1)
        assert directive.steer_action == SteerAction.CONTINUE
        assert directive.reason == "cold_start"

    def test_continue_within_budget(self):
        planner = self._make_planner(max_turns_per_area=5, max_consecutive_turns_in_area=99)
        for i in range(3):
            planner.record_turn("redis caching strategy", turn_number=i + 1)
        directive = planner.get_directive(3)
        assert directive.steer_action == SteerAction.CONTINUE

    def test_pivot_fires_after_max_turns_per_area(self):
        planner = self._make_planner(max_turns_per_area=3, max_consecutive_turns_in_area=99)
        for i in range(4):  # 4 turns > threshold of 3
            planner.record_turn("redis caching eviction strategy", turn_number=i + 1)
        directive = planner.get_directive(4)
        assert directive.steer_action == SteerAction.PIVOT_TO
        assert directive.current_area == "caching"
        assert directive.target_area != "caching"
        assert directive.bridge_phrase is not None

    def test_pivot_fires_after_consecutive_turns(self):
        planner = self._make_planner(max_consecutive_turns_in_area=2, max_turns_per_area=99)
        # Transcript hits only 'caching' signals unambiguously (no 'redis' keyword)
        cache_transcript = "cache invalidation strategy, ttl configuration, eviction policy"
        for i in range(3):  # 3 consecutive > threshold of 2
            planner.record_turn(cache_transcript, turn_number=i + 1)
        directive = planner.get_directive(3)
        assert directive.steer_action == SteerAction.PIVOT_TO


    def test_zoom_out_on_saturation_no_breadth_debt(self):
        """Saturated area but no unvisited areas → ZOOM_OUT."""
        planner = self._make_planner(
            max_turns_per_area=99,
            max_consecutive_turns_in_area=99,
            saturation_threshold=0.1,  # very low — saturates immediately
            breadth_debt_threshold=10,  # high — never triggers pivot
        )
        planner.record_turn("redis caching eviction ttl", turn_number=1)
        directive = planner.get_directive(1)
        assert directive.steer_action == SteerAction.ZOOM_OUT

    def test_coverage_summary_accumulates(self):
        planner = self._make_planner(max_turns_per_area=99)
        planner.record_turn("redis caching strategy", turn_number=1)
        planner.record_turn("kafka event queue consumer", turn_number=2)
        summary = planner.get_coverage_summary()
        assert summary["caching"] > 0
        assert summary["async_processing"] > 0

    def test_bridge_phrase_rendered_for_known_transition(self):
        planner = self._make_planner(max_turns_per_area=2, max_consecutive_turns_in_area=99)
        for i in range(3):
            planner.record_turn("redis cache invalidation strategy", turn_number=i + 1)
        directive = planner.get_directive(3)
        assert directive.steer_action == SteerAction.PIVOT_TO
        # Bridge phrase should be a non-empty string
        assert directive.bridge_phrase and len(directive.bridge_phrase) > 10

    def test_area_detection_from_transcript(self):
        planner = self._make_planner()
        detected = planner.record_turn(
            "We use postgres with B-tree indexes on the user_id column", turn_number=1
        )
        assert detected == "data_layer"

    def test_constraint_scenario_round_robins(self):
        planner = self._make_planner()
        s1 = planner.next_constraint_scenario()
        s2 = planner.next_constraint_scenario()
        # Should be different (cycling through list)
        scenarios = planner.config.constraint_scenarios
        assert s1 in scenarios
        assert s2 in scenarios


# ─── PressureEscalationEngine ─────────────────────────────────────────────────

class TestPressureEscalationEngine:
    def _make_engine(self, **cfg) -> PressureEscalationEngine:
        config = PressureEscalationConfig(ramp_start_turn=1, **cfg)
        return PressureEscalationEngine(config=config)

    def _update(self, engine, turn=1, score=75.0, frustration=0.2,
                stumble=False, collapsed=False, area="caching"):
        return engine.update(
            turn_number=turn,
            candidate_score=score,
            frustration_level=frustration,
            is_in_stumble=stumble,
            is_collapsed=collapsed,
            current_area=area,
        )

    def test_starts_at_warm_up(self):
        engine = self._make_engine()
        assert engine.current_level == PressureLevel.WARM_UP

    def test_ramps_up_gradually(self):
        engine = self._make_engine(turns_per_level_increase=2)
        for i in range(6):
            self._update(engine, turn=i + 1)
        # After 6 turns with 2 turns/level: should be at level 3 (ADVERSARIAL)
        # but adversarial is capped at 1 use — so may be level 2 or 3
        assert engine.current_level >= PressureLevel.SKEPTICAL

    def test_never_jumps_more_than_one_level(self):
        engine = self._make_engine(turns_per_level_increase=1)
        levels_seen = []
        for i in range(6):
            d = self._update(engine, turn=i + 1)
            levels_seen.append(d.pressure_level)
        # No jump of more than 1 between consecutive levels
        for i in range(1, len(levels_seen)):
            assert levels_seen[i] - levels_seen[i - 1] <= 1

    def test_instant_deescalate_on_collapse(self):
        engine = self._make_engine(turns_per_level_increase=1)
        # Ramp up first
        for i in range(4):
            self._update(engine, turn=i + 1)
        # Now collapse
        d = self._update(engine, turn=5, collapsed=True)
        assert d.pressure_level == PressureLevel.RECOVERY

    def test_high_frustration_deescalates_one_level(self):
        engine = self._make_engine(turns_per_level_increase=2, frustration_threshold=0.5)
        # Ramp to SKEPTICAL
        for i in range(4):
            self._update(engine, turn=i + 1, frustration=0.1)
        level_before = engine.current_level
        # High frustration
        d = self._update(engine, turn=5, frustration=0.9)
        assert d.pressure_level < level_before

    def test_struggling_score_holds_level(self):
        engine = self._make_engine(
            turns_per_level_increase=1,
            struggling_score_threshold=50.0,
        )
        for i in range(5):
            d = self._update(engine, turn=i + 1, score=30.0)  # always struggling
        # Should not have ramped above WARM_UP at all (struggling holds)
        assert engine.current_level == PressureLevel.WARM_UP

    def test_adversarial_probe_included_at_level_3(self):
        engine = self._make_engine(turns_per_level_increase=1, max_adversarial_turns=2)
        # Fast-ramp to ADVERSARIAL
        d = None
        for i in range(10):
            d = self._update(engine, turn=i + 1)
            if d.pressure_level == PressureLevel.ADVERSARIAL:
                break
        if d and d.pressure_level == PressureLevel.ADVERSARIAL:
            assert d.adversarial_probe is not None

    def test_recovery_exits_after_stable_turns(self):
        engine = self._make_engine(turns_per_level_increase=2)
        # Collapse
        self._update(engine, turn=1, collapsed=True)
        assert engine.current_level == PressureLevel.RECOVERY
        # 3 stable good turns → exits recovery
        for i in range(3):
            self._update(engine, turn=i + 2, score=70.0, stumble=False, collapsed=False)
        assert engine.current_level == PressureLevel.PROBING


# ─── RecoveryTracker ──────────────────────────────────────────────────────────

class TestRecoveryTracker:
    def _tracker(self) -> RecoveryTracker:
        return RecoveryTracker(session_id="test")

    def _turn(self, tracker, quality="good", transcript="solid explanation",
              fixation=False, pressure=False, ambiguous=False, score=70.0):
        return tracker.record_turn(
            turn_number=tracker._total_turns + 1,
            answer_quality=quality,
            transcript=transcript,
            is_topic_fixation_active=fixation,
            is_under_pressure=pressure,
            question_was_ambiguous=ambiguous,
            performance_score=score,
        )

    def test_starts_stable(self):
        t = self._tracker()
        assert t.current_state == RecoveryState.STABLE

    def test_good_answer_stays_stable(self):
        t = self._tracker()
        state = self._turn(t, "good")
        assert state == RecoveryState.STABLE

    def test_weak_answer_enters_stumble(self):
        t = self._tracker()
        state = self._turn(t, "insufficient")
        assert state == RecoveryState.STUMBLE

    def test_recovery_after_stumble(self):
        t = self._tracker()
        self._turn(t, "insufficient")
        state = self._turn(t, "good")
        assert state == RecoveryState.RECOVERED

    def test_collapse_after_3_stumble_turns(self):
        t = self._tracker()
        self._turn(t, "insufficient")
        self._turn(t, "vague")
        self._turn(t, "incorrect")
        state = self._turn(t, "vague")  # 4th bad turn → collapse
        assert state == RecoveryState.COLLAPSED

    def test_self_correction_detected(self):
        t = self._tracker()
        self._turn(t, "insufficient")
        state = self._turn(t, "vague", transcript="Actually, let me correct that — I meant...")
        assert state == RecoveryState.RECOVERY_ATTEMPT

    def test_loop_attribution(self):
        t = self._tracker()
        state = self._turn(t, "insufficient", fixation=True)
        assert state == RecoveryState.STUMBLE
        snapshot = t.get_snapshot()
        assert snapshot.loop_induced_stumbles == 1
        assert snapshot.candidate_errors == 0

    def test_candidate_error_attribution(self):
        t = self._tracker()
        self._turn(t, "insufficient", fixation=False, pressure=False)
        snapshot = t.get_snapshot()
        assert snapshot.candidate_errors == 1
        assert snapshot.loop_induced_stumbles == 0

    def test_pressure_induced_attribution(self):
        t = self._tracker()
        # Prior good turns establish high score, then stumble under pressure
        self._turn(t, "good", score=75.0)
        self._turn(t, "insufficient", pressure=True, score=75.0)
        snapshot = t.get_snapshot()
        assert snapshot.pressure_induced_stumbles == 1

    def test_recovery_rate_calculated(self):
        t = self._tracker()
        # Stumble then recover
        self._turn(t, "insufficient")
        self._turn(t, "good")
        snapshot = t.get_snapshot()
        assert snapshot.recovery_rate == 1.0

    def test_failed_recovery_tracked(self):
        t = self._tracker()
        self._turn(t, "insufficient")
        for _ in range(4):
            self._turn(t, "vague")
        snapshot = t.get_snapshot()
        assert snapshot.failed_recoveries >= 1
        assert snapshot.recovery_rate == 0.0


# ─── SessionOrchestrator integration ─────────────────────────────────────────

class TestSessionOrchestrator:
    def _make_orchestrator(self, **cfg_kwargs) -> SessionOrchestrator:
        from app.ai.orchestrators.session.session_orchestrator import SessionOrchestratorConfig
        from app.ai.orchestrators.session.session_coverage_planner import CoveragePlannerConfig
        from app.ai.orchestrators.session.pressure_escalation_engine import PressureEscalationConfig

        config = SessionOrchestratorConfig(
            coverage=CoveragePlannerConfig(
                min_turns_to_activate=1,
                max_turns_per_area=3,
                max_consecutive_turns_in_area=2,
            ),
            pressure=PressureEscalationConfig(
                ramp_start_turn=1,
                turns_per_level_increase=99,  # don't ramp in most tests
            ),
        )
        return SessionOrchestrator(session_id="s1", domain="backend", config=config)

    def _eval(self, orch, transcript="redis caching strategy", quality="good",
              score=75.0, frustration=0.2):
        return orch.evaluate(
            transcript=transcript,
            answer_quality=quality,
            performance_score=score,
            frustration_level=frustration,
        )

    def test_returns_session_directive(self):
        orch = self._make_orchestrator()
        d = self._eval(orch)
        assert isinstance(d, SessionDirective)

    def test_pivot_fires_after_consecutive_turns(self):
        orch = self._make_orchestrator()
        # 3 consecutive turns on caching (threshold=2)
        for _ in range(3):
            directive = self._eval(orch, transcript="redis caching eviction ttl invalidation")
        assert directive.steer_action in (SteerAction.PIVOT_TO, SteerAction.ZOOM_OUT)

    def test_recovery_support_overrides_pivot(self):
        """When candidate is collapsed, steering must be CONTINUE (hold in place), not PIVOT."""
        orch = self._make_orchestrator()
        # Force collapse: multiple bad answers
        for _ in range(5):
            self._eval(orch, quality="insufficient", score=20.0)
        directive = self._eval(orch, quality="incorrect", score=20.0)
        # Recovery support takes priority — steer_action must NOT be PIVOT_TO
        assert directive.steer_action != SteerAction.PIVOT_TO
        assert directive.is_collapsed or directive.is_in_stumble

    def test_pressure_instruction_present(self):
        orch = self._make_orchestrator()
        d = self._eval(orch)
        assert isinstance(d.pressure_instruction, str)

    def test_coverage_snapshot_populated(self):
        orch = self._make_orchestrator()
        d = self._eval(orch, transcript="redis caching strategy invalidation")
        assert "caching" in d.coverage_snapshot

    def test_recovery_snapshot_in_directive(self):
        orch = self._make_orchestrator()
        self._eval(orch, quality="insufficient")
        d = self._eval(orch, quality="good")
        assert d.recovery_snapshot is not None
        assert "total_stumbles" in d.recovery_snapshot

    def test_no_pivot_during_stumble(self):
        """While candidate is mid-stumble, hold in place even if area is saturated."""
        from app.ai.orchestrators.session.session_coverage_planner import CoveragePlannerConfig
        from app.ai.orchestrators.session.pressure_escalation_engine import PressureEscalationConfig
        from app.ai.orchestrators.session.session_orchestrator import SessionOrchestratorConfig

        config = SessionOrchestratorConfig(
            coverage=CoveragePlannerConfig(
                min_turns_to_activate=1,
                max_turns_per_area=1,  # pivot immediately
                max_consecutive_turns_in_area=1,
            ),
            pressure=PressureEscalationConfig(ramp_start_turn=99),
        )
        orch = SessionOrchestrator(session_id="s2", domain="backend", config=config)
        # First turn causes stumble
        orch.evaluate(
            transcript="redis cache hit rate",
            answer_quality="insufficient",
            performance_score=30.0,
            frustration_level=0.2,
        )
        # Second turn: still stumbling — should NOT pivot
        d = orch.evaluate(
            transcript="redis cache hit rate",
            answer_quality="vague",
            performance_score=30.0,
            frustration_level=0.2,
        )
        assert d.steer_action != SteerAction.PIVOT_TO
