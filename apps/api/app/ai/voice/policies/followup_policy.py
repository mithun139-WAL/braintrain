import logging

logger = logging.getLogger("followup_policy")

# Technical concepts that warrant a single follow-up probe.
# Deliberately NARROW — only specific, actionable technical signals.
# Generic words like "use", "work", "build" are excluded on purpose.
_KEY_CONCEPTS = [
    "cache", "caching", "redis", "memcached",
    "index", "indexing", "query plan", "explain analyze",
    "sharding", "partitioning", "replication",
    "message queue", "kafka", "rabbitmq", "pubsub",
    "race condition", "deadlock", "transaction", "acid",
    "rate limit", "circuit breaker", "retry",
    "load balanc", "reverse proxy", "nginx",
    "eventual consistency", "cap theorem",
    "websocket", "grpc", "graphql",
    "n+1", "lazy load", "eager load",
]

# Max follow-ups allowed on a single topic before forcing breadth
_MAX_FOLLOWUPS_PER_TOPIC = 2


class FollowupPolicy:
    """
    Decides whether the current candidate answer warrants a follow-up probe.

    Key design constraints:
    - Hard-capped at _MAX_FOLLOWUPS_PER_TOPIC per topic — prevents infinite drilling
    - Only fires on specific, non-trivial technical signals
    - Requires minimum answer length to avoid following up on one-word replies
    """

    def __init__(
        self,
        key_concepts: list[str] | None = None,
        max_followups_per_topic: int = _MAX_FOLLOWUPS_PER_TOPIC,
        min_answer_words: int = 15,
    ):
        self.key_concepts = key_concepts or _KEY_CONCEPTS
        self.max_followups_per_topic = max_followups_per_topic
        self.min_answer_words = min_answer_words

    def should_followup(self, state) -> bool:
        # ── Hard cap: never exceed max follow-ups on one topic ──────────────────
        current_followups = getattr(state.conversation, "topic_followup_count", 0)
        if current_followups >= self.max_followups_per_topic:
            logger.info(
                "followup_blocked | topic_followup_count=%d >= cap=%d → force topic move",
                current_followups,
                self.max_followups_per_topic,
            )
            return False

        # ── Minimum answer length guard ─────────────────────────────────────────
        user_msgs = [m for m in state.conversation.messages if m.role == "user"]
        if not user_msgs:
            return False

        last_answer = user_msgs[-1].content
        if len(last_answer.split()) < self.min_answer_words:
            logger.info("followup_blocked | answer too short (%d words)", len(last_answer.split()))
            return False

        # ── Specific technical concept match ────────────────────────────────────
        text_lower = last_answer.lower()
        for concept in self.key_concepts:
            if concept in text_lower:
                logger.info(
                    "followup_approved | matched_concept='%s' | followup_count=%d/%d",
                    concept,
                    current_followups,
                    self.max_followups_per_topic,
                )
                return True

        return False

    def generate_followup_context(self, state) -> str:
        user_msgs = [m for m in state.conversation.messages if m.role == "user"]
        if not user_msgs:
            return ""

        text_lower = user_msgs[-1].content.lower()
        matched = [c for c in self.key_concepts if c in text_lower]

        if matched:
            # Surface the most specific matched concept, not a generic list
            primary = matched[0]
            return (
                f"The candidate specifically mentioned '{primary}'. "
                f"Ask ONE precise follow-up about their hands-on experience with it — "
                f"what problem it solved, what tradeoff they encountered, or what they'd do differently. "
                f"Do NOT ask about unrelated topics."
            )
        return ""
