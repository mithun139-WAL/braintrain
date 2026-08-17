"""
Interview plan — an ordered list of topics to cover in a session, with a
depth/time budget per topic. Generated once at session start (see
plan_generator.py) and mutated in place, turn by turn, as the interview
progresses (see turn_decision.py).

Persisted as JSONB on InterviewSession.interview_plan (see
app/db/models/interview_session.py) so a reconnecting session resumes the
same plan instead of regenerating one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TopicStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class PlanTopic:
    topic_id: str
    label: str
    target_depth: int = 2          # max follow-ups before forced pivot/move-on
    time_budget_turns: int = 4     # max turns spent on this topic (all angles combined)
    status: TopicStatus = TopicStatus.NOT_STARTED

    # Per-topic conversation state (Step 2). Lives on the topic itself since
    # only one topic is ever "current" at a time — no need for a separate
    # parallel state object duplicating topic_id.
    depth_count: int = 0    # follow-ups asked on the current angle
    turns_spent: int = 0    # turns spent on this topic, across all angles
    angles_used: int = 0    # how many times we've pivoted to a new angle

    def to_dict(self) -> dict:
        d = dict(self.__dict__)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "PlanTopic":
        data = dict(data)
        data["status"] = TopicStatus(data.get("status", "not_started"))
        return cls(**data)


@dataclass
class InterviewPlan:
    topics: list[PlanTopic] = field(default_factory=list)
    max_angles_per_topic: int = 1  # how many pivots allowed before forcing NEXT_TOPIC

    def current(self) -> PlanTopic | None:
        for t in self.topics:
            if t.status == TopicStatus.IN_PROGRESS:
                return t
        return None

    def next_not_started(self) -> PlanTopic | None:
        for t in self.topics:
            if t.status == TopicStatus.NOT_STARTED:
                return t
        return None

    def all_completed(self) -> bool:
        return all(t.status == TopicStatus.COMPLETED for t in self.topics)

    def to_dict(self) -> dict:
        return {
            "topics": [t.to_dict() for t in self.topics],
            "max_angles_per_topic": self.max_angles_per_topic,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InterviewPlan":
        return cls(
            topics=[PlanTopic.from_dict(t) for t in data.get("topics", [])],
            max_angles_per_topic=data.get("max_angles_per_topic", 1),
        )
