import logging
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.events.bus import EventBus
from app.ai.voice.events.event import Event
from app.ai.voice.events.event_types import EventType
from app.ai.voice.behavior.signals import BehavioralSignals
from app.ai.voice.behavior.hesitation_detector import HesitationDetector
from app.ai.voice.behavior.verbosity_analyzer import VerbosityAnalyzer
from app.ai.voice.behavior.topic_drift_detector import TopicDriftDetector
from app.ai.voice.behavior.confidence_tracker import ConfidenceTracker
from app.ai.voice.behavior.pressure_engine import PressureEngine
from app.ai.voice.behavior.metrics import RealtimeMetrics

logger = logging.getLogger("behavior_analyzer")

class BehavioralAnalyzer:
    def __init__(self, state: InterviewState, event_bus: EventBus):
        self.state = state
        self.event_bus = event_bus

        # Initialize detectors
        self.hesitation_detector = HesitationDetector()
        self.verbosity_analyzer = VerbosityAnalyzer()
        self.topic_drift_detector = TopicDriftDetector()
        self.confidence_tracker = ConfidenceTracker()
        self.pressure_engine = PressureEngine()
        self.metrics = RealtimeMetrics()

    async def on_transcript_received(self, event: Event) -> None:
        """
        Subscribed to EventType.TRANSCRIPT_RECEIVED. Runs all behavioral detectors,
        updates state, and emits secondary behavior events through the EventBus.
        """
        transcript = event.payload.get("text", "")
        response_time_ms = event.metadata.get("response_time_ms", 0.0)

        # 1. Analyze Hesitation
        hesitation = self.hesitation_detector.detect(transcript, response_time_ms)
        
        # 2. Analyze Verbosity
        verbosity = self.verbosity_analyzer.analyze(transcript)
        
        # 3. Analyze Topic Drift (Question vs Answer)
        current_question = self.state.conversation.current_question_text or ""
        drift = self.topic_drift_detector.detect(current_question, transcript)

        # 4. Update rolling metrics
        self.metrics.add_turn_metrics(hesitation, verbosity, drift)

        # 5. Update Candidate State Confidence Score
        old_confidence = self.state.candidate.confidence_score
        new_confidence = self.confidence_tracker.update_confidence(
            old_confidence, hesitation, verbosity
        )
        self.state.candidate.confidence_score = new_confidence

        # Synchronize candidate metrics to state
        self.state.candidate.hesitation_count = int(self.metrics.avg_hesitation / 15)
        self.state.candidate.verbosity_score = verbosity

        # 6. Run Pressure Engine
        old_pressure = self.state.pressure_level
        new_pressure = self.pressure_engine.adjust_pressure(new_confidence, hesitation)
        self.state.pressure_level = new_pressure

        # 7. Create/Update signals on InterviewState
        signals = BehavioralSignals(
            hesitation_score=hesitation,
            confidence_score=new_confidence,
            verbosity_score=verbosity,
            topic_drift_score=drift,
            response_pacing_score=self.metrics.avg_response_pacing,
            clarity_signal=100.0 - drift,
            pressure_signal=50.0 if new_pressure == "NORMAL" else (20.0 if new_pressure == "LOW" else 80.0)
        )
        self.state.behavioral_signals = signals

        # 8. Emit secondary events on threshold triggers
        await self._emit_behavioral_events(
            hesitation, old_confidence, new_confidence, drift, verbosity, old_pressure, new_pressure, event.session_id
        )

    async def _emit_behavioral_events(
        self,
        hesitation: float,
        old_confidence: float,
        new_confidence: float,
        drift: float,
        verbosity: float,
        old_pressure: str,
        new_pressure: str,
        session_id: str
    ) -> None:
        # Emit Hesitation
        if hesitation > 40.0:
            logger.info("behavior_analyzer | emitting HESITATION_DETECTED")
            await self.event_bus.emit(
                Event(
                    type=EventType.HESITATION_DETECTED,
                    session_id=session_id,
                    payload={"hesitation_score": hesitation}
                )
            )

        # Emit Confidence Dropped
        if old_confidence >= 40.0 and new_confidence < 40.0:
            logger.info("behavior_analyzer | emitting CONFIDENCE_DROPPED")
            await self.event_bus.emit(
                Event(
                    type=EventType.CONFIDENCE_DROPPED,
                    session_id=session_id,
                    payload={"confidence_score": new_confidence}
                )
            )

        # Emit Topic Drift
        if drift > 65.0:
            logger.info("behavior_analyzer | emitting TOPIC_DRIFT_DETECTED")
            await self.event_bus.emit(
                Event(
                    type=EventType.TOPIC_DRIFT_DETECTED,
                    session_id=session_id,
                    payload={"topic_drift_score": drift}
                )
            )

        # Emit Rambling (extreme verbosity)
        if verbosity > 75.0:
            logger.info("behavior_analyzer | emitting RAMBLING_DETECTED")
            await self.event_bus.emit(
                Event(
                    type=EventType.RAMBLING_DETECTED,
                    session_id=session_id,
                    payload={"verbosity_score": verbosity}
                )
            )

        # Emit Pressure Change
        if old_pressure != new_pressure:
            logger.info("behavior_analyzer | emitting PRESSURE_LEVEL_CHANGED: %s -> %s", old_pressure, new_pressure)
            await self.event_bus.emit(
                Event(
                    type=EventType.PRESSURE_LEVEL_CHANGED,
                    session_id=session_id,
                    payload={"old_pressure": old_pressure, "new_pressure": new_pressure}
                )
            )
