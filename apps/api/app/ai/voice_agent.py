"""
VoiceAgent — real-time AI interviewer over LiveKit WebRTC.

Responsibilities:
  1. Join the LiveKit room as "AI_Interviewer"
  2. Stream synthesised speech (OpenAI TTS) back to the user
  3. Capture user audio via VAD (RMS threshold), transcribe with Groq Whisper,
     query NVIDIA NIM for a reply, then speak it
  4. Broadcast live transcript to the frontend via LiveKit Data Channel
  5. Persist every question and user response to the database so the
     existing evaluation pipeline can analyse the session without changes

Bug fixes applied in this revision
  - send_transcript() was sync and never awaited publish_data (coroutine was
    discarded) → now async, payload encoded to bytes, awaited correctly
  - No guard against concurrent process_user_response tasks → added
    self.is_processing flag; set inline before task creation, cleared before speak()
  - Silence threshold was 1.5 s → reduced to 0.8 s for snappier turn-taking
"""

import asyncio
import logging
import os
import uuid
import wave
import time
import httpx
import json
import numpy as np
import edge_tts
import miniaudio
from jose import jwt
from livekit import rtc
from app.core.config import get_settings

logger = logging.getLogger("voice_agent")

# Global dict: room_name → VoiceAgent instance
active_agents: dict[str, "VoiceAgent"] = {}


class VoiceAgent:
    def __init__(self, room_name: str):
        self.room_name = room_name
        self.room = rtc.Room()
        self.settings = get_settings()
        self.interview_mode = "ONE_ON_ONE_AI"

        self.conversation_history: list[dict] = [
            {
                "role": "system",
                "content": (
                    "You are a professional, friendly, and realistic job interviewer "
                    "conducting an interactive mock interview. Act like a human interviewer. "
                    "Ask one concise question or follow-up at a time. Do not output markdown, "
                    "lists, or bullets. Keep responses short and conversational "
                    "(1-2 sentences max), suitable for a voice call."
                ),
            }
        ]

        self.audio_source = rtc.AudioSource(sample_rate=24000, num_channels=1)
        self.audio_track = rtc.LocalAudioTrack.create_audio_track(
            "agent-voice", self.audio_source
        )

        # ── Runtime state flags ─────────────────────────────────────────────
        self.is_speaking = False
        self.is_running = True
        # Prevents a second process_user_response task firing while one is in
        # progress (transcribing / querying LLM).  Set to True *before* the
        # asyncio.create_task() call to close the race window.
        self.is_processing = False

        # ── DB tracking — persisted for evaluation pipeline ─────────────────
        self.question_sequence: int = 0
        self.current_question_id: uuid.UUID | None = None
        # Wall-clock time when the agent finished speaking (user's turn starts)
        self.question_asked_at: float | None = None
        # Loaded from DB on start; used to tag QuestionInstance.difficulty
        self.session_difficulty: str = "MEDIUM"

    # ── DB helpers ──────────────────────────────────────────────────────────

    async def _load_session_info(self) -> None:
        """Fetch session metadata (difficulty) from the database."""
        try:
            from app.db.session import SessionLocal
            from sqlalchemy import select
            from app.db.models.interview_session import InterviewSession

            async with SessionLocal() as db:
                result = await db.execute(
                    select(InterviewSession).where(
                        InterviewSession.id == uuid.UUID(self.room_name)
                    )
                )
                session = result.scalar_one_or_none()
                if session:
                    self.session_difficulty = session.difficulty or "MEDIUM"
                    self.interview_mode = session.interview_mode or "ONE_ON_ONE_AI"
                    logger.info(
                        "Loaded session info for room %s: diff=%s, mode=%s",
                        self.room_name,
                        self.session_difficulty,
                        self.interview_mode,
                    )
        except Exception as exc:
            logger.error("Failed to load session info: %s", exc)

    async def _save_question_to_db(self, question_text: str) -> uuid.UUID | None:
        """
        Persist the agent's spoken text as a QuestionInstance and return its UUID.
        This makes the question visible to the evaluation pipeline.
        """
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
        """
        Persist the user's transcribed answer as a ResponseInstance linked to the
        current QuestionInstance.  The evaluation pipeline will score this later.
        """
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

    # ── Transcript broadcast ────────────────────────────────────────────────

    async def send_transcript(self, speaker: str, text: str) -> None:
        """
        Broadcast {speaker, text} JSON to the frontend via LiveKit Data Channel.

        FIX: was a sync def that called publish_data() without await — the
        coroutine was created and immediately garbage-collected, so no data was
        ever sent.  Now async, payload is UTF-8 bytes, and publish_data is awaited.
        """
        if not self.is_running:
            return
        payload: bytes = json.dumps({"speaker": speaker, "text": text}).encode("utf-8")
        try:
            await self.room.local_participant.publish_data(payload)
            logger.info("Broadcasted transcript: [%s] → %s", speaker, text[:80])
        except Exception as exc:
            logger.error("Failed to publish transcript data packet: %s", exc)

    # ── Lifecycle ───────────────────────────────────────────────────────────

    async def start(self) -> None:
        # 1. Load session metadata (difficulty and mode) from DB before speaking
        await self._load_session_info()

        # Update system prompt if in PANEL_AI mode
        if self.interview_mode == "PANEL_AI":
            self.conversation_history = [
                {
                    "role": "system",
                    "content": (
                        "You are a panel of three mock interviewers: Marcus, Sarah, and David. "
                        "For each turn, you must act and speak as one of these panel members. "
                        "Always state who is speaking at the start of your response (e.g., 'Marcus: ...' or 'Sarah: ...' or 'David: ...'). "
                        "Ask one concise question or follow-up at a time. Do not output markdown, "
                        "lists, or bullets. Keep responses short and conversational "
                        "(1-2 sentences max), suitable for a voice call."
                    ),
                }
            ]

        # 2. Mint a LiveKit JWT for the agent identity
        current_time = int(time.time())
        payload = {
            "iss": self.settings.livekit_api_key,
            "sub": "AI_Interviewer",
            "nbf": current_time - 60,
            "exp": current_time + 3600,
            "video": {
                "roomJoin": True,
                "room": self.room_name,
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True,
            },
        }
        agent_token = jwt.encode(
            payload,
            self.settings.livekit_api_secret,
            algorithm="HS256",
        )

        # 3. Register room event handlers
        @self.room.on("track_subscribed")
        def on_track_subscribed(track, publication, participant):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info("Subscribed to user audio track: %s", track.sid)
                asyncio.create_task(self.handle_user_audio(track))

        @self.room.on("participant_disconnected")
        def on_participant_disconnected(participant):
            human_participants = [
                p
                for p in self.room.remote_participants.values()
                if p.identity != "AI_Interviewer"
            ]
            if not human_participants:
                logger.info(
                    "All human participants left. Stopping voice agent for room %s.",
                    self.room_name,
                )
                asyncio.create_task(self.stop())

        # 4. Connect
        logger.info("Connecting voice agent to room: %s", self.room_name)
        try:
            await self.room.connect(self.settings.livekit_url, agent_token)
        except Exception as exc:
            logger.error("Failed to connect voice agent to LiveKit: %s", exc)
            self.is_running = False
            active_agents.pop(self.room_name, None)
            return

        # 5. Publish audio track
        publish_options = rtc.TrackPublishOptions(
            source=rtc.TrackSource.SOURCE_MICROPHONE
        )
        try:
            await self.room.local_participant.publish_track(
                self.audio_track, publish_options
            )
            logger.info("Published agent voice track successfully.")
        except Exception as exc:
            logger.error("Failed to publish voice track: %s", exc)

        # 6. Brief pause then open with the first question
        await asyncio.sleep(1.0)
        await self.speak(
            "Hello! Welcome to your mock interview session. I am your AI interviewer today. "
            "Let us begin. Could you please start by introducing yourself and giving a brief "
            "summary of your professional background?"
        )

    async def stop(self) -> None:
        if not self.is_running:
            return
        logger.info("Stopping voice agent for room: %s", self.room_name)
        self.is_running = False
        self.is_speaking = False
        self.is_processing = False
        active_agents.pop(self.room_name, None)
        try:
            await self.room.disconnect()
        except Exception as exc:
            logger.error("Error disconnecting room: %s", exc)

    # ── Speaking ────────────────────────────────────────────────────────────

    async def speak(self, text: str) -> None:
        if not self.is_running:
            return

        self.is_speaking = True

        # Append to LLM conversation history (store the full raw text including prefix so LLM maintains context of who said what)
        self.conversation_history.append({"role": "assistant", "content": text})

        # Determine speaker name and clean text
        speaker_name = "Interviewer"
        clean_text = text
        if self.interview_mode == "PANEL_AI":
            lower_text = text.lower().strip()
            matched_panelist = None
            for p in ["Marcus", "Sarah", "David"]:
                prefix_options = [
                    p.lower() + ":",
                    p.lower() + " here:",
                    "this is " + p.lower() + ":",
                    "this is " + p.lower() + " here:"
                ]
                if any(lower_text.startswith(opt) for opt in prefix_options):
                    matched_panelist = p
                    break
            
            if matched_panelist:
                speaker_name = matched_panelist
                colon_idx = text.find(":")
                if colon_idx != -1:
                    clean_text = text[colon_idx + 1:].strip()
            else:
                # Fallback to round-robin based on sequence (before save_question_to_db increments it)
                panelists = ["Marcus", "Sarah", "David"]
                speaker_name = panelists[self.question_sequence % 3]
        else:
            speaker_name = "Interviewer"

        logger.info("[%s] speaking: %s", speaker_name, clean_text[:120])

        # Persist as a QuestionInstance so evaluation can score the answer later
        question_id = await self._save_question_to_db(clean_text)
        if question_id:
            self.current_question_id = question_id

        # Map speakers to distinct edge-tts neural voices (free, no API key)
        voice_map = {
            "Marcus": "en-US-GuyNeural",
            "Sarah": "en-US-JennyNeural",
            "David": "en-US-ChristopherNeural",
            "Interviewer": "en-US-AriaNeural",
        }
        voice_name = voice_map.get(speaker_name, "en-US-AriaNeural")

        # Generate speech via Microsoft Edge TTS (WebSocket, no API key required)
        mp3_chunks: list[bytes] = []
        try:
            communicate = edge_tts.Communicate(clean_text, voice_name)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_chunks.append(chunk["data"])
        except Exception as exc:
            logger.error("TTS generation failed: %s", exc)
            self.is_speaking = False
            return

        if not mp3_chunks:
            logger.error("TTS returned no audio data.")
            self.is_speaking = False
            return

        # Decode MP3 → raw 16-bit PCM at 24 kHz mono (no ffmpeg required)
        try:
            decoded = miniaudio.decode(
                b"".join(mp3_chunks),
                output_format=miniaudio.SampleFormat.SIGNED16,
                nchannels=1,
                sample_rate=24000,
            )
            pcm_data: bytes = decoded.samples.tobytes()
        except Exception as exc:
            logger.error("TTS audio decode failed: %s", exc)
            self.is_speaking = False
            return

        # Broadcast transcript — audio is ready and will start immediately after
        await self.send_transcript(speaker_name, clean_text)

        # Stream 20 ms PCM frames directly into the LiveKit audio track
        try:
            sample_rate = 24000
            num_channels = 1
            chunk_duration = 0.020  # 20 ms
            bytes_per_chunk = int(sample_rate * chunk_duration) * 2 * num_channels  # 960 bytes
            offset = 0
            while self.is_speaking and self.is_running and offset < len(pcm_data):
                chunk = pcm_data[offset:offset + bytes_per_chunk]
                samples_per_channel = len(chunk) // (2 * num_channels)
                frame = rtc.AudioFrame(chunk, sample_rate, num_channels, samples_per_channel)
                await self.audio_source.capture_frame(frame)
                await asyncio.sleep(chunk_duration)
                offset += bytes_per_chunk
        except Exception as exc:
            logger.error("Error streaming voice response: %s", exc)
        finally:
            self.is_speaking = False
            # Record when we finished speaking so response_time_ms is accurate
            self.question_asked_at = time.time()

    # ── Audio capture / VAD ─────────────────────────────────────────────────

    async def handle_user_audio(self, track) -> None:
        try:
            audio_stream = rtc.AudioStream(track)
            buffer = bytearray()
            silence_duration = 0.0
            speaking = False
            threshold = 200.0  # RMS energy threshold for voice detection

            async for event in audio_stream:
                if not self.is_running:
                    break

                # FIX: also gate on is_processing to prevent queuing multiple
                # concurrent transcription tasks while the first is still running.
                if self.is_speaking or self.is_processing:
                    continue

                frame = event.frame
                sample_rate = frame.sample_rate
                num_channels = frame.num_channels

                samples = np.frombuffer(frame.data, dtype=np.int16)
                if len(samples) == 0:
                    continue

                rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))

                if rms > 50.0:
                    logger.debug("User mic RMS: %.1f (threshold: %.1f)", rms, threshold)

                if rms > threshold:
                    if not speaking:
                        logger.info("User speech onset detected (RMS: %.1f)", rms)
                        speaking = True
                    buffer.extend(frame.data)
                    silence_duration = 0.0
                else:
                    if speaking:
                        buffer.extend(frame.data)
                        silence_duration += len(frame.data) / (
                            sample_rate * 2 * num_channels
                        )

                        # FIX: reduced from 1.5 s → 0.8 s for faster turn-taking
                        if silence_duration >= 0.8:
                            logger.info(
                                "End-of-utterance silence (%.2f s). Processing response…",
                                silence_duration,
                            )
                            speaking = False
                            captured = bytes(buffer)
                            buffer.clear()
                            silence_duration = 0.0

                            # Set the flag BEFORE create_task to close the tiny
                            # race window between task creation and task start.
                            self.is_processing = True
                            asyncio.create_task(
                                self.process_user_response(
                                    captured, sample_rate, num_channels
                                )
                            )
        except Exception as exc:
            logger.exception("Exception in handle_user_audio: %s", exc)

    # ── STT → LLM → TTS pipeline ────────────────────────────────────────────

    async def process_user_response(
        self, audio_data: bytes, sample_rate: int, num_channels: int
    ) -> None:
        if not self.is_running:
            self.is_processing = False
            return

        try:
            await self._process_user_response_inner(audio_data, sample_rate, num_channels)
        except Exception as exc:
            logger.exception("Unhandled exception in process_user_response: %s", exc)
        finally:
            # Always release the processing lock, even if something above crashes.
            # Without this, is_processing stays True forever and all future user
            # audio is silently dropped in handle_user_audio.
            self.is_processing = False

    async def _process_user_response_inner(
        self, audio_data: bytes, sample_rate: int, num_channels: int
    ) -> None:
        # Measure how long the user took to respond
        response_time_ms = (
            int((time.time() - self.question_asked_at) * 1000)
            if self.question_asked_at is not None
            else 0
        )

        # ── 1. Write captured PCM to a temporary WAV file ──────────────────
        temp_input = f"temp_input_{self.room_name}.wav"
        with wave.open(temp_input, "wb") as wf:
            wf.setnchannels(num_channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)

        # ── 2. Transcribe via Groq Whisper ─────────────────────────────────
        transcription = ""
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.settings.groq_api_key}"}
                with open(temp_input, "rb") as f:
                    response = await client.post(
                        f"{self.settings.groq_base_url}/audio/transcriptions",
                        headers=headers,
                        files={"file": (temp_input, f, "audio/wav")},
                        data={
                            "model": self.settings.groq_whisper_model,
                            "response_format": "json",
                        },
                        timeout=30.0,
                    )
                if response.status_code == 200:
                    transcription = response.json().get("text", "").strip()
                    logger.info("Transcription: %s", transcription[:120])
                else:
                    logger.error("Groq API error %d: %s", response.status_code, response.text)
        except Exception as exc:
            logger.error("Failed to transcribe user audio: %s", exc)
        finally:
            try:
                os.remove(temp_input)
            except OSError:
                pass

        if not transcription:
            logger.info("Empty transcription — skipping LLM turn.")
            return

        # ── 3. Broadcast user transcript to frontend ───────────────────────
        await self.send_transcript("Candidate", transcription)

        # ── 4. Persist response to DB for evaluation pipeline ──────────────
        if self.current_question_id:
            await self._save_response_to_db(
                self.current_question_id,
                transcription,
                response_time_ms,
            )

        # ── 5. Build LLM reply via NVIDIA NIM ──────────────────────────────
        self.conversation_history.append({"role": "user", "content": transcription})
        reply = ""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.settings.nvidia_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.settings.nvidia_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.settings.nvidia_model,
                        "messages": self.conversation_history,
                        "max_tokens": 150,
                        "temperature": 0.7,
                    },
                    timeout=30.0,
                )
                if response.status_code == 200:
                    reply = (
                        response.json()["choices"][0]["message"]["content"].strip()
                    )
                else:
                    logger.error(
                        "NVIDIA NIM error %d: %s", response.status_code, response.text
                    )
        except Exception as exc:
            logger.error("Failed to query NVIDIA NIM: %s", exc)

        if not reply:
            reply = (
                "I appreciate your response. Let me ask you another question. "
                "Can you describe a challenging situation you faced in a previous "
                "role and how you resolved it?"
            )

        # ── 6. Clear processing flag, then speak the reply ─────────────────
        # Important: clear BEFORE speak() so that is_speaking (set inside speak)
        # is the only gate while audio is streaming.
        self.is_processing = False
        await self.speak(reply)


# ── Module-level launcher ───────────────────────────────────────────────────


def launch_voice_agent(room_name: str) -> None:
    """
    Spawn a background VoiceAgent for the given room if one is not already running.
    Safe to call multiple times — subsequent calls for the same room are no-ops.
    """
    if room_name not in active_agents:
        agent = VoiceAgent(room_name)
        active_agents[room_name] = agent
        asyncio.create_task(agent.start())
        logger.info("Dispatched background voice agent for room %s.", room_name)
