import asyncio
import logging
import time
import uuid
import httpx
from datetime import datetime
from livekit import rtc

from app.core.config import get_settings
from app.ai.voice.state.conversation_state import ConversationState
from app.ai.voice.state.candidate_state import CandidateState
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.conversation.memory import ConversationMemory, ConversationMessage
from app.ai.voice.conversation.manager import ConversationManager
from app.ai.voice.policies.interruption_policy import InterruptionPolicy
from app.ai.voice.policies.followup_policy import FollowupPolicy
from app.ai.voice.policies.difficulty_policy import DifficultyPolicy
from app.ai.voice.policies.response_policy import ResponsePolicy
from app.ai.voice.policies.turn_policy import TurnPolicy
from app.ai.voice.audio.vad import VoiceActivityDetector, VADResult
from app.ai.voice.audio.recorder import AudioRecorder
from app.ai.voice.audio.stt_service import STTService
from app.ai.voice.audio.tts_service import TTSService
from app.ai.voice.audio.audio_streamer import AudioStreamer
from app.ai.voice.audio.livekit_transport import LiveKitTransport
from app.ai.voice.llm import (
    PromptManager,
    SystemPromptBuilder,
    InterviewPromptBuilder,
    FollowupPromptBuilder,
    ClarificationPromptBuilder,
    ResponseGenerator,
    ResponseParser,
    SpeakerFormatter,
    ResponseFormatter,
    Interviewer,
)
from app.ai.voice.events import EventType, Event, EventBus
from app.ai.voice.events.chat_events import emit_chat_message
from app.ai.voice.events.handlers import (
    ConversationHandler,
    PolicyHandler,
    LoggingHandler,
    MetricsHandler,
)
from app.ai.voice.events.subscribers import (
    TranscriptSubscriber,
    DecisionSubscriber,
    AudioSubscriber,
)
from app.ai.voice.behavior import BehavioralAnalyzer
from app.ai.voice.realtime import (
    LatencyTracker,
    ResponseCache,
    ResponsePrefetcher,
    TurnPredictor,
    TranscriptStreamProcessor,
    SpeculativeEngine,
    TimingController,
    InterruptionCoordinator,
)
from app.ai.voice.memory import MemoryPipeline
from app.ai.voice.evaluation import (
    RefactoredEvaluationPipeline,
    EvaluationLogger,
)
from app.ai.voice.simulation import PersonalityEngine
from app.ai.voice.conversation import FactRegistry, FactExtractor
from app.ai.voice.policies import FactGroundingPolicy, DomainPolicy, DomainContext


logger = logging.getLogger("voice_agent")

active_agents: dict[str, "VoiceAgent"] = {}

class VoiceAgent:
    def __init__(
        self,
        room_name: str,
        state: InterviewState,
        conversation_manager: ConversationManager,
        interviewer: Interviewer,
        turn_policy: TurnPolicy,
        difficulty_policy: DifficultyPolicy,
        response_policy: ResponsePolicy,
        vad: VoiceActivityDetector,
        recorder: AudioRecorder,
        stt_service: STTService,
        tts_service: TTSService,
        audio_streamer: AudioStreamer,
        transport: LiveKitTransport,
        event_bus: EventBus,
        latency_tracker: LatencyTracker,
        speculative_engine: SpeculativeEngine,
        memory_pipeline: MemoryPipeline | None = None,
        evaluation_pipeline: RefactoredEvaluationPipeline | None = None,
        personality_engine: PersonalityEngine | None = None,
    ):
        """
        VoiceAgent coordinates live session state, events, and interview flow.
        Behavioral rules and conversational decisions are delegated to TurnPolicy and response subsystems.
        """
        self.room_name = room_name
        self.state = state
        self.conversation_manager = conversation_manager
        self.interviewer = interviewer
        self.turn_policy = turn_policy
        self.difficulty_policy = difficulty_policy
        self.response_policy = response_policy
        self.vad = vad
        self.recorder = recorder
        self.stt_service = stt_service
        self.tts_service = tts_service
        self.audio_streamer = audio_streamer
        self.transport = transport
        self.event_bus = event_bus
        self.latency_tracker = latency_tracker
        self.speculative_engine = speculative_engine

        # ── Intelligence layers (Steps 8-10) ────────────────────────────────
        self.memory_pipeline: MemoryPipeline | None = memory_pipeline
        self.evaluation_pipeline: EvaluationPipeline | None = evaluation_pipeline
        self.personality_engine: PersonalityEngine | None = personality_engine

        # Attach latency tracker to state for handler access
        self.state.latency_tracker = latency_tracker

        self.settings = get_settings()

        # ── Runtime state flags ─────────────────────────────────────────────
        self.is_speaking = False
        self.is_running = True
        self.is_processing = False

        # ── DB tracking ─────────────────────────────────────────────────────
        self.question_sequence: int = 0
        self.current_question_id: uuid.UUID | None = None
        self.question_asked_at: float | None = None

    @property
    def interview_mode(self) -> str:
        return self.state.mode

    @interview_mode.setter
    def interview_mode(self, val: str):
        self.state.mode = val
        self.state.panel_mode = (val == "PANEL_AI")

    @property
    def session_difficulty(self) -> str:
        return self.state.difficulty

    @session_difficulty.setter
    def session_difficulty(self, val: str):
        self.state.difficulty = val

    def _should_continue_speaking(self) -> bool:
        return self.is_speaking and self.is_running

    # ── DB Helpers ──────────────────────────────────────────────────────────

    async def _load_session_info(self) -> None:
        try:
            from app.db.session import SessionLocal
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            from app.db.models.interview_session import InterviewSession

            async with SessionLocal() as db:
                result = await db.execute(
                    select(InterviewSession)
                    .options(
                        selectinload(InterviewSession.topic),
                        selectinload(InterviewSession.user)
                    )
                    .where(
                        InterviewSession.id == uuid.UUID(self.room_name)
                    )
                )
                session = result.scalar_one_or_none()
                if session:
                    self.session_difficulty = session.difficulty or "MEDIUM"
                    self.interview_mode = session.interview_mode or "ONE_ON_ONE_AI"
                    self.state.adaptive_enabled = session.adaptive or False
                    self.state.target_duration_minutes = session.duration_minutes or 15
                    self.state.interview_category = session.interview_category or "GENERAL"
                    self.state.minutes_remaining = float(self.state.target_duration_minutes)
                    
                    if session.personality_config and "journey_context" in session.personality_config:
                        journey_context = session.personality_config["journey_context"]
                        self.state.conversation.current_topic = journey_context.get("round_name") or "Technical Screen"
                    elif session.topic and session.topic.name:
                        self.state.conversation.current_topic = session.topic.name
                    else:
                        self.state.conversation.current_topic = str(session.topic_id)

                    if session.user and session.user.display_name:
                        self.state.candidate.candidate_name = session.user.display_name.split()[0]
                    self.state.candidate.candidate_id = str(session.user_id)

                    # ── Interview plan (topic coverage) ─────────────────────
                    from app.ai.voice.planning.plan import InterviewPlan

                    if session.interview_plan:
                        self.state.conversation.plan = InterviewPlan.from_dict(session.interview_plan)
                    else:
                        plan = None
                        if session.personality_config and "journey_context" in session.personality_config:
                            try:
                                from app.ai.voice.planning.plan import PlanTopic, TopicStatus
                                journey_context = session.personality_config["journey_context"]
                                round_focus = journey_context.get("round_focus", {})
                                focus = round_focus.get("focus", {}) if isinstance(round_focus, dict) else {}
                                areas = focus.get("areas", []) if isinstance(focus, dict) else []
                                if not areas and isinstance(round_focus, dict):
                                    areas = round_focus.get("areas", [])
                                
                                if areas:
                                    topics = []
                                    for idx, area in enumerate(areas):
                                        topics.append(PlanTopic(
                                            topic_id=f"journey-topic-{idx}-{uuid.uuid4().hex[:6]}",
                                            label=area,
                                            target_depth=2,
                                            time_budget_turns=4,
                                            status=TopicStatus.NOT_STARTED
                                        ))
                                    if topics:
                                        topics[0].status = TopicStatus.IN_PROGRESS
                                    
                                    plan = InterviewPlan(topics=topics, max_angles_per_topic=1)
                                    self.state.conversation.plan = plan
                                    session.interview_plan = plan.to_dict()
                                    await db.commit()
                                    logger.info("Generated InterviewPlan from journey focus areas: %s", areas)
                            except Exception as exc:
                                logger.error("Failed to construct plan from journey context: %s", exc)

                        if plan is None:
                            try:
                                from app.ai.voice.planning.plan_generator import InterviewPlanGenerator
                                plan = await InterviewPlanGenerator().generate(
                                    topic_name=self.state.conversation.current_topic or "General",
                                    interview_category=self.state.interview_category,
                                    difficulty=self.session_difficulty,
                                    duration_minutes=self.state.target_duration_minutes,
                                )
                                self.state.conversation.plan = plan
                                session.interview_plan = plan.to_dict()
                                await db.commit()
                            except Exception as exc:
                                logger.error("Failed to generate interview plan (continuing without one): %s", exc)

                    if self.state.conversation.plan:
                        import json
                        plan_details = [
                            {
                                "topic_id": t.topic_id,
                                "label": t.label,
                                "target_depth": t.target_depth,
                                "status": t.status.value if hasattr(t.status, "value") else str(t.status)
                            }
                            for t in self.state.conversation.plan.topics
                        ]
                        logger.info("INTERVIEW_PLAN_AT_START: %s", json.dumps(plan_details))

                    logger.info(
                        "Loaded session info for room %s: diff=%s, mode=%s, adaptive=%s, topic=%s, candidate=%s",
                        self.room_name,
                        self.session_difficulty,
                        self.interview_mode,
                        self.state.adaptive_enabled,
                        self.state.conversation.current_topic,
                        getattr(self.state.candidate, "candidate_name", "Unknown")
                    )
        except Exception as exc:
            logger.error("Failed to load session info: %s", exc)

    async def _save_question_to_db(self, question_text: str) -> uuid.UUID | None:
        try:
            from app.db.session import SessionLocal
            from app.db.models.question_instance import QuestionInstance

            question_id = uuid.uuid4()
            self.question_sequence += 1

            async with SessionLocal() as db:
                q = QuestionInstance(
                    id=question_id,
                    session_id=uuid.UUID(self.room_name),
                    content=question_text,
                    difficulty=self.session_difficulty,
                    sequence_order=self.question_sequence,
                )
                db.add(q)
                await db.commit()

            logger.info(
                "Saved question #%d to DB: %s…",
                self.question_sequence,
                question_text[:80],
            )
            return question_id
        except Exception as exc:
            logger.error("Failed to save question to DB: %s", exc)
            return None

    async def _save_response_to_db(
        self,
        question_id: uuid.UUID,
        answer_text: str,
        response_time_ms: int,
    ) -> None:
        try:
            from app.db.session import SessionLocal
            from app.db.models.response_instance import ResponseInstance

            async with SessionLocal() as db:
                r = ResponseInstance(
                    id=uuid.uuid4(),
                    question_id=question_id,
                    session_id=uuid.UUID(self.room_name),
                    answer_text=answer_text,
                    response_time_ms=max(0, response_time_ms),
                    thinking_time_ms=0,
                    answer_length=len(answer_text.split()),
                    audio_processing_status="SKIPPED",
                )
                db.add(r)
                await db.commit()

            logger.info(
                "Saved response for question %s (rt=%dms): %s…",
                question_id,
                response_time_ms,
                answer_text[:80],
            )
        except Exception as exc:
            logger.error("Failed to save response to DB: %s", exc)

    # ── Transcript helper ───────────────────────────────────────────────────

    # ── Lifecycle ───────────────────────────────────────────────────────────

    async def start(self) -> None:
        await self._load_session_info()

        # ── Step 10: Activate personality based on session mode ──────────────
        if self.personality_engine:
            mode = self.state.mode or "ONE_ON_ONE_AI"
            persona_map = {
                "PANEL_AI": "google_design_interviewer",
                "ONE_ON_ONE_AI": "standard_interviewer",
            }
            persona = persona_map.get(mode, "standard_interviewer")
            try:
                await self.personality_engine.select_persona(persona)
                logger.info("[personality] Activated persona '%s' for mode '%s'", persona, mode)
            except Exception as exc:
                logger.warning("[personality] Could not select persona '%s': %s", persona, exc)

        # ── Step 8: Retrieve historical candidate memory ─────────────────────
        memory_context = ""
        if self.memory_pipeline:
            try:
                candidate_id = self.state.candidate.candidate_id if hasattr(self.state.candidate, "candidate_id") else None
                if candidate_id:
                    memory_context = await self.memory_pipeline.retrieve_context_for_prompt(
                        candidate_id=candidate_id,
                        query_text="interview session start",
                        state=self.state,
                    )
                    if memory_context:
                        logger.info("[memory] Retrieved %d chars of historical context", len(memory_context))
                        self.state.memory_context = memory_context
            except Exception as exc:
                logger.warning("[memory] Context retrieval failed (non-fatal): %s", exc)

        agent_token = self.transport.generate_token("AI_Interviewer")

        self.transport.register_handlers(
            on_track_subscribed=self.on_track_subscribed,
            on_participant_disconnected=self.on_participant_disconnected,
            on_data_received=self.handle_data_message,
        )

        logger.info("Connecting voice agent to room: %s", self.room_name)
        try:
            await self.transport.connect(agent_token)
        except Exception as exc:
            logger.error("Failed to connect voice agent to LiveKit: %s", exc)
            self.is_running = False
            active_agents.pop(self.room_name, None)
            return

        try:
            await self.transport.publish_audio()
            logger.info("Published agent voice track successfully.")
        except Exception as exc:
            logger.error("Failed to publish voice track: %s", exc)

        # Emit TOPIC_CHANGED event initially to sync state
        await self.event_bus.emit(
            Event(
                type=EventType.TOPIC_CHANGED,
                session_id=self.room_name,
                payload={"topic": self.state.conversation.current_topic or "General"}
            )
        )

        await asyncio.sleep(1.0)

        # Emit the RESPONSE_GENERATED event to trigger the initial greeting event pipeline
        candidate_name = getattr(self.state.candidate, "candidate_name", None)
        topic = self.state.conversation.current_topic or "General"
        if candidate_name:
            greeting_text = (
                f"Hello {candidate_name}! Welcome to your mock interview session. I am your AI interviewer today. "
                f"Our interview will focus on {topic}. Let's begin. Could you please start by introducing yourself "
                "and giving a brief summary of your professional background?"
            )
        else:
            greeting_text = (
                "Hello! Welcome to your mock interview session. I am your AI interviewer today. "
                f"Our interview will focus on {topic}. Let's begin. Could you please start by introducing yourself "
                "and giving a brief summary of your professional background?"
            )
        await self.event_bus.emit(
            Event(
                type=EventType.RESPONSE_GENERATED,
                session_id=self.room_name,
                payload={
                    "raw_text": greeting_text,
                    "clean_text": greeting_text,
                    "speaker_name": "Interviewer",
                    "voice_name": "en-US-AriaNeural"
                }
            )
        )

    def on_track_subscribed(self, track, publication, participant):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info("Subscribed to user audio track: %s", track.sid)
            asyncio.create_task(self.handle_user_audio(track))

    def on_participant_disconnected(self, participant):
        human_participants = [
            p
            for p in self.transport.get_remote_participants().values()
            if p.identity != "AI_Interviewer"
        ]
        if not human_participants:
            logger.info(
                "All human participants left. Stopping voice agent for room %s.",
                self.room_name,
            )
            asyncio.create_task(self.stop())

    async def stop(self) -> None:
        if not self.is_running:
            return
        logger.info("Stopping voice agent for room: %s", self.room_name)
        self.is_running = False
        self.is_speaking = False
        self.is_processing = False
        self.state.completed = True
        
        # Emit INTERVIEW_COMPLETED event for orchestrators
        await self.event_bus.emit(
            Event(
                type=EventType.INTERVIEW_COMPLETED,
                session_id=self.room_name,
                payload={
                    "turn_count": self.state.conversation.turn_count,
                    "question_count": self.question_sequence,
                }
            )
        )
        
        active_agents.pop(self.room_name, None)

        # ── Step 8: Persist session memory ───────────────────────────────────
        if self.memory_pipeline:
            try:
                candidate_id = self.state.candidate.candidate_id if hasattr(self.state.candidate, "candidate_id") else None
                session_id_str = self.room_name
                messages = self.conversation_manager.memory.messages if self.conversation_manager else []
                if candidate_id and messages:
                    from app.db.session import SessionLocal
                    async with SessionLocal() as db:
                        persisted = await self.memory_pipeline.process_session_end(
                            candidate_id=candidate_id,
                            session_id=uuid.UUID(session_id_str),
                            messages=messages,
                            db=db,
                        )
                    logger.info("[memory] Persisted %d memories for candidate %s", persisted, candidate_id)
            except Exception as exc:
                logger.warning("[memory] Session end processing failed (non-fatal): %s", exc)

        # ── Step 9: Run post-session evaluation ──────────────────────────────
        if self.evaluation_pipeline:
            try:
                candidate_id = self.state.candidate.candidate_id if hasattr(self.state.candidate, "candidate_id") else None
                messages = self.conversation_manager.memory.messages if self.conversation_manager else []
                if candidate_id and messages:
                    behavioral = {
                        "hesitation_count": getattr(self.state.candidate, "hesitation_count", 0),
                        "avg_response_time_ms": getattr(self.state.candidate, "avg_response_time_ms", 0),
                        "topic_drift_rate": getattr(self.state.candidate, "topic_drift_rate", 0.0),
                    }
                    report = await self.evaluation_pipeline.execute_evaluation(
                        session_id=uuid.UUID(self.room_name),
                        candidate_id=candidate_id,
                        messages=messages,
                        behavioral_metrics=behavioral,
                    )
                    logger.info(
                        "[evaluation] Session %s scored. CI: %s | Recs: %d",
                        self.room_name, report.confidence_interval, len(report.recommendations)
                    )
            except Exception as exc:
                logger.warning("[evaluation] Post-session evaluation failed (non-fatal): %s", exc)

        try:
            await self.transport.disconnect()
        except Exception as exc:
            logger.error("Error disconnecting room: %s", exc)

    # ── Speaking ────────────────────────────────────────────────────────────

    async def speak(
        self,
        text: str,
        speaker_name: str = None,
        voice_name: str = None,
        raw_text: str = None,
    ) -> None:
        if not self.is_running:
            return

        self.is_processing = False
        self.is_speaking = True

        # ── Step 10: Inject personality verbal fillers ───────────────────────
        if self.personality_engine:
            try:
                text = self.personality_engine.format_interviewer_speech(text)
            except Exception:
                pass  # Non-fatal: use original text

        if not speaker_name or not voice_name or not raw_text:
            speaker_name, clean_text, voice_name = self.interviewer.speaker_formatter.format_speaker(
                text, self.question_sequence, self.state.panel_mode
            )
            raw_text = text
        else:
            clean_text = text

        logger.info("[%s] speaking: %s", speaker_name, clean_text[:120])

        # Publish chat message to data channel
        content_type = self._detect_content_type(clean_text)
        language = self._detect_language(clean_text)
        asyncio.create_task(
            emit_chat_message(self.transport, {
                "role": "interviewer",
                "content": clean_text,
                "content_type": content_type,
                "language": language,
            })
        )

        question_id = await self._save_question_to_db(clean_text)
        if question_id:
            self.current_question_id = question_id
            self.state.conversation.current_question_id = str(question_id)
            
            # Emit QUESTION_ASKED event for orchestrators
            await self.event_bus.emit(
                Event(
                    type=EventType.QUESTION_ASKED,
                    session_id=self.room_name,
                    payload={
                        "question": clean_text,
                        "question_id": str(question_id),
                        "sequence": self.question_sequence,
                        "speaker": speaker_name,
                    }
                )
            )

        # TTS Synthesis Event Track
        self.latency_tracker.track_stage_start("tts")
        tts_start = time.perf_counter()
        await self.event_bus.emit(
            Event(
                type=EventType.TTS_STARTED,
                session_id=self.room_name,
                payload={"text": clean_text, "speaker": speaker_name, "voice": voice_name}
            )
        )

        # Clean text from any markdown code blocks or triple-backtick segments for clean speech synthesis
        import re
        spoken_text = re.sub(r"```[\s\S]*?```", "", clean_text)
        spoken_text = re.sub(r"\s+", " ", spoken_text).strip()
        if not spoken_text:
            spoken_text = "Please take a look at the challenge on your screen."

        mp3_bytes = await self.tts_service.synthesize(spoken_text, voice_name)
        self.latency_tracker.track_stage_end("tts")
        tts_latency_ms = int((time.perf_counter() - tts_start) * 1000)

        if not mp3_bytes:
            logger.error("TTS returned no audio data.")
            self.is_speaking = False
            await self.event_bus.emit(
                Event(
                    type=EventType.TTS_COMPLETED,
                    session_id=self.room_name,
                    payload={"status": "failed"},
                    metadata={"tts_latency_ms": tts_latency_ms}
                )
            )
            return

        await self.event_bus.emit(
            Event(
                type=EventType.TTS_COMPLETED,
                session_id=self.room_name,
                payload={"status": "success"},
                metadata={"tts_latency_ms": tts_latency_ms}
            )
        )

        # Audio streaming playback events
        self.latency_tracker.track_stage_end("total")
        self.latency_tracker.track_stage_start("playback")
        stream_start = time.perf_counter()
        await self.event_bus.emit(
            Event(
                type=EventType.AUDIO_STREAM_STARTED,
                session_id=self.room_name,
                payload={"speaker": speaker_name}
            )
        )

        await self.audio_streamer.stream_mp3(mp3_bytes, stop_check_func=self._should_continue_speaking)
        self.latency_tracker.track_stage_end("playback")

        stream_latency_ms = int((time.perf_counter() - stream_start) * 1000)
        await self.event_bus.emit(
            Event(
                type=EventType.AUDIO_STREAM_COMPLETED,
                session_id=self.room_name,
                payload={"speaker": speaker_name},
                metadata={"stream_duration_ms": stream_latency_ms}
            )
        )

        self.is_speaking = False
        self.question_asked_at = time.time()

        # Emit QUESTION_ASKED
        await self.event_bus.emit(
            Event(
                type=EventType.QUESTION_ASKED,
                session_id=self.room_name,
                payload={"text": clean_text, "speaker": speaker_name}
            )
        )

    def _detect_content_type(self, text: str) -> str:
        if "```" in text:
            return "code"
        lower = text.lower()
        if any(k in lower for k in ["design a system", "design the", "draw", "architecture"]):
            return "system_design"
        if any(k in lower for k in ["given an array", "return the", "time complexity", "space complexity", "input:", "output:"]):
            return "dsa"
        return "text"

    def _detect_language(self, text: str) -> str | None:
        import re
        m = re.search(r"```(\w+)", text)
        return m.group(1) if m else None

    async def handle_data_message(self, data: bytes, participant, kind) -> None:
        import json
        try:
            msg = json.loads(data.decode("utf-8"))
        except Exception:
            return

        if msg.get("type") != "CANDIDATE_MESSAGE":
            return

        content = msg.get("content", "").strip()
        image_b64 = msg.get("image_b64")

        candidate_answer = content
        if image_b64:
            candidate_answer += "\n\n[Candidate also submitted a system design diagram.]"

        if self.current_question_id and candidate_answer:
            response_time_ms = int((time.time() - (self.question_asked_at or time.time())) * 1000)
            await self._save_response_to_db(self.current_question_id, candidate_answer, response_time_ms)

        await self.event_bus.emit(
            Event(
                type=EventType.TRANSCRIPT_RECEIVED,
                session_id=self.room_name,
                payload={
                    "text": candidate_answer,
                    "transcript": candidate_answer,
                    "turn_number": self.state.conversation.turn_count,
                },
                metadata={
                    "response_time_ms": 0,
                    "stt_latency_ms": 0,
                }
            )
        )

    # ── Audio capture / VAD ─────────────────────────────────────────────────

    async def handle_user_audio(self, track) -> None:
        try:
            audio_stream = rtc.AudioStream(track)
            
            async for event in audio_stream:
                if not self.is_running:
                    break

                if self.is_speaking or self.is_processing:
                    continue

                frame = event.frame
                vad_result = self.vad.process_frame(
                    frame.data,
                    sample_rate=frame.sample_rate,
                    num_channels=frame.num_channels,
                )

                if vad_result.rms > 50.0:
                    logger.debug("User mic RMS: %.1f (threshold: %.1f)", vad_result.rms, self.vad.threshold)

                if vad_result.speech_started:
                    logger.info("speech_started | User speech onset detected (RMS: %.1f)", vad_result.rms)
                    self.recorder.start(sample_rate=frame.sample_rate, num_channels=frame.num_channels)
                    
                    asyncio.create_task(
                        self.event_bus.emit(
                            Event(
                                type=EventType.USER_STARTED_SPEAKING,
                                session_id=self.room_name,
                            )
                        )
                    )

                if vad_result.is_speaking:
                    self.recorder.append(frame.data)

                if vad_result.speech_ended:
                    logger.info("speech_ended | End-of-utterance silence detected. Processing response...")
                    wav_path = self.recorder.export_wav()
                    self.recorder.reset()
                    
                    asyncio.create_task(
                        self.event_bus.emit(
                            Event(
                                type=EventType.USER_STOPPED_SPEAKING,
                                session_id=self.room_name,
                            )
                        )
                    )
                    
                    self.is_processing = True
                    asyncio.create_task(
                        self.process_user_response(
                            wav_path, frame.sample_rate, frame.num_channels
                        )
                    )
        except Exception as exc:
            logger.exception("Exception in handle_user_audio: %s", exc)

    # ── STT → LLM → TTS pipeline ────────────────────────────────────────────

    async def process_user_response(
        self, wav_path: str, sample_rate: int, num_channels: int
    ) -> None:
        if not self.is_running:
            self.is_processing = False
            return

        try:
            await self._process_user_response_inner(wav_path)
        except Exception as exc:
            logger.exception("Unhandled exception in process_user_response: %s", exc)
            # Release lock in case of errors before event emit
            self.is_processing = False

    async def _process_user_response_inner(self, wav_path: str) -> None:
        self.latency_tracker.track_stage_start("total")
        token = self.speculative_engine.get_new_cancellation_token()
        active_topic = self.state.conversation.current_topic or "General"
        self.speculative_engine.prepare_followup(self.room_name, token, active_topic)

        response_time_ms = (
            int((time.time() - self.question_asked_at) * 1000)
            if self.question_asked_at is not None
            else 0
        )

        self.latency_tracker.track_stage_start("stt")
        stt_start = time.perf_counter()
        transcription = await self.stt_service.transcribe(wav_path)
        self.latency_tracker.track_stage_end("stt")
        stt_latency_ms = int((time.perf_counter() - stt_start) * 1000)

        if not transcription:
            logger.info("Empty transcription — skipping LLM turn.")
            self.is_processing = False
            self.speculative_engine.cancel_pending()
            return

        if self.current_question_id:
            await self._save_response_to_db(
                self.current_question_id,
                transcription,
                response_time_ms,
            )

        # Emit TRANSCRIPT_RECEIVED event to kick off handlers/subscribers
        await self.event_bus.emit(
            Event(
                type=EventType.TRANSCRIPT_RECEIVED,
                session_id=self.room_name,
                payload={
                    "text": transcription,
                    "transcript": transcription,  # Add for orchestrators
                    "turn_number": self.state.conversation.turn_count,
                },
                metadata={
                    "response_time_ms": response_time_ms,
                    "stt_latency_ms": stt_latency_ms,
                }
            )
        )

        # Publish user chat message to data channel (for voice transcription)
        asyncio.create_task(
            emit_chat_message(self.transport, {
                "role": "candidate",
                "content": transcription,
                "content_type": "text",
            })
        )

        # ── Step 10: Adapt personality based on candidate turn ───────────────
        if self.personality_engine:
            try:
                candidate = self.state.candidate
                topic_drift = getattr(candidate, "topic_drift_rate", 0.0)
                hesitation = min(1.0, getattr(candidate, "hesitation_count", 0) / 10.0)
                verbosity = min(1.0, len(transcription.split()) / 200.0)
                adapted_params, prompt_instruction = self.personality_engine.process_user_turn(
                    topic_drift=topic_drift,
                    hesitation=hesitation,
                    verbosity=verbosity,
                )
                # Store for prompt augmentation
                self.state.personality_instruction = prompt_instruction
                thinking_pause = self.personality_engine.get_thinking_delay()
                if thinking_pause > 0:
                    await asyncio.sleep(thinking_pause)
            except Exception as exc:
                logger.debug("[personality] Turn adaptation failed (non-fatal): %s", exc)

# ── Module-level launcher ───────────────────────────────────────────────────

def launch_voice_agent(room_name: str) -> None:
    """
    Spawn a background VoiceAgent for the given room if one is not already running.
    """
    if room_name not in active_agents:
        settings = get_settings()
        
        conversation_state = ConversationState(
            messages=[],
            current_question_id=None,
            current_question_text=None,
            current_topic=None,
            current_speaker="Interviewer",
            turn_count=0,
            topic_followup_count=0,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        candidate_state = CandidateState()
        interview_state = InterviewState(
            session_id=room_name,
            conversation=conversation_state,
            candidate=candidate_state,
            mode="ONE_ON_ONE_AI",
            difficulty="MEDIUM",
            adaptive_enabled=False,
            panel_mode=False,
            completed=False,
        )

        memory = ConversationMemory(max_messages=20)
        conversation_manager = ConversationManager(state=interview_state, memory=memory)
        
        # Realtime components
        latency_tracker = LatencyTracker()
        response_cache = ResponseCache()

        # New prompt/LLM infra
        prompt_manager = PromptManager(response_cache=response_cache)
        system_prompt_builder = SystemPromptBuilder(prompt_manager)
        interview_prompt_builder = InterviewPromptBuilder(prompt_manager)
        followup_prompt_builder = FollowupPromptBuilder(prompt_manager)
        clarification_prompt_builder = ClarificationPromptBuilder(prompt_manager)
        response_generator = ResponseGenerator()
        response_parser = ResponseParser()
        speaker_formatter = SpeakerFormatter()
        response_formatter = ResponseFormatter()

        interruption_policy = InterruptionPolicy()
        followup_policy = FollowupPolicy()
        difficulty_policy = DifficultyPolicy()
        response_policy = ResponsePolicy()

        # ── Fact Grounding System ────────────────────────────────────────────
        fact_registry = FactRegistry()
        fact_extractor = FactExtractor(fact_registry)
        conversation_manager.set_fact_extractor(fact_extractor)

        # ── Domain Policy ─────────────────────────────────────────────────────
        domain_policy = DomainPolicy()
        domain_context = domain_policy.create_context(
            topic=interview_state.conversation.current_topic or "General",
        )

        # ── Policies ─────────────────────────────────────────────────────────
        fact_grounding_policy = FactGroundingPolicy(fact_registry)

        interviewer = Interviewer(
            prompt_manager=prompt_manager,
            system_prompt_builder=system_prompt_builder,
            interview_prompt_builder=interview_prompt_builder,
            followup_prompt_builder=followup_prompt_builder,
            clarification_prompt_builder=clarification_prompt_builder,
            response_generator=response_generator,
            response_parser=response_parser,
            speaker_formatter=speaker_formatter,
            response_formatter=response_formatter,
            response_policy=response_policy,
        )
        interviewer.set_fact_grounding_policy(fact_grounding_policy)
        interviewer.set_domain_context(domain_context)

        turn_policy = TurnPolicy(
            interruption_policy=interruption_policy,
            followup_policy=followup_policy,
            difficulty_policy=difficulty_policy,
            response_policy=response_policy,
        )

        transport = LiveKitTransport(
            room_name=room_name,
            livekit_url=settings.livekit_url,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        )
        vad = VoiceActivityDetector(
            threshold=200.0,
            silence_timeout=0.8,
            sample_width=2,
        )
        recorder = AudioRecorder(room_name=room_name)
        stt_service = STTService(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            model=settings.groq_whisper_model,
        )
        tts_service = TTSService()
        audio_streamer = AudioStreamer(audio_source=transport.audio_source)

        # ── Event-Driven Subsystem Wiring ────────────────────────────────────
        event_bus = EventBus()

        response_prefetcher = ResponsePrefetcher(prompt_manager)
        speculative_engine = SpeculativeEngine(
            event_bus=event_bus,
            response_cache=response_cache,
            response_prefetcher=response_prefetcher,
        )
        timing_controller = TimingController()

        conversation_handler = ConversationHandler(conversation_manager, transport)
        policy_handler = PolicyHandler(interview_state, turn_policy, difficulty_policy, event_bus)
        logging_handler = LoggingHandler()
        metrics_handler = MetricsHandler(interview_state)
        
        transcript_subscriber = TranscriptSubscriber()
        decision_subscriber = DecisionSubscriber(interview_state, interviewer, event_bus)
        audio_subscriber = AudioSubscriber(timing_controller=timing_controller)
        
        behavior_analyzer = BehavioralAnalyzer(interview_state, event_bus)

        # ── NEW: Initialize Orchestrators ─────────────────────────────────────
        from app.ai.orchestrators.integration import create_orchestrator_hub
        from app.ai.orchestrators.contracts.interview_contracts import (
            InterviewConfig,
            InterviewDomain,
        )
        
        # Determine domain from session (default to BACKEND)
        orchestrator_domain = InterviewDomain.BACKEND
        
        # Create orchestrator config
        orchestrator_config = InterviewConfig(
            domain=orchestrator_domain,
            target_duration_minutes=45,
            max_questions_per_round=5,
            max_followup_depth=3,
        )
        
        # Create and register orchestrator hub
        orchestrator_hub = create_orchestrator_hub(event_bus, orchestrator_config)
        orchestrator_hub.register_event_handlers()
        
        logger.info(
            f"Orchestrators initialized for room {room_name}: "
            f"domain={orchestrator_domain.value}"
        )

        # Wire Up Core Turn subscriptions
        event_bus.subscribe(EventType.TRANSCRIPT_RECEIVED, conversation_handler.on_transcript_received)
        event_bus.subscribe(EventType.TRANSCRIPT_RECEIVED, policy_handler.on_transcript_received)
        event_bus.subscribe(EventType.TRANSCRIPT_RECEIVED, transcript_subscriber.on_transcript_received)
        event_bus.subscribe(EventType.TRANSCRIPT_RECEIVED, behavior_analyzer.on_transcript_received)
        event_bus.subscribe(EventType.DECISION_CREATED, decision_subscriber.on_decision_created)
        event_bus.subscribe(EventType.RESPONSE_GENERATED, conversation_handler.on_response_generated)
        event_bus.subscribe(EventType.RESPONSE_GENERATED, audio_subscriber.on_response_generated)

        # Wire metrics and logger to track all events
        for event_type in EventType:
            event_bus.subscribe(event_type, logging_handler.handle_event)
            event_bus.subscribe(event_type, metrics_handler.handle_event)

        agent = VoiceAgent(
            room_name=room_name,
            state=interview_state,
            conversation_manager=conversation_manager,
            interviewer=interviewer,
            turn_policy=turn_policy,
            difficulty_policy=difficulty_policy,
            response_policy=response_policy,
            vad=vad,
            recorder=recorder,
            stt_service=stt_service,
            tts_service=tts_service,
            audio_streamer=audio_streamer,
            transport=transport,
            event_bus=event_bus,
            latency_tracker=latency_tracker,
            speculative_engine=speculative_engine,
            memory_pipeline=MemoryPipeline(),
            evaluation_pipeline=RefactoredEvaluationPipeline(
                domain=domain_context.primary_domain,
            ),
            personality_engine=PersonalityEngine(personas_dir="personas"),
        )

        # Attach orchestrator hub to agent
        agent.orchestrator_hub = orchestrator_hub
        
        logger.info(f"OrchestratorHub attached to VoiceAgent for room {room_name}")

        # Register agent reference to allow subscriber audio playbacks
        audio_subscriber.set_agent(agent)

        active_agents[room_name] = agent
        asyncio.create_task(agent.start())
        logger.info("Dispatched background voice agent for room %s.", room_name)
