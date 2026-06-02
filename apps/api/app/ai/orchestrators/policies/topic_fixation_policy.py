"""
Topic Fixation Policy — session-level breadth guard.

Problem this solves:
    The TurnOrchestrator only counts `consecutive_followups` per question.
    When a candidate keeps circling one tool (e.g. "redis"), the orchestrator
    happily issues PROBE_DEEPER / FOLLOW_UP turn after turn across MULTIPLE
    questions because its counter resets each time we call should_reset_followup_chain().

    This policy watches topic exposure counts across the whole session and
    fires a BREADTH_REDIRECT action when a single topic has dominated too
    many turns — regardless of question boundaries.

Integration:
    TurnOrchestrator._determine_action() checks this policy BEFORE the
    answer-quality routing table (priority 1.5 — after escalation, before depth).
"""
from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, PrivateAttr

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical topic normalisation map
# Map surface forms → canonical concept key used for counting.
# Extend as needed; matching is case-insensitive substring.
# ---------------------------------------------------------------------------
_TOPIC_ALIASES: Dict[str, str] = {
    # Caching / data-stores
    "redis": "redis",
    "memcached": "memcached",
    "cache": "caching",
    "caching": "caching",
    # Messaging
    "kafka": "kafka",
    "rabbitmq": "rabbitmq",
    "pubsub": "pubsub",
    "message queue": "message_queue",
    # Databases
    "postgres": "postgres",
    "postgresql": "postgres",
    "mysql": "mysql",
    "mongodb": "mongodb",
    "dynamo": "dynamodb",
    "dynamodb": "dynamodb",
    "cassandra": "cassandra",
    # Search
    "elasticsearch": "elasticsearch",
    "opensearch": "opensearch",
    # API / Architecture
    "rest": "rest_api",
    "graphql": "graphql",
    "grpc": "grpc",
    "websocket": "websocket",
    "api design": "api_design",
    # Infrastructure
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "docker": "docker",
    "aws": "aws",
    "gcp": "gcp",
    "azure": "azure",
    # Patterns
    "microservice": "microservices",
    "monolith": "monolith",
    "event sourcing": "event_sourcing",
    "cqrs": "cqrs",
    "cap theorem": "cap_theorem",
    "consistency": "consistency",
    "availability": "availability",
}


def _extract_topics(text: str) -> List[str]:
    """
    Return canonical topic keys detected in *text*.
    Matches are case-insensitive; multi-word phrases matched before singles.
    """
    text_lower = text.lower()
    found: List[str] = []
    # Sort by length desc so multi-word phrases win over substrings
    for surface, canonical in sorted(_TOPIC_ALIASES.items(), key=lambda x: -len(x[0])):
        if re.search(r"\b" + re.escape(surface) + r"\b", text_lower):
            found.append(canonical)
    # Deduplicate while preserving first-match order
    seen: set = set()
    unique: List[str] = []
    for t in found:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


class TopicFixationConfig(BaseModel):
    """Tunable thresholds for fixation detection."""

    # How many session turns on ONE topic before triggering breadth redirect
    max_topic_turns_per_session: int = 4

    # What fraction of total session turns a single topic may occupy
    max_topic_fraction: float = 0.40

    # Minimum total turns before fraction check activates (avoids false positives early)
    min_turns_for_fraction_check: int = 6

    # Cooldown: after a breadth-redirect, don't re-fire for this many turns
    redirect_cooldown_turns: int = 3

    # Broad context prompt template injected into TurnDecision metadata
    breadth_redirect_prompt: str = (
        "Let's step back — what other architectural decisions did you consider "
        "beyond {topic}? I want to understand the bigger picture."
    )


class TopicFixationTracker(BaseModel):
    """Per-session state for topic fixation detection."""

    session_id: str
    config: TopicFixationConfig = Field(default_factory=TopicFixationConfig)

    # topic → total turn count this session
    topic_turn_counts: Dict[str, int] = Field(default_factory=dict)

    # Total turns processed (for fraction calculation)
    total_turns: int = 0

    # Turns since last breadth-redirect (cooldown)
    turns_since_last_redirect: int = Field(default=999)

    # Which topic triggered the last redirect
    last_redirected_topic: Optional[str] = None

    # Private: one-shot idempotency cache for check_fixation() within a single turn.
    # Cleared on each record_turn() call.
    _pending_redirect: Optional[Tuple[bool, Optional[str], Optional[str]]] = PrivateAttr(default=None)

    def record_turn(self, transcript: str, question_text: str) -> None:
        """
        Call once per TRANSCRIPT_RECEIVED turn BEFORE calling check_fixation().
        Only the candidate *transcript* is used for topic counting — the question
        text is excluded so the interviewer's own phrasing does not inflate counts.
        Increments cooldown counter and clears any stale pending result.
        """
        self.total_turns += 1
        self.turns_since_last_redirect += 1
        self._pending_redirect = None  # invalidate stale cache

        topics = _extract_topics(transcript)  # transcript only — not question_text
        for t in topics:
            self.topic_turn_counts[t] = self.topic_turn_counts.get(t, 0) + 1

    def check_fixation(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Inspect current state and decide whether to trigger a breadth redirect.

        Idempotent within a single turn: the first call computes the result and
        caches it; subsequent calls within the same turn return the cached value
        without re-registering the cooldown.  The cache is cleared on the next
        call to record_turn().

        Returns:
            (should_redirect, dominant_topic, redirect_prompt)
        """
        if self._pending_redirect is not None:
            return self._pending_redirect

        result = self._compute_fixation()
        self._pending_redirect = result
        return result

    def _compute_fixation(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Internal: compute fixation without caching side-effects."""
        if not self.topic_turn_counts:
            return False, None, None

        # Cooldown guard
        if self.turns_since_last_redirect < self.config.redirect_cooldown_turns:
            logger.debug(
                "TopicFixation cooldown active (%d/%d)",
                self.turns_since_last_redirect,
                self.config.redirect_cooldown_turns,
            )
            return False, None, None

        # Find the most-discussed topic
        dominant_topic, max_count = max(
            self.topic_turn_counts.items(), key=lambda kv: kv[1]
        )

        # --- Hard count threshold ---
        if max_count >= self.config.max_topic_turns_per_session:
            prompt = self.config.breadth_redirect_prompt.format(topic=dominant_topic.replace("_", " "))
            self._register_redirect(dominant_topic)
            logger.info(
                "TopicFixation: hard-count threshold hit — topic=%s count=%d",
                dominant_topic,
                max_count,
            )
            return True, dominant_topic, prompt

        # --- Fraction threshold (only after enough turns) ---
        if (
            self.total_turns >= self.config.min_turns_for_fraction_check
            and self.total_turns > 0
        ):
            fraction = max_count / self.total_turns
            if fraction >= self.config.max_topic_fraction:
                prompt = self.config.breadth_redirect_prompt.format(
                    topic=dominant_topic.replace("_", " ")
                )
                self._register_redirect(dominant_topic)
                logger.info(
                    "TopicFixation: fraction threshold hit — topic=%s fraction=%.2f",
                    dominant_topic,
                    fraction,
                )
                return True, dominant_topic, prompt

        return False, None, None

    def _register_redirect(self, topic: str) -> None:
        self.turns_since_last_redirect = 0
        self.last_redirected_topic = topic

    def get_topic_summary(self) -> Dict[str, int]:
        """Return a sorted snapshot of topic turn counts."""
        return dict(
            sorted(self.topic_turn_counts.items(), key=lambda kv: -kv[1])
        )
