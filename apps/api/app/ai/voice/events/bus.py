import time
import inspect
import asyncio
import logging
from typing import Callable, Any, Dict, List
from app.ai.voice.events.event_types import EventType
from app.ai.voice.events.event import Event

logger = logging.getLogger("event_bus")

class EventBus:
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable[[Event], Any]]] = {}

    def subscribe(self, event_type: EventType, handler: Callable[[Event], Any]) -> None:
        """Subscribes an event handler to a specific EventType."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug("event_subscribed | type: %s | handler: %s", event_type.name, handler.__name__ if hasattr(handler, "__name__") else str(handler))

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], Any]) -> None:
        """Unsubscribes an event handler from a specific EventType."""
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug("event_unsubscribed | type: %s | handler: %s", event_type.name, handler.__name__ if hasattr(handler, "__name__") else str(handler))

    async def emit(self, event: Event) -> None:
        """
        Emits an Event asynchronously. All registered handlers for the EventType 
        are dispatched concurrently in separate tasks to prevent blocking.
        """
        handlers = self._handlers.get(event.type, [])
        if not handlers:
            return

        for handler in handlers:
            asyncio.create_task(self._safe_execute(handler, event))

    async def _safe_execute(self, handler: Callable[[Event], Any], event: Event) -> None:
        start_time = time.perf_counter()
        
        # Format handler name for clean structured logs
        handler_name = getattr(handler, "__name__", str(handler))
        if hasattr(handler, "__self__"):
            handler_name = f"{handler.__self__.__class__.__name__}.{handler_name}"

        try:
            if inspect.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
            
            processing_time = time.perf_counter() - start_time
            logger.info(
                "event_processed | type: %s | session_id: %s | duration_s: %.4f | handler: %s",
                event.type.name,
                event.session_id,
                processing_time,
                handler_name,
            )
        except Exception as exc:
            processing_time = time.perf_counter() - start_time
            logger.exception(
                "event_failed | type: %s | session_id: %s | duration_s: %.4f | handler: %s | error: %s",
                event.type.name,
                event.session_id,
                processing_time,
                handler_name,
                exc,
            )
