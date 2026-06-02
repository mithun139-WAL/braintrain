import logging
from datetime import datetime
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.events.event import Event
from app.ai.voice.events.event_types import EventType

logger = logging.getLogger("metrics_handler")

class MetricsHandler:
    def __init__(self, state: InterviewState):
        self.state = state
        self._user_speech_start_time = None
        self._last_question_time = None

    def handle_event(self, event: Event) -> None:
        """
        Processes realtime conversation and system latency metrics.
        Updates state.candidate values in-memory.
        """
        c_state = self.state.candidate

        if event.type == EventType.QUESTION_ASKED:
            self._last_question_time = event.timestamp
            
        elif event.type == EventType.USER_STARTED_SPEAKING:
            self._user_speech_start_time = event.timestamp
            if self._last_question_time:
                # Calculate thinking time (silence duration before candidate spoke)
                thinking_time = (event.timestamp - self._last_question_time).total_seconds()
                # Update rolling average thinking seconds
                if c_state.avg_thinking_seconds == 0.0:
                    c_state.avg_thinking_seconds = thinking_time
                else:
                    c_state.avg_thinking_seconds = (c_state.avg_thinking_seconds + thinking_time) / 2.0
                logger.info("metrics_handler | thinking_time_s: %.2f", thinking_time)

        elif event.type == EventType.USER_STOPPED_SPEAKING:
            if self._user_speech_start_time:
                speaking_duration = (event.timestamp - self._user_speech_start_time).total_seconds()
                # Update rolling average response seconds
                if c_state.avg_response_seconds == 0.0:
                    c_state.avg_response_seconds = speaking_duration
                else:
                    c_state.avg_response_seconds = (c_state.avg_response_seconds + speaking_duration) / 2.0
                logger.info("metrics_handler | user_speaking_duration_s: %.2f", speaking_duration)
            self._user_speech_start_time = None

        elif event.type == EventType.INTERRUPTION_TRIGGERED:
            c_state.interruption_count += 1
            c_state.interruptions_attempted += 1
            logger.info("metrics_handler | interruption_count: %d", c_state.interruption_count)

        elif event.type == EventType.FOLLOWUP_TRIGGERED:
            c_state.followup_count += 1
            logger.info("metrics_handler | followup_count: %d", c_state.followup_count)

        elif event.type == EventType.TOPIC_CHANGED:
            c_state.topic_switches += 1
            logger.info("metrics_handler | topic_switches: %d", c_state.topic_switches)

        elif event.type == EventType.TRANSCRIPT_RECEIVED:
            # Simple verbosity check (words per response)
            text = event.payload.get("text", "")
            words = len(text.split())
            # Map word count to a 0-100 verbosity score (e.g. 30 words is ideal (50), more is high, less is low)
            c_state.verbosity_score = min(100.0, max(0.0, words * 1.5))
            c_state.last_response_at = datetime.utcnow()
