"""
Turn decision policy — decides what to do next, given an interview plan and
a sufficiency signal for the candidate's last answer. Pure and synchronous:
no I/O, no LLM calls, fully unit-testable in isolation (see
tests/test_turn_decision.py).

This sits in front of question generation (interview_prompt_builder.py /
interviewer.py) as a hard constraint, not a suggestion — the model never
freely decides to keep probing.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.ai.voice.planning.plan import InterviewPlan, PlanTopic, TopicStatus
from app.ai.voice.planning.sufficiency import AnswerSufficiency

# Default thresholds — configurable via decide_next_turn() kwargs.
DEFAULT_SUFFICIENCY_THRESHOLD = 4       # score >= this short-circuits a forced follow-up
DEFAULT_SUFFICIENCY_EARLY_ROUNDS = 2    # only short-circuits on the 1st/2nd answer for a topic


class TurnDecisionAction(str, Enum):
    PROBE = "PROBE"            # ask a deeper follow-up on the same topic thread
    PIVOT = "PIVOT"            # same broad topic, different angle, reset depth_count
    NEXT_TOPIC = "NEXT_TOPIC"  # move to the next topic in the plan
    WRAP_UP = "WRAP_UP"        # no topics remain / budget exhausted


@dataclass
class TurnDecision:
    action: TurnDecisionAction
    topic_id: Optional[str]
    rationale: str


def decide_next_turn(
    plan: InterviewPlan,
    last_answer_eval: Optional[AnswerSufficiency] = None,
    *,
    sufficiency_threshold: int = DEFAULT_SUFFICIENCY_THRESHOLD,
    sufficiency_early_rounds: int = DEFAULT_SUFFICIENCY_EARLY_ROUNDS,
) -> TurnDecision:
    """
    Mutates `plan` in place (advances/pivots the current topic) and returns
    the resulting decision. Call once per candidate turn, after incrementing
    the current topic's `turns_spent`.
    """
    topic = plan.current()
    if topic is None:
        return TurnDecision(TurnDecisionAction.WRAP_UP, None, "no topics remain in the plan")

    # Rule: time budget exhausted → NEXT_TOPIC, no PIVOT allowed, regardless of depth.
    if topic.turns_spent >= topic.time_budget_turns:
        return _next_topic(plan, topic, "time budget exhausted for this topic")

    # Rule: depth cap reached → force PIVOT or NEXT_TOPIC, never PROBE.
    if topic.depth_count >= topic.target_depth:
        return _advance(plan, topic, "depth cap reached")

    # Rule: high sufficiency on an early answer → don't force a token follow-up.
    if (
        last_answer_eval is not None
        and last_answer_eval.score >= sufficiency_threshold
        and topic.depth_count < sufficiency_early_rounds
    ):
        return _advance(
            plan, topic,
            f"sufficiency score {last_answer_eval.score}/5 on an early answer — no forced follow-up needed",
        )

    # Otherwise: keep probing this thread.
    topic.depth_count += 1
    return TurnDecision(TurnDecisionAction.PROBE, topic.topic_id, "within depth/time budget, probing deeper")


def _advance(plan: InterviewPlan, topic: PlanTopic, reason: str) -> TurnDecision:
    """Choose PIVOT (new angle, same topic) or NEXT_TOPIC, honoring max_angles_per_topic."""
    has_time_left = topic.turns_spent < topic.time_budget_turns
    if topic.angles_used < plan.max_angles_per_topic and has_time_left:
        topic.angles_used += 1
        topic.depth_count = 0
        return TurnDecision(TurnDecisionAction.PIVOT, topic.topic_id, reason)
    return _next_topic(plan, topic, reason)


def _next_topic(plan: InterviewPlan, topic: PlanTopic, reason: str) -> TurnDecision:
    topic.status = TopicStatus.COMPLETED
    nxt = plan.next_not_started()
    if nxt is None:
        return TurnDecision(TurnDecisionAction.WRAP_UP, None, f"{reason}; no topics remain")
    nxt.status = TopicStatus.IN_PROGRESS
    return TurnDecision(TurnDecisionAction.NEXT_TOPIC, nxt.topic_id, reason)
