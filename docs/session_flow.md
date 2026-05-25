# Interview Practice Session — End-to-End Flow

Full journey from clicking **Start Session** through **Evaluation Report** generation.

---

## Phase 1 — Session Creation (UI → API)

```
User fills session config form
  → Topic, difficulty (EASY/MEDIUM/HARD), mode (1:1 AI / Panel), duration
  → POST /sessions
```

**API: `sessions/service.py → create_session()`**

1. **Plan gate**: Free users locked to `ONE_ON_ONE_AI` + max 15 min
2. **Usage gate**: `usage_svc.check_session_limit()` — enforces monthly session cap
3. **Topic validation**: Confirms topic exists and user has access
4. **DB write**: `InterviewSession` row inserted with `status = "CREATED"`
5. **Usage increment**: Async fire-and-forget counter bump
6. **Response**: Full `SessionResponse` returned to UI (includes `id`, config fields)

---

## Phase 2 — Activating the Session (UI → API)

```
User clicks "Start Session" button
  → PUT /sessions/{id}/start
```

**API: `sessions/service.py → start_session()`**

- State machine guard: rejects unless `status == "CREATED"`
- Sets `status = "ACTIVE"`, writes `started_at = now()`
- Returns updated `SessionResponse`

---

## Phase 3 — WebRTC Token + Voice Agent Launch

```
UI requests a room token
  → GET /sessions/{id}/webrtc-token
```

**API: `sessions/router.py → get_webrtc_token()`**

1. **JWT minted** (HS256) with LiveKit `videoGrant`:
   - `roomJoin: true`, `room: session_id`
   - `canPublish: true`, `canSubscribe: true`
   - Expiry: 2 hours
2. **`launch_voice_agent(str(session_id))`** called synchronously:
   - Instantiates all subsystems (see below)
   - Registers agent in `active_agents` dict
   - `asyncio.create_task(agent.start())` — runs in background

**Token returned → UI connects to LiveKit room**

---

## Phase 4 — Voice Agent Initialisation

> Runs in `app/ai/voice/agent.py`

### Subsystems wired in `launch_voice_agent()`:

| Layer | Class | Role |
|---|---|---|
| State | `InterviewState`, `ConversationState`, `CandidateState` | Session context |
| Memory | `ConversationMemory` (in-session) | Rolling 20-message window |
| LLM | `PromptManager`, `SystemPromptBuilder`, `InterviewPromptBuilder` | Prompt assembly |
| Response | `ResponseGenerator`, `ResponseParser`, `ResponseFormatter` | LLM call + parse |
| Audio in | `VoiceActivityDetector`, `AudioRecorder`, `STTService` (Groq Whisper) | Capture + transcribe |
| Audio out | `TTSService` (Azure TTS), `AudioStreamer`, `LiveKitTransport` | Synthesis + playback |
| Policies | `TurnPolicy`, `InterruptionPolicy`, `FollowupPolicy`, `DifficultyPolicy` | Turn control |
| Events | `EventBus` + handlers/subscribers | Decoupled pipeline |
| Realtime | `SpeculativeEngine`, `LatencyTracker`, `ResponseCache` | Low-latency optimization |
| **Step 8** | `MemoryPipeline` | Cross-session long-term memory |
| **Step 9** | `EvaluationPipeline` | Post-session structured scoring |
| **Step 10** | `PersonalityEngine` | Dynamic interviewer personality |

### `agent.start()` sequence:

```
1. _load_session_info()          → Load difficulty, mode, adaptive flag from DB
2. PersonalityEngine.select_persona()
   → mode "ONE_ON_ONE_AI" → "standard_interviewer" persona (YAML)
   → mode "PANEL_AI"      → "google_design_interviewer" persona
3. MemoryPipeline.retrieve_context_for_prompt()
   → Fetches candidate's historical memories from candidate_memories (pgvector similarity)
   → Stores compact text block in state.memory_context
4. transport.connect(agent_token)  → LiveKit room join
5. transport.publish_audio()       → AI voice track published
6. EventBus.emit(TOPIC_CHANGED)
7. EventBus.emit(RESPONSE_GENERATED) → triggers greeting speech
```

**Greeting delivered**: "Hello! Welcome to your mock interview session..."

---

## Phase 5 — Live Interview Loop (Per Turn)

```
┌─────────────────────────────────────────────────────────────┐
│                    EACH CANDIDATE TURN                       │
└─────────────────────────────────────────────────────────────┘
```

### 5a. Candidate Speaks → VAD Detection

```
handle_user_audio(track)
  ├── VoiceActivityDetector.process_frame(audio_frame)
  │     RMS threshold: 200.0
  │     Silence timeout: 0.8s
  ├── speech_started → recorder.start(), emit USER_STARTED_SPEAKING
  ├── is_speaking    → recorder.append(frame.data)
  └── speech_ended   → recorder.export_wav()
                        emit USER_STOPPED_SPEAKING
                        asyncio.create_task(process_user_response(wav_path))
```

### 5b. STT — Speech-to-Text (Groq Whisper)

```
STTService.transcribe(wav_path)
  → GroqTranscriptionProvider
  → openai SDK → api.groq.com/openai/v1
  → model: whisper-large-v3 (or whisper-large-v3-turbo)
  → response_format: verbose_json
  → Returns: transcribed text
```

> Cost: **$0.00** — Groq Whisper is currently free-tier

If transcription is empty → skip LLM, reset `is_processing`.

### 5c. DB Write — Save Response

```
_save_response_to_db(question_id, transcription, response_time_ms)
  → ResponseInstance row (answer_text, audio_processing_status="SKIPPED")
```

### 5d. Event Pipeline

```
EventBus.emit(TRANSCRIPT_RECEIVED)
  ├── ConversationHandler.on_transcript_received()   → appends to ConversationMemory
  ├── PolicyHandler.on_transcript_received()
  │     → TurnPolicy decides: FOLLOWUP / NEXT_QUESTION / CLARIFY
  │     → DifficultyPolicy adjusts difficulty based on performance
  │     → emits DECISION_CREATED
  ├── TranscriptSubscriber.on_transcript_received()  → logs
  └── BehavioralAnalyzer.on_transcript_received()    → tracks patterns
```

### 5e. Step 10 — Personality Adaptation (per turn)

```
PersonalityEngine.process_user_turn(topic_drift, hesitation, verbosity)
  → InterviewerState.adjust_impressions()
      patience ↑/↓, frustration ↑/↓, warmth ↑/↓
  → AdaptationEngine.get_turn_adaptation()   → pacing params
  → AdaptationEngine.get_prompt_instruction() → directive stored in state
  → RealismEngine.calculate_thinking_pause() → optional await asyncio.sleep()
```

### 5f. LLM — Response Generation

```
DecisionSubscriber.on_decision_created()
  → Interviewer.generate_response()
      ├── PromptManager assembles:
      │     SystemPromptBuilder  → role, topic, style
      │     InterviewPromptBuilder → conversation history (last 20 msgs)
      │     state.memory_context  → historical candidate context (Step 8)
      │     state.personality_instruction → live directive (Step 10)
      └── ResponseGenerator → NIM API (meta/llama-3.1-8b-instruct)
            or OpenAI GPT-4o-mini (if AI_ENABLED=true)
  → ResponseParser.parse() → clean question text
  → emit RESPONSE_GENERATED
```

### 5g. TTS + Audio Playback

```
RESPONSE_GENERATED →
  agent.speak(text)
    ├── PersonalityEngine.format_interviewer_speech(text)
    │     → RealismEngine.inject_conversational_filler()
    │         e.g. "Hmm, interesting..." / "Right, so..." (probability-gated)
    ├── SpeakerFormatter.format_speaker()   → speaker name, voice name
    ├── _save_question_to_db(clean_text)    → QuestionInstance row
    ├── TTSService.synthesize(text, voice)  → Azure TTS → MP3 bytes
    │     emit TTS_STARTED / TTS_COMPLETED
    └── AudioStreamer.stream_mp3(mp3_bytes)
          → decode MP3 → PCM frames → LiveKit audio source
          → emit AUDIO_STREAM_STARTED / AUDIO_STREAM_COMPLETED
  → emit QUESTION_ASKED
```

**→ Candidate hears the AI interviewer's question through WebRTC**

---

## Phase 6 — Ending the Session

```
User clicks "End Session"
  → PUT /sessions/{id}/complete
```

**API: `sessions/service.py → complete_session()`**

1. Guard: `status` must be `"ACTIVE"`
2. **Atomic transaction**:
   - `status → "COMPLETED"`, `ended_at = now()`
   - `EvaluationJob` row created with `status = "PENDING"`
3. **`agent.stop()` triggered** (participant disconnect or explicit call)

### `agent.stop()` cleanup (Steps 8 + 9):

```
Step 8 — MemoryPipeline.process_session_end()
  ├── SessionSummarizer.summarize_and_extract_memories()
  │     → LLM call: analyze full conversation transcript
  │     → Extract: behavioral patterns, strengths, weaknesses, hesitations
  │     → Produces List[MemoryObject] (episodic + behavioral + semantic)
  ├── MemoryStore.create_memory() × N   → INSERT into candidate_memories
  │     (with pgvector embeddings via MemoryEncoder)
  └── MemoryCompactor.compact_candidate_memories()
        → Merge near-duplicate memories (cosine similarity threshold)

Step 9 — EvaluationPipeline.execute_evaluation()  [voice-layer evaluation]
  ├── All registered evaluators run in parallel (asyncio.gather)
  ├── ScoringEngine.calculate_dimension_scores()
  │     TECHNICAL / BEHAVIORAL / COMMUNICATION / SYSTEM_DESIGN / REASONING
  ├── Consistency check: high tech score + low behavioral → −15% penalty
  └── Generates: EvaluationReport with strengths, improvements, recommendations
        Logged but not persisted (DB eval handled by worker below)
```

---

## Phase 7 — Background Evaluation Worker

```
APScheduler ticks every 10 seconds:
  run_evaluation_tick()
    → eval_repo.claim_next_pending_job()  (SELECT FOR UPDATE SKIP LOCKED)
    → eval_service.analyze_session_internal(db, session_id)
```

### `_run_analysis()` pipeline — the full evaluation:

```
1. Load session, validate status = "COMPLETED"
2. Load all QuestionInstance + ResponseInstance rows
3. Filter to answered questions only

4. Credit check:
   PRO user + credits > 0  → Real AI providers
   FREE / no credits        → Stub providers

5. For each question-response pair:
   ┌──────────────────────────────────────────┐
   │ 5a. Audio transcription (if audio_url)   │
   │     GroqTranscriptionProvider            │
   │     → whisper-large-v3                   │
   │     → verbose_json → text + duration     │
   │                                          │
   │ 5b. Merge sources:                       │
   │     transcribed_text ?? answer_text      │
   │                                          │
   │ 5c. LLM evaluation                       │
   │     NIMEvaluationProvider                │
   │     (or OpenAIEvaluationProvider)        │
   │     → SYSTEM_PROMPT + user_prompt        │
   │     → json_object mode, temp=0.1         │
   │     → Returns 5–6 scores (0–100):        │
   │         clarityScore                     │
   │         structureScore                   │
   │         depthScore                       │
   │         confidenceScore                  │
   │         communicationScore               │
   │         technicalScore (optional)        │
   │                                          │
   │ 5d. Server-side scores:                  │
   │     pressure_score   ← response_time_ms  │
   │     thinking_depth   ← thinking_time_ms  │
   │                                          │
   │ 5e. Difficulty boost (HARD: +4 to        │
   │     clarity, structure, depth, technical)│
   │                                          │
   │ 5f. Weighted overall_score:              │
   │     TECHNICAL sessions:                  │
   │       content_avg×0.45 + tech×0.30       │
   │       + comm×0.10 + conf×0.05            │
   │       + timing×0.10                      │
   │     BEHAVIORAL sessions:                 │
   │       content_avg×0.45 + conf×0.20       │
   │       + comm×0.15 + timing×0.10          │
   │       + tech_or_50×0.10                  │
   │                                          │
   │ 5g. Persist scores to ResponseInstance   │
   └──────────────────────────────────────────┘

6. Aggregate all signal averages → session-level scores
7. Create EvaluationReport row (DB)
8. Consume evaluation credit (PRO only)
9. Session status → "ANALYZED"
10. Mark EvaluationJob → "COMPLETED"
```

---

## Phase 8 — Reading the Evaluation Report

```
UI polls GET /sessions/{id}/status  (every few seconds)
  → evaluation_job_status: "PENDING" → "PROCESSING" → "COMPLETED"
  → overall_score appears

User opens Report page
  → GET /sessions/{id}/evaluation
  → evaluation/service.py → get_evaluation()
```

### Report Structure (`SessionEvaluationResponseSchema`):

```json
{
  "session_id": "uuid",
  "overall_score": 74.3,
  "summary": "Solid foundation with an overall score of 74.3/100. Key areas for growth: structure and confidence.",
  "dimensions": {
    "clarity":        82.0,   // LLM scored
    "structure":      61.0,   // LLM scored
    "depth":          70.0,   // LLM scored
    "confidence":     58.0,   // LLM scored
    "communication":  75.0,   // LLM scored
    "hesitation":     88.0,   // INVERTED: 100 - raw_hesitation_score (higher = better)
    "technical":      79.0,   // LLM scored (null for behavioral sessions)
    "pressure":       83.0,   // server: response_time_ms curve
    "thinking_depth": 71.0    // server: thinking_time_ms curve
  },
  "strengths": [
    "Clear and coherent communication",
    "Calm and composed under time pressure"
  ],
  "improvements": [
    "Use the STAR format (Situation, Task, Action, Result)",
    "Outline your answer mentally before speaking",
    "Eliminate hedging phrases like 'I think' and 'maybe'",
    "State your position assertively, then support it with evidence"
  ],
  "difficulty_progression": {
    "started_at": "MEDIUM",
    "ended_at": "HARD"
  },
  "evaluated_at": "2026-05-24T10:43:32.000Z"
}
```

### Score Thresholds

| Range | Summary Label |
|---|---|
| ≥ 75 | "Strong performance" — clarity and structure highlighted as strengths |
| 50–74 | "Solid foundation" — structure and confidence flagged for growth |
| < 50 | "Developing performance" — depth and hesitation are key focus |

### Strength derivation

Any dimension scoring **≥ 70** is automatically included in `strengths[]`.

### Improvement suggestion triggers

| Dimension | Trigger | Suggestion |
|---|---|---|
| structure | < 60 | STAR format, mental outline before speaking |
| confidence | < 60 | Eliminate hedging, state position assertively |
| depth | < 60 | Quantified examples, explain the "why" |
| communication | < 60 | 60–120s target, record and review for fillers |
| pressure | < 50 | "Too quick — take a breath" |
| thinking_depth | < 50 | "Practice 4–8s pause before answering" |

---

## Data Flow Diagram

```
Browser ──POST /sessions──────────────────────► InterviewSession (CREATED)
        ──PUT /start──────────────────────────► InterviewSession (ACTIVE)
        ──GET /webrtc-token───────────────────► JWT + launch_voice_agent()
                                                     │
              LiveKit room join ◄────────────────────┘
                    │
              [VAD loop] User speaks
                    │
              Groq Whisper STT
                    │
              EventBus TRANSCRIPT_RECEIVED
                    │
              ┌─────▼──────┐  ┌────────────────┐  ┌──────────────────┐
              │ TurnPolicy  │  │ BehavioralAnal. │  │PersonalityEngine │
              └─────┬──────┘  └────────────────┘  └──────────────────┘
                    │ DECISION_CREATED
              NIM/OpenAI LLM generate question
                    │
              Azure TTS → MP3 → LiveKit → Candidate ears
                    │
              [loop repeats until End Session]
                    │
        ──PUT /complete──────────────────────►  InterviewSession (COMPLETED)
                                                EvaluationJob (PENDING)
                                                agent.stop()
                                                  ├── MemoryPipeline (Step 8)
                                                  └── EvaluationPipeline (Step 9)
                                                     │
              APScheduler (10s tick) ────────────────┘
              claim_next_pending_job()
              analyze_session_internal()
                ├── Groq Whisper transcription (per response)
                ├── NIM LLM evaluation (per response)
                ├── Server-side timing scores
                └── Aggregate → EvaluationReport (ANALYZED)
                                                     │
        ──GET /sessions/{id}/evaluation─────────────►  SessionEvaluationResponseSchema
```

---

## Key Technology Choices

| Component | Technology | Why |
|---|---|---|
| Voice transport | LiveKit (WebRTC) | Sub-100ms audio latency |
| STT | Groq Whisper large-v3 | Free tier, LPU-accelerated, fast |
| LLM (interviewer) | NVIDIA NIM (llama-3.1-8b-instruct) | Free OSS, low latency |
| LLM (evaluation) | NIM or OpenAI GPT-4o-mini | Credit-gated |
| TTS | Azure Cognitive Services | High-quality neural voices |
| Vector memory | pgvector (PostgreSQL) | No extra infra, co-located with main DB |
| Background jobs | APScheduler (in-process) | No Redis/Celery overhead needed |
