"""
Tests for TopicFixationTracker and the turn orchestrator breadth-redirect logic.

Run:
    cd apps/api && python -m pytest test_topic_fixation.py -v
"""
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.ai.orchestrators.policies.topic_fixation_policy import (
    TopicFixationTracker,
    TopicFixationConfig,
    _extract_topics,
)
from app.ai.orchestrators.contracts.turn_contracts import TurnAction, AnswerQuality


# ─── _extract_topics ──────────────────────────────────────────────────────────

class TestExtractTopics:
    def test_single_tool_detected(self):
        topics = _extract_topics("We used redis for caching session data")
        assert "redis" in topics

    def test_case_insensitive(self):
        topics = _extract_topics("Redis and KAFKA are both in our stack")
        assert "redis" in topics
        assert "kafka" in topics

    def test_multi_word_phrase(self):
        topics = _extract_topics("We applied cap theorem to our design")
        assert "cap_theorem" in topics

    def test_no_false_positives(self):
        topics = _extract_topics("I worked on a Python web application")
        # None of our canonical topics should appear
        assert topics == []

    def test_deduplication(self):
        # "cache" and "caching" both map to "caching"
        topics = _extract_topics("We used a cache for caching requests")
        assert topics.count("caching") == 1


# ─── TopicFixationTracker ─────────────────────────────────────────────────────

class TestTopicFixationTracker:
    def _make_tracker(self, **cfg_overrides) -> TopicFixationTracker:
        # Default cooldown=0 so tests fire immediately, unless caller overrides it
        cfg_overrides.setdefault("redirect_cooldown_turns", 0)
        cfg = TopicFixationConfig(**cfg_overrides)
        return TopicFixationTracker(session_id="test-session", config=cfg)

    def test_no_fixation_initially(self):
        tracker = self._make_tracker()
        should, topic, prompt = tracker.check_fixation()
        assert should is False
        assert topic is None

    def test_hard_count_threshold_triggers(self):
        tracker = self._make_tracker(max_topic_turns_per_session=3)
        for _ in range(3):
            # Only transcript counts — question_text is ignored
            tracker.record_turn(
                "I used redis for session storage and redis for leaderboards",
                "Tell me about your caching strategy"  # 'caching' from here is NOT counted
            )
        should, topic, prompt = tracker.check_fixation()
        assert should is True
        assert topic == "redis"  # redis dominates from transcript
        assert "redis" in prompt.lower() or "step back" in prompt.lower()

    def test_hard_count_below_threshold_no_trigger(self):
        tracker = self._make_tracker(max_topic_turns_per_session=4)
        for _ in range(3):
            tracker.record_turn("I used redis", "caching question")
        should, _, _ = tracker.check_fixation()
        assert should is False

    def test_fraction_threshold_triggers(self):
        tracker = self._make_tracker(
            max_topic_turns_per_session=999,  # disable hard-count
            max_topic_fraction=0.4,
            min_turns_for_fraction_check=5,
        )
        # Only transcript counts — use transcripts without ambiguous overlap
        # 4 redis turns + 2 kafka turns = 6 total; redis fraction = 4/6 ≈ 0.67 > 0.4
        for _ in range(4):
            tracker.record_turn("redis is our primary data store for sessions", "performance question")
        for _ in range(2):
            tracker.record_turn("kafka is our event bus", "how do you handle events?")
        should, topic, _ = tracker.check_fixation()
        assert should is True
        assert topic == "redis"

    def test_cooldown_prevents_double_fire(self):
        tracker = self._make_tracker(
            max_topic_turns_per_session=2,
            redirect_cooldown_turns=3,
        )
        for _ in range(2):
            tracker.record_turn("redis redis redis", "")
        # First check fires and registers cooldown
        should1, _, _ = tracker.check_fixation()
        assert should1 is True
        # Simulate next turn — clears pending cache, increments turns_since (now=1)
        tracker.record_turn("redis again", "")
        # Cooldown has only advanced 1 turn (need 3) — should block
        should2, _, _ = tracker.check_fixation()
        assert should2 is False

    def test_cooldown_expires(self):
        tracker = self._make_tracker(
            max_topic_turns_per_session=2,
            redirect_cooldown_turns=2,
        )
        for _ in range(2):
            tracker.record_turn("redis redis redis", "")
        tracker.check_fixation()  # fires, starts cooldown (turns_since=0)
        # Simulate 2 more turns passing (each record_turn increments turns_since)
        tracker.record_turn("something unrelated", "")   # turns_since=1
        tracker.record_turn("something unrelated again", "")  # turns_since=2 == cooldown
        # Now cooldown (2 turns) has elapsed
        should, _, _ = tracker.check_fixation()
        assert should is True

    def test_get_topic_summary(self):
        tracker = self._make_tracker()
        tracker.record_turn("redis and kafka", "ignored question")
        tracker.record_turn("redis again", "another ignored question")
        summary = tracker.get_topic_summary()
        assert summary["redis"] == 2
        assert summary["kafka"] == 1


# ─── TurnOrchestrator integration ─────────────────────────────────────────────

class TestTurnOrchestratorBreadthRedirect:
    """Integration smoke-test: verify BREADTH_REDIRECT surfaces through analyze_turn."""

    def _make_orchestrator(self):
        from app.ai.orchestrators.turn_orchestrator import TurnOrchestrator
        from app.ai.orchestrators.policies.topic_fixation_policy import TopicFixationConfig

        cfg = TopicFixationConfig(
            max_topic_turns_per_session=2,
            redirect_cooldown_turns=0,
        )
        return TurnOrchestrator(fixation_config=cfg)

    def _make_evaluation(self, quality=AnswerQuality.GOOD, score=75.0):
        from app.ai.orchestrators.contracts.evaluation_contracts import (
            UnifiedEvaluation, RuleBasedMetrics, LLMBasedMetrics
        )
        return UnifiedEvaluation(
            final_score=score,
            rule_based_score=score,
            llm_based_score=score,
            answer_quality=quality,
            rule_based_metrics=RuleBasedMetrics(),
            llm_based_metrics=LLMBasedMetrics(),
            confidence=0.8,
        )

    def _make_question(self, text="Tell me about your caching strategy"):
        from app.ai.orchestrators.state.interview_runtime_state import QuestionState
        return QuestionState(
            question_id="q1",
            question_text=text,
            question_type="initial",
            domain="backend",
            difficulty="medium",
            target_topics=["caching"],
        )

    def _make_candidate_state(self):
        from app.ai.orchestrators.state.interview_runtime_state import CandidateRuntimeState
        return CandidateRuntimeState(candidate_id="c1", session_id="s1")

    @pytest.mark.asyncio
    async def test_redirect_fires_after_threshold(self):
        orch = self._make_orchestrator()
        eval_ = self._make_evaluation()
        q = self._make_question()
        c = self._make_candidate_state()

        from app.ai.orchestrators.contracts.interview_contracts import (
            InterviewPhase, InterviewerMood
        )

        kwargs = dict(
            session_id="s1",
            turn_number=1,
            transcript="We used redis for caching. Redis is very fast.",
            evaluation=eval_,
            current_question=q,
            candidate_state=c,
            current_phase=InterviewPhase.TECHNICAL_ROUND_1,
            interviewer_mood=InterviewerMood.NEUTRAL,
            consecutive_followups=0,
            max_followup_depth=3,
        )

        # Turn 1: record redis — not yet at threshold
        d1 = await orch.analyze_turn(**kwargs)
        assert d1.action != TurnAction.BREADTH_REDIRECT, "Should not redirect on first turn"

        # Turn 2: hits threshold (max=2) — should redirect
        kwargs["turn_number"] = 2
        # Use a transcript that only has redis, no 'cach*' words
        kwargs["transcript"] = "Redis is extremely fast for leaderboards and rate limiting."
        d2 = await orch.analyze_turn(**kwargs)
        assert d2.action == TurnAction.BREADTH_REDIRECT
        assert "breadth_redirect_prompt" in (d2.metadata or {})
        # Only transcript counts — redis (from transcript) dominates
        assert d2.metadata["breadth_redirect_topic"] == "redis"

    @pytest.mark.asyncio
    async def test_no_redirect_for_varied_topics(self):
        orch = self._make_orchestrator()
        eval_ = self._make_evaluation()
        c = self._make_candidate_state()

        from app.ai.orchestrators.contracts.interview_contracts import (
            InterviewPhase, InterviewerMood
        )
        from app.ai.orchestrators.state.interview_runtime_state import QuestionState

        topics = [
            ("We used redis for caching.", "caching question"),
            ("Kafka handles our event streaming.", "event streaming question"),
            ("Postgres is our primary database.", "database question"),
        ]

        for i, (transcript, q_text) in enumerate(topics):
            q = QuestionState(
                question_id=f"q{i}",
                question_text=q_text,
                question_type="initial",
                domain="backend",
                difficulty="medium",
                target_topics=[],
            )
            d = await orch.analyze_turn(
                session_id="s1",
                turn_number=i,
                transcript=transcript,
                evaluation=eval_,
                current_question=q,
                candidate_state=c,
                current_phase=InterviewPhase.TECHNICAL_ROUND_1,
                interviewer_mood=InterviewerMood.NEUTRAL,
                consecutive_followups=0,
                max_followup_depth=3,
            )
            assert d.action != TurnAction.BREADTH_REDIRECT, (
                f"Unexpected redirect on turn {i} with varied topics"
            )
