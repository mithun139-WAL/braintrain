import time
import logging
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.policies.turn_policy import TurnPolicy
from app.ai.voice.policies.difficulty_policy import DifficultyPolicy
from app.ai.voice.events.bus import EventBus
from app.ai.voice.events.event import Event
from app.ai.voice.events.event_types import EventType

logger = logging.getLogger("policy_handler")

class PolicyHandler:
    def __init__(
        self,
        state: InterviewState,
        turn_policy: TurnPolicy,
        difficulty_policy: DifficultyPolicy,
        event_bus: EventBus,
    ):
        self.state = state
        self.turn_policy = turn_policy
        self.difficulty_policy = difficulty_policy
        self.event_bus = event_bus

    async def on_transcript_received(self, event: Event) -> None:
        """Runs the turn policies after candidate transcript is received."""
        start_time = time.perf_counter()
        tracker = getattr(self.state, "latency_tracker", None)
        if tracker:
            tracker.track_stage_start("policy")

        # 1. Database Difficulty Adjustment
        from app.db.session import SessionLocal
        try:
            async with SessionLocal() as db:
                await self.difficulty_policy.adjust_difficulty(db, self.state)
        except Exception as exc:
            logger.error("policy_handler | failed to adjust difficulty: %s", exc)

        # 2. Decide next action using TurnPolicy
        decision = self.turn_policy.decide_next_action(self.state)
        
        if tracker:
            tracker.track_stage_end("policy")

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "policy_handler | decision calculated: %s | reason: %s | latency: %dms",
            decision.action.value,
            decision.reason,
            latency_ms
        )

        # 3. Emit DECISION_CREATED
        await self.event_bus.emit(
            Event(
                type=EventType.DECISION_CREATED,
                session_id=event.session_id,
                payload={"decision": decision},
                metadata={"policy_latency_ms": latency_ms}
            )
        )
