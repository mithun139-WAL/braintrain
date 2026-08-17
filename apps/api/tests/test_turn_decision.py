"""
Unit tests for the interview plan / turn decision policy (topic coverage fix).

Run:
    cd apps/api && .venv/bin/python -m pytest tests/test_turn_decision.py -v
"""
from app.ai.voice.planning.plan import InterviewPlan, PlanTopic, TopicStatus
from app.ai.voice.planning.plan_generator import InterviewPlanGenerator
from app.ai.voice.planning.sufficiency import AnswerSufficiency
from app.ai.voice.planning.turn_decision import TurnDecisionAction, decide_next_turn


def _plan(*topics: PlanTopic, max_angles_per_topic: int = 1) -> InterviewPlan:
    if topics:
        topics[0].status = TopicStatus.IN_PROGRESS
    return InterviewPlan(topics=list(topics), max_angles_per_topic=max_angles_per_topic)


class TestDepthCap:
    def test_depth_cap_forces_pivot_even_with_juicy_answer(self):
        topic = PlanTopic(topic_id="t1", label="backend", target_depth=2, time_budget_turns=10, depth_count=2)
        plan = _plan(topic)

        # Sufficiency is deliberately low ("juicy"/interesting answer, not yet
        # sufficient) — depth cap must still win, never PROBE.
        juicy_but_incomplete = AnswerSufficiency(score=2, rationale="interesting but incomplete")
        decision = decide_next_turn(plan, juicy_but_incomplete)

        assert decision.action in (TurnDecisionAction.PIVOT, TurnDecisionAction.NEXT_TOPIC)
        assert decision.action != TurnDecisionAction.PROBE

    def test_depth_cap_with_no_room_left_goes_straight_to_next_topic(self):
        topic = PlanTopic(topic_id="t1", label="backend", target_depth=2, time_budget_turns=10, depth_count=2)
        topic2 = PlanTopic(topic_id="t2", label="frontend")
        plan = _plan(topic, topic2, max_angles_per_topic=0)  # no pivots allowed

        decision = decide_next_turn(plan, None)

        assert decision.action == TurnDecisionAction.NEXT_TOPIC
        assert decision.topic_id == "t2"
        assert topic.status == TopicStatus.COMPLETED
        assert topic2.status == TopicStatus.IN_PROGRESS


class TestSufficiencyShortCircuit:
    def test_high_sufficiency_on_first_answer_skips_forced_followup(self):
        topic = PlanTopic(topic_id="t1", label="system design", target_depth=3, time_budget_turns=10, depth_count=0)
        topic2 = PlanTopic(topic_id="t2", label="behavioral")
        plan = _plan(topic, topic2)

        excellent = AnswerSufficiency(score=5, rationale="thorough, complete answer")
        decision = decide_next_turn(plan, excellent)

        assert decision.action in (TurnDecisionAction.PIVOT, TurnDecisionAction.NEXT_TOPIC)

    def test_low_sufficiency_keeps_probing(self):
        topic = PlanTopic(topic_id="t1", label="system design", target_depth=3, time_budget_turns=10, depth_count=0)
        plan = _plan(topic)

        weak = AnswerSufficiency(score=2, rationale="shallow answer")
        decision = decide_next_turn(plan, weak)

        assert decision.action == TurnDecisionAction.PROBE
        assert topic.depth_count == 1

    def test_sufficiency_only_short_circuits_early_rounds(self):
        # depth_count already at 2 (past the "early rounds" window) — a high
        # score no longer short-circuits via the sufficiency rule specifically,
        # but the depth cap rule (target_depth=3, so not yet capped) does NOT
        # fire either, so this should still PROBE.
        topic = PlanTopic(topic_id="t1", label="system design", target_depth=3, time_budget_turns=10, depth_count=2)
        plan = _plan(topic)

        excellent = AnswerSufficiency(score=5, rationale="thorough")
        decision = decide_next_turn(plan, excellent, sufficiency_early_rounds=2)

        assert decision.action == TurnDecisionAction.PROBE


class TestTimeBudget:
    def test_time_budget_exhaustion_forces_next_topic_regardless_of_depth(self):
        topic = PlanTopic(topic_id="t1", label="backend", target_depth=5, time_budget_turns=2, turns_spent=2, depth_count=0)
        topic2 = PlanTopic(topic_id="t2", label="frontend")
        plan = _plan(topic, topic2)

        # A juicy, low-depth-count answer would normally PROBE — but the time
        # budget rule must win and never PIVOT (goes straight to NEXT_TOPIC).
        decision = decide_next_turn(plan, AnswerSufficiency(score=1, rationale="shallow"))

        assert decision.action == TurnDecisionAction.NEXT_TOPIC
        assert decision.topic_id == "t2"


class TestWrapUp:
    def test_all_topics_completed_wraps_up(self):
        topic = PlanTopic(topic_id="t1", label="backend", status=TopicStatus.COMPLETED)
        plan = InterviewPlan(topics=[topic])  # no IN_PROGRESS topic

        decision = decide_next_turn(plan, None)

        assert decision.action == TurnDecisionAction.WRAP_UP
        assert decision.topic_id is None

    def test_next_topic_with_none_remaining_wraps_up(self):
        topic = PlanTopic(topic_id="t1", label="backend", target_depth=1, time_budget_turns=10, depth_count=1)
        plan = _plan(topic, max_angles_per_topic=0)  # only one topic, no pivots allowed

        decision = decide_next_turn(plan, None)

        assert decision.action == TurnDecisionAction.WRAP_UP


class TestPlanGenerationGenericity:
    def test_fallback_labels_are_generic_not_hardcoded_to_tech(self):
        backend_labels = InterviewPlanGenerator._fallback_labels("Full Stack Developer", "TECHNICAL")
        pm_labels = InterviewPlanGenerator._fallback_labels("Product Manager", "BEHAVIORAL")

        # Same generic skeleton shape for both — no tech-specific terms baked in.
        assert "candidate background" in backend_labels
        assert "candidate background" in pm_labels
        assert "Full Stack Developer" in backend_labels
        assert "Product Manager" in pm_labels
        for forbidden in ("redis", "kafka", "sql", "react"):
            assert forbidden not in " ".join(backend_labels).lower()
            assert forbidden not in " ".join(pm_labels).lower()

    def test_parse_labels_from_valid_json_array(self):
        raw = 'Sure, here you go:\n["candidate background", "APIs", "behavioral"]'
        labels = InterviewPlanGenerator._parse_labels(raw)
        assert labels == ["candidate background", "APIs", "behavioral"]

    def test_parse_labels_returns_empty_on_garbage(self):
        assert InterviewPlanGenerator._parse_labels("not json at all") == []
        assert InterviewPlanGenerator._parse_labels("") == []

    async def test_generate_falls_back_when_llm_call_fails(self, monkeypatch):
        generator = InterviewPlanGenerator()

        async def _boom(*args, **kwargs):
            raise RuntimeError("network down")

        monkeypatch.setattr(generator.response_generator, "generate", _boom)

        plan = await generator.generate(
            topic_name="Product Manager",
            interview_category="BEHAVIORAL",
            difficulty="MEDIUM",
            duration_minutes=15,
        )

        assert len(plan.topics) == 4
        assert plan.topics[0].status == TopicStatus.IN_PROGRESS
        assert all(t.status == TopicStatus.NOT_STARTED for t in plan.topics[1:])


class TestPlanRoundTrip:
    def test_to_dict_from_dict_round_trip(self):
        topic = PlanTopic(topic_id="t1", label="backend", depth_count=1, status=TopicStatus.IN_PROGRESS)
        plan = InterviewPlan(topics=[topic])

        restored = InterviewPlan.from_dict(plan.to_dict())

        assert restored.topics[0].topic_id == "t1"
        assert restored.topics[0].status == TopicStatus.IN_PROGRESS
        assert restored.topics[0].depth_count == 1
