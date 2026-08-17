"""
Generates a session's InterviewPlan — an ordered list of topics to cover.

Deliberately generic: the plan is derived from whatever role/topic/category
the session already carries (nothing here is hardcoded to a tech stack), so
the same generator produces a sensible plan for "Full Stack Developer",
"Product Manager", a behavioral-only session, etc.

Uses the same LLM plumbing as the rest of the voice agent (ResponseGenerator
→ NVIDIA NIM). If the call fails or returns something unparseable, falls
back to a fixed generic skeleton rather than blocking session start.
"""
from __future__ import annotations

import json
import logging
import re
import uuid

from app.ai.voice.llm.response_generator import ResponseGenerator
from app.ai.voice.planning.plan import InterviewPlan, PlanTopic, TopicStatus

logger = logging.getLogger("interview_plan_generator")

_DEFAULT_TARGET_DEPTH = 2
_DEFAULT_TIME_BUDGET_TURNS = 4


class InterviewPlanGenerator:
    def __init__(self, response_generator: ResponseGenerator | None = None):
        self.response_generator = response_generator or ResponseGenerator()

    async def generate(
        self,
        *,
        topic_name: str,
        interview_category: str,
        difficulty: str,
        duration_minutes: int = 15,
    ) -> InterviewPlan:
        try:
            labels = await self._generate_topic_labels(
                topic_name=topic_name,
                interview_category=interview_category,
                difficulty=difficulty,
                duration_minutes=duration_minutes,
            )
        except Exception as exc:
            logger.warning("plan_generation_failed | falling back to generic plan | error: %s", exc)
            labels = []

        if not labels:
            labels = self._fallback_labels(topic_name, interview_category)

        # Budget turns roughly evenly across topics within the session duration,
        # leaving headroom for intro/wrap-up. Minimum 3 turns/topic.
        per_topic_budget = max(3, (duration_minutes * 2) // max(len(labels), 1))

        topics = [
            PlanTopic(
                topic_id=str(uuid.uuid4()),
                label=label,
                target_depth=_DEFAULT_TARGET_DEPTH,
                time_budget_turns=min(per_topic_budget, _DEFAULT_TIME_BUDGET_TURNS + 2),
                status=TopicStatus.NOT_STARTED,
            )
            for label in labels
        ]
        if topics:
            topics[0].status = TopicStatus.IN_PROGRESS

        plan = InterviewPlan(topics=topics)
        logger.info(
            "interview_plan_generated | topic=%s | category=%s | labels=%s",
            topic_name, interview_category, labels,
        )
        return plan

    async def _generate_topic_labels(
        self, *, topic_name: str, interview_category: str, difficulty: str, duration_minutes: int
    ) -> list[str]:
        prompt = (
            "You are planning the topic coverage for a single interview session. "
            f"Role/topic: {topic_name}. Interview category: {interview_category}. "
            f"Difficulty: {difficulty}. Duration: {duration_minutes} minutes.\n\n"
            "Produce an ordered list of 3-5 topics to cover during this interview, "
            "generic to this role/topic (do not assume any specific technology unless "
            "it is literally the role/topic given). Always include a brief candidate "
            "background/warm-up topic first. Reply with ONLY a JSON array of short "
            "topic labels, e.g. [\"candidate background\", \"core technical area\", "
            "\"system design / scenario\", \"behavioral\"]."
        )
        raw = await self.response_generator.generate([{"role": "system", "content": prompt}])
        return self._parse_labels(raw)

    @staticmethod
    def _parse_labels(raw: str) -> list[str]:
        if not raw:
            return []
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return []
        try:
            parsed = json.loads(match.group(0))
        except (json.JSONDecodeError, ValueError):
            return []
        labels = [str(x).strip() for x in parsed if str(x).strip()]
        return labels[:5]

    @staticmethod
    def _fallback_labels(topic_name: str, interview_category: str) -> list[str]:
        # ponytail: generic 4-topic skeleton, no tech-specific assumptions.
        # Upgrade path: role-specific templates once enough sessions exist to
        # justify curating them (see task spec Step 1 "load from a template").
        return [
            "candidate background",
            topic_name or interview_category or "core topic",
            "topic surfaced from resume/JD",
            "behavioral",
        ]
