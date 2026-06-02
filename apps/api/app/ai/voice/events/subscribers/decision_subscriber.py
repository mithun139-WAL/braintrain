import time
import logging
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.llm.interviewer import Interviewer
from app.ai.voice.events.bus import EventBus
from app.ai.voice.events.event import Event
from app.ai.voice.events.event_types import EventType

logger = logging.getLogger("decision_subscriber")

class DecisionSubscriber:
    def __init__(self, state: InterviewState, interviewer: Interviewer, event_bus: EventBus):
        self.state = state
        self.interviewer = interviewer
        self.event_bus = event_bus

    async def on_decision_created(self, event: Event) -> None:
        """Listens to decisions to invoke Interviewer response generation turns."""
        decision = event.payload.get("decision")
        if not decision:
            return

        # Start timer for LLM generation metrics
        start_time = time.perf_counter()

        logger.info("decision_subscriber | decision received: %s -> generating LLM response", decision.action.value)
        
        # Mark latency start/end of LLM generation
        tracker = getattr(self.state, "latency_tracker", None)
        if tracker:
            tracker.track_stage_start("llm")
        
        # Invoke Interviewer to generate prompt layers, call provider, parse and format response
        res = await self.interviewer.respond(self.state, decision)

        if tracker:
            tracker.track_stage_end("llm")

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "decision_subscriber | response generated | speaker: %s | latency: %dms",
            res.get("speaker_name"),
            latency_ms
        )

        # Emit RESPONSE_GENERATED event
        await self.event_bus.emit(
            Event(
                type=EventType.RESPONSE_GENERATED,
                session_id=event.session_id,
                payload={
                    "raw_text": res["raw_text"],
                    "clean_text": res["clean_text"],
                    "speaker_name": res["speaker_name"],
                    "voice_name": res["voice_name"]
                },
                metadata={
                    "generation_latency_ms": latency_ms,
                    "decision": decision,
                    **event.metadata  # Preserve policy latency
                }
            )
        )
