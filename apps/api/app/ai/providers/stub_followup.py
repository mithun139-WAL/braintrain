"""
StubFollowupProvider — zero-cost fallback for local dev and degraded mode.

Always returns needs_followup=False so the session flow is never blocked
when no API key is configured or the LLM call fails.
"""
from app.ai.protocols import FollowupInput, FollowupSignal


class StubFollowupProvider:
    """Stub follow-up provider — always signals answer is sufficient."""

    async def analyze(self, input: FollowupInput) -> FollowupSignal:
        return FollowupSignal(
            needs_followup=False,
            followup_question=None,
            acknowledgement="Good answer. Moving to the next question.",
            gap_identified=None,
        )
