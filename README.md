# BrainTrain 🚀

**AI-Powered Technical Interview Training Platform — built for developers, by developers.**

*Substantially built for the hackathon theme: **AI at Work: Productivity & Teamwork Reimagined**, leveraging the **Microsoft AI Stack** via **Azure AI Foundry (GitHub Models)**.*

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Platform Compliance](https://img.shields.io/badge/microsoft--ai--stack-compliant-blue.svg)]()
[![Theme](https://img.shields.io/badge/theme-AI--at--Work-orange.svg)]()

---

## Table of Contents

1. [What is BrainTrain?](#-what-is-braintrain)
2. [Tech Stack](#-tech-stack)
3. [Repository Structure](#-repository-structure)
4. [How AI is Implemented](#-how-ai-is-implemented)
5. [How RAG is Implemented](#-how-rag-is-implemented)
6. [How LangChain is Utilised](#-how-langchain-is-utilised)
7. [How the Interview Room is Simulated](#-how-the-interview-room-is-simulated)
8. [Interview Journeys](#-interview-journeys)
9. [Practice Sessions](#-practice-sessions)
10. [Module Reference — Backend](#-module-reference--backend-appsapi)
11. [Module Reference — Frontend](#-module-reference--frontend-appsweb)
12. [Getting Started](#-getting-started)
13. [Environment Variables](#-environment-variables)

---

## 🎯 What is BrainTrain?

BrainTrain is a **full-stack, AI-powered interview training platform** that replaces manual peer-coaching with an always-on voice agent. Engineers upload their resume and a job description, and the platform:

1. **Analyses** both documents to understand candidate strengths, weaknesses, and the target role requirements.
2. **Generates a personalised multi-round interview journey** that mirrors a real hiring process (Technical, System Design, Behavioral rounds).
3. **Simulates a live interview room** — the AI interviewer speaks over WebRTC, listens, transcribes the candidate's speech, and makes real-time decisions (follow-ups, clarifications, difficulty escalation).
4. **Evaluates responses** across 7 calibrated dimensions: Clarity, Structure, Depth, Confidence, Communication, Technical Accuracy, and Hesitation.
5. **Coaches** the user after each session through a conversational coaching chat.
6. **Creates a 7-day personalised training plan** targeting the weakest performance dimension.

> **Comparison quick-table**
>
> | Feature | ChatGPT | Google Interview Warmup | **BrainTrain** |
> |---|---|---|---|
> | Multi-Dimensional Scoring | No | No | **Yes (7 calibrated metrics)** |
> | Longitudinal Tracking | No | No | **Yes (progress over time)** |
> | Real-time Voice Probing | No | No | **Yes (async voice agent)** |
> | Personalised Training Plan | No | No | **Yes (7-day plan)** |
> | Knowledge Base (RAG) | No | No | **Yes (hybrid semantic + keyword)** |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Monorepo** | pnpm workspaces |
| **Frontend** | Next.js 15 (App Router), React 18, Tailwind CSS 3, Zustand v5, React Query v5, Recharts |
| **Backend** | FastAPI, Python 3.12, SQLAlchemy 2.0 async, PostgreSQL + asyncpg, Alembic |
| **AI — LLM** | Azure AI Foundry / GitHub Models (primary), NVIDIA NIM, OpenAI GPT-4o-mini (fallback), Stub (dev) |
| **AI — Audio STT** | Groq Whisper (whisper-large-v3), OpenAI Whisper-1 (fallback) |
| **AI — TTS** | Edge-TTS (Microsoft neural voices) |
| **AI — Orchestration** | LangChain (coaching chain), custom policy engine |
| **WebRTC / Audio** | LiveKit (real-time audio rooms) |
| **Vector Store** | PostgreSQL `pgvector` — IVFFlat cosine index |
| **Shared Types** | `packages/shared` — TypeScript DTOs and enums |

---

## 📁 Repository Structure

```
braintrain/
├── apps/
│   ├── api/                          # FastAPI backend
│   │   ├── app/
│   │   │   ├── adaptive/             # Adaptive difficulty engine
│   │   │   ├── ai/
│   │   │   │   ├── factory.py        # Provider selection (GitHub > NIM > OpenAI > Stub)
│   │   │   │   ├── intelligence/     # Retrieval pipeline, memory, rule engine
│   │   │   │   ├── orchestrators/    # High-level AI orchestration
│   │   │   │   ├── prompts/          # Prompt templates
│   │   │   │   ├── providers/        # Concrete LLM provider implementations
│   │   │   │   ├── rag/              # RAG ingest (ingest.py) + retriever (retriever.py)
│   │   │   │   └── voice/            # Live voice agent (agent.py) + all subsystems
│   │   │   │       ├── audio/        # VAD, recorder, STT, TTS, LiveKit transport
│   │   │   │       ├── behavior/     # Behavioral analyser
│   │   │   │       ├── conversation/ # Memory, fact registry, fact extractor
│   │   │   │       ├── decisions/    # Turn decision logic
│   │   │   │       ├── evaluation/   # In-session evaluation pipeline
│   │   │   │       ├── events/       # EventBus, handlers, subscribers
│   │   │   │       ├── llm/          # Prompt builders, response generator/parser
│   │   │   │       ├── memory/       # Episodic, semantic, behavioral memory
│   │   │   │       ├── policies/     # Turn, followup, difficulty, response, domain policies
│   │   │   │       ├── realtime/     # Latency tracker, speculative engine, cache, prefetcher
│   │   │   │       ├── simulation/   # Personality engine, registry, profiles, adaptation
│   │   │   │       └── state/        # Conversation, candidate, interview state
│   │   │   ├── core/                 # Config, exceptions, middleware, rate limiter
│   │   │   ├── db/                   # SQLAlchemy models + Alembic migrations
│   │   │   ├── interview_journey/    # Journey orchestrator, analyzers, planners, personas
│   │   │   │   ├── analyzers/        # resume_analyzer, jd_analyzer, company_signal_extractor
│   │   │   │   ├── personas/         # persona_generator, speech_patterns
│   │   │   │   ├── planners/         # round_generator, strategy_generator, difficulty_mapper
│   │   │   │   └── routers/          # Journey HTTP endpoints
│   │   │   ├── modules/              # Domain modules (each = router + service + schema + repo)
│   │   │   │   ├── analytics/        # Performance analytics service
│   │   │   │   ├── billing/          # Stripe billing integration
│   │   │   │   ├── coaching/         # AI coaching sessions
│   │   │   │   ├── evaluation/       # Post-session evaluation reports
│   │   │   │   ├── identity/         # Auth, JWT, user profiles
│   │   │   │   ├── knowledge/        # Knowledge document CRUD + chunk management
│   │   │   │   ├── question_bank/    # Curated question storage
│   │   │   │   ├── questions/        # Dynamic question generation per session
│   │   │   │   ├── responses/        # Candidate response submission
│   │   │   │   ├── sessions/         # Interview session lifecycle
│   │   │   │   ├── topics/           # Topic management
│   │   │   │   └── training_plans/   # 7-day AI-generated training plans
│   │   │   ├── usage/                # Token / usage tracking
│   │   │   └── workers/              # APScheduler background jobs
│   │   └── personas/                 # YAML/JSON interviewer persona definitions
│   │       ├── behavioral/
│   │       ├── faang/                # e.g. google_system_design.yaml
│   │       └── startup/
│   ├── web/                          # Next.js 15 frontend
│   │   ├── app/
│   │   │   ├── (auth)/               # Login / signup pages
│   │   │   ├── (dashboard)/dashboard/
│   │   │   │   ├── page.tsx          # Main dashboard
│   │   │   │   ├── analytics/        # Analytics charts
│   │   │   │   ├── coach/            # Coaching chat UI
│   │   │   │   ├── cognitive/        # Cognitive performance view
│   │   │   │   ├── interview-journey/ # Journey creation + round list UI
│   │   │   │   ├── knowledge/        # Knowledge base upload UI
│   │   │   │   ├── progress/         # Progress tracker
│   │   │   │   ├── sessions/         # Session history list
│   │   │   │   ├── settings/         # User settings
│   │   │   │   ├── topics/           # Topic browser
│   │   │   │   ├── training/         # Training plan viewer
│   │   │   │   └── trends/           # Score trends
│   │   │   └── (session)/            # Live interview session UI
│   │   ├── components/               # Shared UI components
│   │   ├── core/                     # API client, auth, config
│   │   ├── features/                 # Feature-level hooks & logic (auth, onboarding, training)
│   │   ├── hooks/                    # Custom React hooks
│   │   └── lib/                      # Utilities
│   └── mobile/                       # Mobile client (React Native)
├── docs/                             # Architecture guides
├── packages/
│   └── shared/                       # Shared TypeScript types, DTOs, enums
└── prisma/                           # (Legacy) Prisma schema reference
```

---

## 🤖 How AI is Implemented

BrainTrain uses a **multi-layer AI architecture** with provider abstraction, so the system works regardless of which LLM API key you have.

### Provider Factory (`app/ai/factory.py`)

The factory module is the single entry point for all AI providers. It selects the correct implementation at startup using a **priority chain**:

```
LLM tasks (question gen, evaluation, coaching, follow-up):
  1. GitHub Models / Azure AI Foundry  (GITHUB_TOKEN present)
  2. NVIDIA NIM                        (NVIDIA_API_KEY present)
  3. OpenAI GPT-4o-mini               (OPENAI_API_KEY present)
  4. Stub provider                     (zero-cost local dev)

Audio transcription:
  1. Groq whisper-large-v3            (GROQ_API_KEY present)
  2. OpenAI Whisper-1                 (OPENAI_API_KEY present)
  3. Stub provider
```

Each provider is cached with `@lru_cache(maxsize=1)` so it is instantiated once per process.

### Five Distinct AI Tasks

| Task | Factory Function | Used By |
|---|---|---|
| **Question Generation** | `get_question_gen_provider()` | Session question endpoint |
| **Response Evaluation** | `get_evaluation_provider()` | Post-response scoring |
| **AI Coaching** | `get_coach_provider()` | Coaching chat sessions |
| **Follow-up Analysis** | `get_followup_provider()` | Real-time interviewer decisions |
| **Audio Transcription** | `get_transcription_provider()` | Voice agent STT pipeline |

### Azure AI Foundry / GitHub Models Integration

When `GITHUB_TOKEN` is set, all LLM calls route to `https://models.inference.ai.azure.com`. The same OpenAI-compatible interface means zero code changes are needed when switching between providers — only the base URL and token differ.

### Adaptive Difficulty Engine (`app/adaptive/engine.py`)

After each response, the engine calculates the next question's difficulty:

- Pulls the last **3 scored responses** across sessions with the same user / topic / interview type.
- Computes the **rolling average overall score**.
- Applies threshold rules:
  - Score **> 72** → escalate difficulty (EASY → MEDIUM → HARD)
  - Score **< 55** → de-escalate difficulty (HARD → MEDIUM → EASY)
  - Otherwise → maintain current difficulty
- Requires a minimum of **2 scored responses** before any transition.

---

## 📚 How RAG is Implemented

RAG (Retrieval-Augmented Generation) is used to **ground the AI interviewer's questions and follow-ups** in verified technical knowledge, preventing hallucinations and ensuring questions are accurate and deep.

### Ingestion Pipeline (`app/ai/rag/ingest.py`)

A curated set of technical interview guides is shipped with the codebase and ingested on first run via:

```bash
uv run python -m app.ai.rag.ingest
```

**Domains covered by the seed corpus:**
- Backend Engineering (Caching Strategies, Redis, Database Concurrency, Isolation Levels, Deadlocks)
- Frontend Engineering (React Fiber, Performance Optimization, Core Web Vitals — LCP/INP/CLS)
- System Design (Distributed Rate Limiters — Token Bucket, Leaky Bucket, Sliding Window)
- AI Engineering (Advanced RAG, pgvector indexing strategies, Hybrid Retrieval)

**Ingestion steps per document:**
1. Deduplicate by title — delete and re-create if existing.
2. Pass to `KnowledgeDocumentService.create_document()` which handles:
   - **Chunking** — splits the markdown content into semantically coherent chunks.
   - **Embedding generation** — each chunk is encoded into a vector via `MemoryEncoder`.
   - **Storage** — chunk text + vector + metadata (domain, topic, difficulty) stored in PostgreSQL with `pgvector`.

### Hybrid Retrieval Pipeline (`app/ai/intelligence/retrieval/retrieval_pipeline.py`)

Every time the interviewer needs context, it calls `InterviewKnowledgeRetriever.retrieve_context()`:

```
1. Semantic Search    — cosine distance vector similarity (pgvector IVFFlat index)
2. Keyword Search     — PostgreSQL full-text search (to_tsquery / ILIKE)
3. Metadata Filtering — filter by domain, topic, difficulty
4. Hybrid Re-ranking  — Reciprocal Rank Fusion (RRF) merges both result sets
5. Context Building   — top-k chunks formatted into a grounding block (max 1000 tokens)
```

The retrieval query is parameterised by:
- `query_text` — the current question topic or candidate's answer segment
- `domain` — e.g. `backend`, `frontend`, `system_design`
- `topic` — e.g. `caching`, `react`, `distributed_systems`
- `difficulty` — `EASY` / `MEDIUM` / `HARD`
- `top_k` (default 3) and `similarity_threshold` (default 0.6)

The resulting context string is injected into the interviewer's system prompt, giving the LLM authoritative grounding before it generates its next question or follow-up.

### Memory Encoder (`app/ai/voice/memory/memory_encoder.py`)

`MemoryEncoder` wraps the embedding model and is shared between the RAG pipeline and the voice memory subsystem. This ensures a single, consistent embedding space across the entire platform.

---

## 🔗 How LangChain is Utilised

LangChain is used specifically for the **AI Coaching module** (`app/ai/providers/langchain_coach.py`) when an OpenAI key is configured.

### `LangChainCoachProvider`

```python
# Backed by ChatOpenAI (gpt-4o-mini, temperature=0.7)
llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, temperature=0.7, max_tokens=512)
```

**How it works:**
1. The full conversation history (`messages: List[dict]`) is passed on every call — the provider is **stateless**, meaning the calling service owns the history.
2. A rich **system prompt** is built from a template that injects:
   - The current `focus_area` (confidence, clarity, technical, general)
   - An optional `context_summary` pulled from the user's most recent evaluation report — giving the coach specific, data-grounded feedback rather than generic advice.
3. The conversation is converted into LangChain message types (`SystemMessage`, `HumanMessage`, `AIMessage`) and dispatched via `llm.ainvoke()`.

**Coaching frameworks the system prompt mandates:**
- STAR (Situation, Task, Action, Result)
- SBI (Situation, Behavior, Impact)
- Rule of Three
- Problem-Solution-Result

**Coach persona:** "BrainTrain's elite AI communication coach — a combination of executive communication coach, behavioral interview expert, and career advisor." It is instructed to be warm but direct, offer micro-exercises under 5 minutes, celebrate specific wins, and stay concise (3–5 sentences).

For non-OpenAI providers (GitHub Models, NIM), the coaching endpoint falls back to native provider implementations (`GitHubModelsCoachProvider`, `NIMCoachProvider`) that replicate the same conversational pattern without LangChain.

---

## 🎤 How the Interview Room is Simulated

The simulated interview room is the most complex part of BrainTrain. It uses **LiveKit WebRTC**, a multi-layer voice processing pipeline, a personality simulation engine, and a real-time event bus — all coordinated by the `VoiceAgent` class.

### Architecture Overview

```
Candidate's browser
      │  (WebRTC audio track via LiveKit SDK)
      ▼
LiveKit Server (self-hosted or cloud)
      │  (audio frames)
      ▼
LiveKitTransport  →  AudioRecorder  →  VAD (VoiceActivityDetector)
                                              │
                                    Silence detected (end of turn)
                                              │
                                        STTService (Groq Whisper)
                                              │ transcript
                                        MemoryPipeline
                                              │ encoded memory
                                    ┌─────────────────────┐
                                    │   TurnPolicy decides │
                                    │  what happens next:  │
                                    │  follow-up / next Q  │
                                    │  / clarification     │
                                    └─────────┬───────────┘
                                              │ decision
                                    PersonalityEngine
                                    (adapts tone & pacing)
                                              │
                              ┌───────────────────────────┐
                              │  RAG retriever (context)   │
                              │  + LLM (response gen)      │
                              └───────────┬───────────────┘
                                          │ text response
                                      TTSService (Edge-TTS)
                                          │ audio bytes
                                    AudioStreamer
                                          │ (back to LiveKit)
                                          ▼
                                Candidate's speakers
```

### Key Subsystems

#### 1. `VoiceAgent` (`app/ai/voice/agent.py`)
The central coordinator (~940 lines). Holds references to every subsystem. Runs the main event loop: receives audio frames from LiveKit, detects speech boundaries with VAD, transcribes, runs policy decisions, generates responses, and streams audio back.

#### 2. `PersonalityEngine` + `PersonalityRegistry` (`app/ai/voice/simulation/`)
The interviewer has a **configurable personality** described by 12 numeric parameters:

| Parameter | Effect |
|---|---|
| `pacing_speed` | How fast the interviewer speaks/responds |
| `interruption_frequency` | How often the interviewer interrupts |
| `silence_tolerance` | How long the interviewer waits before prompting |
| `skepticism_level` | How much the interviewer challenges answers |
| `technical_depth` | Depth of technical questions |
| `followup_aggressiveness` | How relentlessly follow-ups are pursued |
| `verbosity_tolerance` | Patience for long/rambling answers |
| `ambiguity_tolerance` | Acceptance of vague answers |
| `pressure_intensity` | Overall stress level of the interview |
| `conversational_warmth` | Friendliness of tone |
| `challenge_escalation` | Strategy (e.g., `TradeoffDrilling`) |
| `acknowledgment_patterns` | List of verbal acknowledgments the interviewer uses |

Personas are defined in YAML/JSON files under `apps/api/personas/` (organised by `faang/`, `behavioral/`, `startup/`) and seeded into the `agent_personas` database table on startup. The `PersonalityRegistry` checks the database first (so edits via the admin dashboard take effect immediately) and falls back to static files.

**Example — Google System Design persona (`faang/google_system_design.yaml`):**
```yaml
name: "Google System Design Interviewer"
archetype: "Skeptical Architect"
characteristics:
  skepticism_level: 0.9
  technical_depth: 0.95
  pressure_intensity: 0.75
  conversational_warmth: 0.3
  verbosity_tolerance: 0.3
acknowledgment_patterns:
  - "Okay. But what happens if the network partitions?"
  - "Understood. However, how does that scale write-path throughput?"
```

#### 3. `AdaptationEngine` + `RealismEngine` (`app/ai/voice/simulation/`)
- **`AdaptationEngine`** — at each candidate turn, reads `topic_drift`, `hesitation`, and `verbosity` signals to dynamically adjust the interviewer's warmth, patience, and frustration state. This makes the interviewer respond realistically to candidate performance.
- **`RealismEngine`** — injects conversational fillers ("Hmm...", "Let me think...") matched to the active personality profile, and calculates a thinking delay (pause before the interviewer speaks) to simulate human cognition.

#### 4. Policy System (`app/ai/voice/policies/`)
Stateless policy objects separate behavioural rules from the `VoiceAgent`:

| Policy | Purpose |
|---|---|
| `TurnPolicy` | Decides whether it is the interviewer's or candidate's turn to speak |
| `FollowupPolicy` | Determines if a follow-up question should be generated |
| `DifficultyPolicy` | Signals when difficulty should change |
| `ResponsePolicy` | Controls response length and style |
| `InterruptionPolicy` | Governs when the agent may interrupt |
| `DomainPolicy` | Enforces topic boundaries (prevents domain drift) |
| `FactGroundingPolicy` | Requires the LLM to cite facts from the RAG context |

#### 5. Memory System (`app/ai/voice/memory/`)
A multi-layer memory pipeline stores and retrieves information across the session:

- **Episodic Memory** — sequence of turns and conversation events
- **Semantic Memory** — vectorised summaries of key facts discussed
- **Behavioral Memory** — tracks candidate patterns (hesitation rate, verbosity, topic changes)
- `MemoryCompactor` — summarises old memory to prevent context overflow
- `MemoryDecay` — ages out stale memories
- `RetrievalEngine` + `RetrievalRanker` — fetches relevant past context for the current question
- `SessionSummarizer` — produces an end-of-session memory summary

#### 6. Realtime Optimisation (`app/ai/voice/realtime/`)
Built for low-latency response:

- `LatencyTracker` — measures end-to-end response latency
- `ResponseCache` — caches common interviewer responses
- `ResponsePrefetcher` — pre-generates likely next questions speculatively
- `TurnPredictor` — predicts when the candidate is about to finish speaking
- `SpeculativeEngine` — starts generating the next response before the candidate fully stops
- `TimingController` — coordinates audio playback timing
- `InterruptionCoordinator` — handles barge-in events gracefully

#### 7. Event Bus (`app/ai/voice/events/`)
A pub/sub event bus (`EventBus`) decouples subsystems. Key event types:
- `TRANSCRIPT_RECEIVED` — new candidate speech transcribed
- `INTERVIEWER_SPEAKING` / `CANDIDATE_SPEAKING` — turn state changes
- `EVALUATION_COMPLETE` — scoring finished for a response
- `SESSION_ENDED` — session lifecycle event

Handlers: `ConversationHandler`, `PolicyHandler`, `LoggingHandler`, `MetricsHandler`  
Subscribers: `TranscriptSubscriber`, `DecisionSubscriber`, `AudioSubscriber`

---

## 🗺️ Interview Journeys

An **Interview Journey** is a curated, multi-round interview simulation tailored to a specific job application. It mirrors the real hiring process at a target company and role.

### Creation Flow

1. **User submits** their resume text and a job description URL or text, along with the target company name and role title.
2. **`analyze_and_plan()` orchestrator** (`app/interview_journey/orchestrator.py`) runs five sequential analyses:

   | Analyser | Output |
   |---|---|
   | `resume_analyzer.py` | Candidate level (JUNIOR/MID/SENIOR), verified technologies, strengths, weaknesses |
   | `jd_analyzer.py` | Role category (FRONTEND/BACKEND/FULLSTACK/DATA/DEVOPS), role level, must-have and preferred skills |
   | `company_signal_extractor.py` | Company-specific interview patterns and signals (FAANG hiring bar, startup pace) |
   | `verified_profile_builder.py` | Consolidated candidate profile reconciling resume vs JD gap |
   | `prerequisites_generator.py` | Study checklist — specific topics the candidate should revise before each round |

3. **`round_generator.py`** builds the round sequence based on role category:

   | Role | Rounds Generated |
   |---|---|
   | BACKEND | Behavioral + Backend Core + System Design + Backend Deep Dive |
   | FRONTEND | Behavioral + Frontend Core + Frontend Architecture + Frontend System Design |
   | FULLSTACK | Behavioral + Frontend Core + Backend Core + System Design |
   | DATA | Behavioral + Data Core + System Design + ML Deep Dive |
   | DEVOPS | Behavioral + Infrastructure + others |

4. **For each round**, the planner runs:
   - `generate_strategy()` — creates a questioning strategy for this round based on company signals and candidate level.
   - `map_difficulty()` — sets the starting difficulty (EASY/MEDIUM/HARD).
   - `generate_persona()` — selects an interviewer persona archetype matched to the round type and company culture.

5. **Each round is stored** as a `JourneySession` row in the database, linked to the parent Journey. The Journey's status is set to `ACTIVE`.

### Starting a Round

When the user clicks "Start Round":
- `start_round()` creates a live `InterviewSession` with the round's difficulty, persona config, and verified candidate profile injected as `personality_config`.
- A LiveKit room token is provisioned.
- The `VoiceAgent` connects to the room, loads the specified persona, and begins the session.

### Journey Memory

`journey_memory_manager.py` maintains cross-round context — what was discussed in previous rounds is available to the interviewer in subsequent rounds, creating a cohesive narrative across the full interview loop.

### Final Report

`final_report_generator.py` aggregates scores across all rounds to produce a holistic interview performance report including round-by-round breakdown, overall strengths/weaknesses, and a recommended next action.

---

## 🏋️ Practice Sessions

A **Practice Session** is a standalone, single-topic interview session — not tied to a full journey. It is the quickest way to practice a specific skill area.

### Session Lifecycle

```
User selects topic + difficulty + type (TECHNICAL/BEHAVIORAL)
    │
POST /sessions  →  creates InterviewSession record
    │
GET /sessions/:id/questions/next
    │
    ├── Calls QuestionGenerationProvider (LLM)
    │       └── Injects RAG context for current topic
    │
    └── Returns next QuestionInstance
           │
    User submits answer (voice or text)
           │
    POST /questions/:id/responses
           │
    EvaluationPipeline scores the response (7 dimensions)
           │
    AdaptiveDifficultyEngine determines next difficulty
           │
    Repeat until session ends
           │
    POST /sessions/:id/end
           │
    EvaluationReport generated (aggregated scores, coaching notes)
           │
    Optional: POST /coaching         → AI coaching session
    Optional: POST /training-plans/generate → 7-day plan
```

### Question Generation

Questions are dynamically generated per turn via the LLM, grounded by:
- The session's **topic** and **interview type**
- RAG-retrieved **knowledge chunks** for the topic
- The candidate's **conversation history** (to avoid repeating questions)
- The **current difficulty level** from the adaptive engine

### Response Evaluation (`app/modules/evaluation/service.py`)

Every submitted response is scored across **7 dimensions** (0–100 scale each):

| Dimension | What is Measured |
|---|---|
| **Clarity** | How clear and unambiguous the answer is |
| **Structure** | Logical organisation (intro, body, conclusion) |
| **Depth** | Technical depth and completeness |
| **Confidence** | Assertiveness and conviction in the answer |
| **Communication** | Language quality, grammar, professional vocabulary |
| **Technical Accuracy** | Correctness of technical claims |
| **Hesitation** | Inverse of pause frequency and filler word count |

An `overall_score` is the weighted average of all dimensions. The evaluation also produces:
- A `strengths` paragraph (what the candidate did well)
- A `weaknesses` paragraph (specific improvement areas)
- `coaching_notes` (actionable advice for immediate improvement)

### Coaching Sessions (`app/modules/coaching/service.py`)

After any session, the user can open a coaching chat. The coaching service:
1. Optionally loads the linked session's evaluation report to build a `context_summary`.
2. Creates a `CoachingSession` record with a chosen `focus_area` (confidence, clarity, technical, general).
3. Routes messages through `LangChainCoachProvider` (if OpenAI key is set) or a native provider.
4. Maintains full conversation history in the database — the user can close and re-open a session without losing context.

### Training Plans (`app/modules/training_plans/service.py`)

After evaluation, the platform generates a **7-day personalised training plan**:
1. Identifies the **weakest scoring dimension** from the latest evaluation report.
2. Uses the evaluation AI provider to generate **14 micro-exercises** (2 per day) specifically targeting that dimension.
3. Each exercise has a type (`mirror_practice`, `recording`, `writing`, `voice_exercise`) with step-by-step instructions.
4. Any existing active plan is **superseded** — there is always at most one active plan per user.
5. Users can mark tasks as complete from the Training Plan dashboard page.

---

## 📦 Module Reference — Backend (`apps/api`)

### `app/ai/`

| File / Folder | Purpose |
|---|---|
| `factory.py` | Provider selection — single source of truth for all AI dependencies |
| `intelligence/` | Retrieval pipeline, memory orchestration, rule engine, strategic orchestration |
| `providers/` | 19 concrete provider implementations (GitHub Models, NIM, OpenAI, Groq, Stub, LangChain) |
| `rag/ingest.py` | Batch ingestion of curated documents into pgvector |
| `rag/retriever.py` | `InterviewKnowledgeRetriever` — query interface for RAG |
| `voice/agent.py` | `VoiceAgent` — main interview room coordinator |
| `voice/simulation/` | `PersonalityEngine`, `PersonalityRegistry`, `AdaptationEngine`, `RealismEngine` |
| `voice/memory/` | Multi-tier memory pipeline (episodic, semantic, behavioral) |
| `voice/policies/` | 7 stateless policy classes |
| `voice/realtime/` | Latency tracking, speculative response generation, caching |
| `voice/events/` | `EventBus`, handlers, subscribers |
| `voice/audio/` | VAD, recorder, STT service, TTS service, LiveKit transport, audio streamer |
| `voice/llm/` | Prompt builders, response generator/parser, speaker formatter |

### `app/interview_journey/`

| File / Folder | Purpose |
|---|---|
| `orchestrator.py` | `analyze_and_plan()`, `start_round()` — top-level journey lifecycle |
| `analyzers/` | Resume analyser, JD analyser, company signal extractor, profile builder |
| `planners/` | Round generator, strategy generator, difficulty mapper, prerequisites generator |
| `personas/` | Persona generator, speech pattern definitions |
| `final_report_generator.py` | Aggregates cross-round scores into a holistic report |
| `followup_engine.py` | Real-time follow-up question generation |
| `journey_memory_manager.py` | Stores and retrieves cross-round memory |
| `evaluation.py` | Journey-level evaluation logic |
| `routers/` | FastAPI routes for journey CRUD and round operations |

### `app/modules/`

| Module | Purpose |
|---|---|
| `identity/` | User auth, JWT tokens, user profile CRUD |
| `topics/` | Interview topics — global and user-defined |
| `question_bank/` | Curated questions stored in the DB |
| `questions/` | Per-session dynamic question generation |
| `responses/` | Candidate response submission and storage |
| `sessions/` | Interview session lifecycle (create, start, end, list) |
| `evaluation/` | 7-dimension scoring service and report generation |
| `analytics/` | Aggregated performance analytics per user/topic |
| `coaching/` | AI coaching session CRUD and message routing |
| `training_plans/` | 7-day training plan generation and task tracking |
| `knowledge/` | Knowledge document upload, chunk management, admin search |
| `billing/` | Stripe subscription management |

### `app/adaptive/`
`engine.py` — rolling-average adaptive difficulty with threshold rules (>72 escalate, <55 de-escalate).

### `app/workers/`
APScheduler background jobs — periodic evaluation processing, cleanup tasks.

### `personas/`
YAML/JSON interviewer personality files organised by category:
- `faang/` — e.g., `google_system_design.yaml` (Skeptical Architect archetype)
- `behavioral/` — HR and culture-fit interviewer archetypes
- `startup/` — Fast-paced, generalist startup interviewer archetypes

---

## 📦 Module Reference — Frontend (`apps/web`)

### Route Groups

| Route | Purpose |
|---|---|
| `(auth)/` | Login and signup pages |
| `(dashboard)/dashboard/` | Main dashboard and all sub-pages |
| `(session)/dashboard/sessions/` | Live interview session UI |

### Dashboard Pages

| Page | Purpose |
|---|---|
| `page.tsx` | Home dashboard — score overview, recent sessions, quick-start |
| `analytics/` | Detailed analytics charts (Recharts) per dimension |
| `coach/` | Conversational coaching chat interface |
| `cognitive/` | Cognitive performance metrics view |
| `interview-journey/` | Create journey, view rounds, start round |
| `knowledge/` | Upload and manage knowledge documents for RAG |
| `progress/` | Progress tracker across sessions |
| `sessions/` | Historical session list and detail view |
| `settings/` | User preferences, AI behaviour settings |
| `topics/` | Browse and select practice topics |
| `training/` | Active training plan — view tasks, mark complete |
| `trends/` | Score trend charts over time |

### Feature Modules (`features/`)

| Feature | Purpose |
|---|---|
| `auth/` | Login, signup, token management |
| `onboarding/` | First-run profile setup flow |
| `training/` | Training plan interaction hooks |

---

## 🚀 Getting Started

### Prerequisites
- Node.js 20+
- pnpm 10+
- Python 3.12+
- PostgreSQL 15+ with `pgvector` extension enabled
- `uv` Python package manager
- LiveKit server (run locally with `livekit-server --dev`)

### 1. Clone and install
```bash
git clone <repo-url>
cd braintrain
pnpm install
```

### 2. Backend setup
```bash
cd apps/api
uv sync
cp .env.example .env.development
# Edit .env.development — set GITHUB_TOKEN as minimum
```

### 3. Database
```bash
# Run migrations
uv run alembic upgrade head

# Seed RAG knowledge base
uv run python -m app.ai.rag.ingest
```

### 4. Start all services
```bash
# Terminal 1 — LiveKit
livekit-server --dev

# Terminal 2 — Backend (from apps/api)
uv run uvicorn app.main:app --reload --port 8000

# Terminal 3 — Frontend (from apps/web)
pnpm dev
```

Application runs at `http://localhost:3000`. API docs at `http://localhost:8000/docs`.

---

## 🔑 Environment Variables

All environment variables live in `apps/api/.env.development`.

```env
# ── Azure AI Foundry / GitHub Models (PRIMARY) ──────────────────────────────
GITHUB_TOKEN=ghu_...
GITHUB_MODEL=meta-llama-3.1-70b-instruct
GITHUB_MODELS_BASE_URL=https://models.inference.ai.azure.com

# ── NVIDIA NIM (FALLBACK 2) ──────────────────────────────────────────────────
NVIDIA_API_KEY=nvapi-...
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=meta/llama-3.1-70b-instruct

# ── OpenAI (FALLBACK 3 — also enables LangChain coaching) ───────────────────
OPENAI_API_KEY=sk-...

# ── Groq (AUDIO TRANSCRIPTION) ───────────────────────────────────────────────
GROQ_API_KEY=gsk_...

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/braintrain_api_dev

# ── LiveKit (WebRTC audio rooms) ──────────────────────────────────────────────
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...

# ── Application ───────────────────────────────────────────────────────────────
APP_ENV=development
FRONTEND_URL=http://localhost:3000
JWT_SECRET=...
```

> **Minimum viable setup**: Set `GITHUB_TOKEN` and `DATABASE_URL`. Everything else has a stub fallback.

---

## 🏆 Why BrainTrain is Different

| Feature | ChatGPT | Google Interview Warmup | **BrainTrain** |
|---|---|---|---|
| **Multi-Dimensional Scoring** | No (Generates prose) | No (Keywords only) | **Yes (7 calibrated metrics)** |
| **Longitudinal Tracking** | No (Fresh session every time) | No (One-off) | **Yes (Progress over time)** |
| **Real-time Voice Probing** | No (Text/Voice chatbot) | No (Pre-recorded prompt) | **Yes (Async voice agent)** |
| **Personalised Training Plan** | No | No | **Yes (7-day workout generation)** |
| **Knowledge Base (RAG)** | No | No | **Yes (Semantic + Keyword search)** |
| **Multi-round Journey** | No | No | **Yes (Full hiring loop simulation)** |
| **Adaptive Difficulty** | No | No | **Yes (Score-based auto-adjustment)** |
| **Interviewer Personas** | No | No | **Yes (FAANG, Startup, Behavioral)** |
