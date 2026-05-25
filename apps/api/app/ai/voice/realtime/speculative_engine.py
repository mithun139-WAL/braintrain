import asyncio
import logging
from typing import Dict, Optional, Any
from app.ai.voice.events.bus import EventBus
from app.ai.voice.events.event import Event
from app.ai.voice.events.event_types import EventType
from app.ai.voice.realtime.response_cache import ResponseCache
from app.ai.voice.realtime.response_prefetcher import ResponsePrefetcher

logger = logging.getLogger("speculative_engine")

class SpeculativeEngine:
    def __init__(self, event_bus: EventBus, response_cache: ResponseCache, response_prefetcher: ResponsePrefetcher):
        self.event_bus = event_bus
        self.response_cache = response_cache
        self.response_prefetcher = response_prefetcher
        self.current_token: int = 0
        self.pending_tasks: Dict[str, asyncio.Task] = {}

    def get_new_cancellation_token(self) -> int:
        """
        Increments and returns a new cancellation token.
        Calling this cancels all previous speculative tasks.
        """
        self.current_token += 1
        self.cancel_pending()
        logger.info("speculative_engine | new token issued: %d | stale tasks cancelled", self.current_token)
        return self.current_token

    def is_token_valid(self, token: int) -> bool:
        """Checks if the given token matches the active turn token."""
        return token == self.current_token

    def prepare_prompt(self, session_id: str, token: int, state: Any, decision: Any) -> None:
        """
        Speculatively triggers lightweight prompt layers assembly.
        Registers the speculative background task.
        """
        task_name = f"prompt_{session_id}"
        
        async def run_speculation():
            await self.event_bus.emit(
                Event(
                    type=EventType.SPECULATIVE_TASK_STARTED,
                    session_id=session_id,
                    payload={"task": "prepare_prompt", "token": token}
                )
            )
            
            # Simulate prompt formatting context
            await asyncio.sleep(0.01)
            
            if not self.is_token_valid(token):
                logger.info("speculative_engine | prepare_prompt | cancelled by token check")
                await self.event_bus.emit(
                    Event(
                        type=EventType.SPECULATIVE_TASK_CANCELLED,
                        session_id=session_id,
                        payload={"task": "prepare_prompt", "token": token}
                    )
                )
                return

            # Cache the precompiled context for prompt lookup
            cache_key = f"prebuilt_prompt_{session_id}"
            self.response_cache.set(cache_key, {"decision_action": decision.action.value}, ttl_seconds=15.0)
            
            await self.event_bus.emit(
                Event(
                    type=EventType.PROMPT_PREFETCHED,
                    session_id=session_id,
                    payload={"task": "prepare_prompt", "token": token}
                )
            )
            logger.info("speculative_engine | prompt pre-built successfully for token: %d", token)

        # Spawn task
        task = asyncio.create_task(run_speculation())
        self.pending_tasks[task_name] = task

    def prepare_followup(self, session_id: str, token: int, active_topic: str) -> None:
        """Speculatively prefetches topic-related mockup prompts."""
        task_name = f"followup_{session_id}"

        async def run_followup_speculation():
            await self.event_bus.emit(
                Event(
                    type=EventType.SPECULATIVE_TASK_STARTED,
                    session_id=session_id,
                    payload={"task": "prepare_followup", "token": token}
                )
            )

            # Prefetch context using matched topics
            prefetched_context = self.response_prefetcher.prefetch_context(active_topic)
            await asyncio.sleep(0.01)

            if not self.is_token_valid(token):
                logger.info("speculative_engine | prepare_followup | cancelled by token check")
                return

            if prefetched_context:
                cache_key = f"prebuilt_followup_{session_id}"
                self.response_cache.set(cache_key, prefetched_context, ttl_seconds=15.0)
                logger.info("speculative_engine | followup pre-fetched successfully for token: %d", token)

        task = asyncio.create_task(run_followup_speculation())
        self.pending_tasks[task_name] = task

    def cancel_pending(self) -> None:
        """Cancels all currently running speculative tasks."""
        for name, task in list(self.pending_tasks.items()):
            if not task.done():
                task.cancel()
                logger.debug("speculative_engine | cancelled task: %s", name)
        self.pending_tasks.clear()
