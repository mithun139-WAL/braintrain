# BrainTrain Backend — Architecture Documentation

> **Platform Purpose**  
> BrainTrain is a confidence-first interview training platform. It is not a mock interview script runner.
> It is a structured confidence evaluation engine with adaptive progression — built for people who
> know their answers but fail under pressure, freeze in high-stakes interviews, or struggle to
> articulate clearly when it matters most.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Database Schema](#4-database-schema)
5. [Module Breakdown](#5-module-breakdown)
   - [Identity Module](#51-identity-module)
   - [Sessions Module](#52-sessions-module)
   - [Questions Module](#53-questions-module)
   - [Responses Module](#54-responses-module)
   - [AI Module](#55-ai-module)
   - [Evaluation Module](#56-evaluation-module)
   - [Adaptive Engine Module](#57-adaptive-engine-module)
6. [Core Flows](#6-core-flows)
7. [Session Lifecycle State Machine](#7-session-lifecycle-state-machine)
8. [Evaluation Pipeline](#8-evaluation-pipeline)
9. [Adaptive Difficulty Engine](#9-adaptive-difficulty-engine)
10. [API Reference](#10-api-reference)
11. [What Is Stubbed vs Real](#11-what-is-stubbed-vs-real)
12. [What Comes Next](#12-what-comes-next)

---

## 1. System Overview

BrainTrain's backend is a **behaviour-driven evaluation system** built on four architectural layers:

```
┌─────────────────────────────────────────────────┐
│  Layer 4 — Adaptive Policy Layer                │
│  AdaptiveEngineService                          │
│  Reads PerformanceSignals → decides difficulty  │
├─────────────────────────────────────────────────┤
│  Layer 3 — Signal Layer                         │
│  PerformanceSignal (structured output)          │
│  clarityScore, structureScore, depthScore, ...  │
├─────────────────────────────────────────────────┤
│  Layer 2 — Evaluation Layer                     │
│  AnswerEvaluationProvider (AI abstraction)      │
│  StubEvaluationProvider (current)               │
│  ← OpenAIEvaluationProvider (future)            │
├─────────────────────────────────────────────────┤
│  Layer 1 — Session Layer                        │
│  Text + Audio responses from the user           │
└─────────────────────────────────────────────────┘
```

Every design decision traces back to the core thesis:
> *The platform exists to detect, measure, and improve confidence — not just knowledge.*

---

## 2. Technology Stack

| Concern | Technology |
|---|---|
| Runtime | Node.js |
| Framework | NestJS (TypeScript) |
| Database | PostgreSQL |
| ORM | Prisma |
| Auth | JWT + bcrypt + Google OAuth2 + OTP |
| Config | `@nestjs/config` with env-file per environment |
| AI Abstraction | Custom `AnswerEvaluationProvider` interface (DI-injected) |
| Package Manager | pnpm (monorepo) |

---

## 3. Project Structure

```
apps/backend/
├── prisma/
│   ├── schema.prisma              ← Single source of truth for DB shape
│   └── migrations/                ← Auto-generated migration history
│
├── src/
│   ├── app.module.ts              ← Root module wiring
│   ├── main.ts                    ← Bootstrap + global pipes
│   │
│   ├── prisma/                    ← Prisma client wrapper (singleton)
│   │
│   ├── modules/
│   │   ├── identity/              ← Auth: register, login, OTP, Google OAuth
│   │   ├── sessions/              ← Session lifecycle management
│   │   ├── questions/             ← Question generation + orchestration
│   │   ├── responses/             ← Answer submission + ingestion
│   │   ├── ai/                    ← AI abstraction layer (interface + providers)
│   │   │   ├── interfaces/
│   │   │   │   ├── answer-evaluation-provider.interface.ts
│   │   │   │   ├── evaluation-input.interface.ts
│   │   │   │   └── performance-signal.interface.ts
│   │   │   ├── providers/
│   │   │   │   └── stub-evaluation.provider.ts
│   │   │   ├── ai.module.ts
│   │   │   └── ai.tokens.ts
│   │   ├── evaluation/            ← Session analysis + report generation
│   │   │   ├── dto/
│   │   │   │   ├── session-evaluation-response.dto.ts
│   │   │   │   └── evaluation-response.mapper.ts
│   │   │   ├── evaluation.controller.ts
│   │   │   ├── evaluation.service.ts
│   │   │   └── evaluation.module.ts
│   │   └── adaptive/              ← Difficulty transition engine
│   │       ├── adaptive-engine.service.ts
│   │       └── adaptive.module.ts
│   │
│   └── simulation/
│       └── simulate-archetypes.ts  ← Offline engine validation tool
```

---

## 4. Database Schema

### `User`
Stores identity. Supports email/password, phone number, and Google OAuth sign-in.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `email` | String? | Unique, optional |
| `phoneNumber` | String? | Unique, optional |
| `googleId` | String? | Unique, for OAuth |
| `passwordHash` | String? | bcrypt hashed |
| `deletedAt` | DateTime? | Soft delete |

---

### `OtpCode`
Supports passwordless login via OTP (email or phone).

| Field | Notes |
|---|---|
| `identifier` | Email or phone number |
| `code` | bcrypt-hashed 6-digit OTP |
| `expiresAt` | 10 minutes from creation |
| `isUsed` | Prevents replay attacks |
| `attemptCount` | Rate-limiting hook |

---

### `Topic`
The interview subject. Can be global (platform-defined) or user-created.

| Field | Notes |
|---|---|
| `name` | e.g. "React", "System Design", "Leadership" |
| `isGlobal` | Platform topic = true, User topic = false |
| `createdByUserId` | null for global topics |
| `parentTopicId` | Supports subtopic hierarchy |

---

### `InterviewSession`
The central entity. One session = one focused interview on one topic.

| Field | Notes |
|---|---|
| `userId` | Tenant isolation — strictly enforced |
| `topicId` | Topic being interviewed on |
| `mode` | `ONE_ON_ONE_AI`, `GROUP_AI`, `HYBRID` |
| `difficulty` | Base difficulty: `BEGINNER`, `INTERMEDIATE`, `ADVANCED` |
| `adaptive` | If true, AdaptiveEngine drives difficulty per question |
| `durationMinutes` | Intended session length |
| `status` | State machine: see Section 7 |
| `personalityConfig` | JSON — future AI interviewer persona |
| `startedAt` / `endedAt` | Lifecycle timestamps |

---

### `QuestionInstance`
A single question generated within a session. Not reusable across sessions by design.

| Field | Notes |
|---|---|
| `sessionId` | Parent session |
| `content` | The actual question text |
| `difficulty` | Difficulty at which this specific question was asked |
| `sequenceOrder` | 1-indexed; unique per session |

**Max 20 questions per session** (enforced at service layer).

---

### `ResponseInstance`
The user's answer to a single question. **One response per question** (enforced via unique constraint).

| Field | Notes |
|---|---|
| `answerText` | Text answer (optional if audio provided) |
| `audioUrl` | URL to audio recording (optional) |
| `responseTimeMs` | Total time taken to answer |
| `thinkingTimeMs` | Pause before starting to answer |
| `answerLength` | Character count of text answer |
| `clarityScore` | Set by EvaluationService after session analysis |
| `structureScore` | Set by EvaluationService after session analysis |
| `depthScore` | Set by EvaluationService after session analysis |
| `confidenceScore` | Set by EvaluationService after session analysis |
| `communicationScore` | Set by EvaluationService after session analysis |
| `hesitationScore` | Inverse — lower is better (0 = no hesitation) |
| `technicalScore` | null for behavioral questions |
| `overallScore` | Weighted composite. **Primary signal for AdaptiveEngine** |
| `evaluationExplanation` | Human-readable note from the evaluator |

**Key design decision**: Scores are `null` at submission time. They are written by `EvaluationService` after the session completes. This separates the fast submission path from the slow evaluation path.

---

### `EvaluationReport`
Session-level aggregated scores. One report per session (enforced via unique constraint).

| Field | Notes |
|---|---|
| `sessionId` | Parent session (unique) |
| `overallScore` | Average of per-response `overallScore` |
| `clarityScore` | Average of per-response `clarityScore` |
| `structureScore` | Average of per-response `structureScore` |
| `depthScore` | Average of per-response `depthScore` |
| `confidenceScore` | Average of per-response `confidenceScore` |
| `communicationScore` | Average of per-response `communicationScore` |
| `hesitationScore` | Average of per-response `hesitationScore` |
| `technicalScore` | null for behavioral sessions |
| `feedbackSummary` | One-paragraph feedback text |
| `improvementSuggestions` | JSON: keyed by dimension (structure, confidence, etc.) |

---

## 5. Module Breakdown

### 5.1 Identity Module

**Path**: `src/modules/identity/`

Handles all authentication flows. Every other module trusts `req.user.userId` from the decoded JWT — no other trust mechanism exists.

**Auth Methods**:

| Method | Endpoint | Description |
|---|---|---|
| Email/Password Register | `POST /auth/register` | Creates user, returns JWT |
| Email/Password Login | `POST /auth/login` | Validates credentials, returns JWT |
| OTP Request | `POST /auth/otp/request` | Generates 6-digit OTP (hashed in DB), rate-limited to 1/60s |
| OTP Verify | `POST /auth/otp/verify` | Validates OTP, creates user if new, returns JWT |
| Google OAuth | `POST /auth/google` | Verifies Google ID token, links/creates account, returns JWT |

**Security model**:
- Passwords are bcrypt-hashed (salt rounds: 10)
- OTPs are bcrypt-hashed before storage (prevents DB read attacks)
- OTPs expire in 10 minutes
- JWTs are signed and stateless
- All protected routes use `JwtAuthGuard` with `userId` extracted from token payload

---

### 5.2 Sessions Module

**Path**: `src/modules/sessions/`

Manages the full lifecycle of an `InterviewSession`. Enforces tenant isolation on every query — `userId` from JWT is always part of the `WHERE` clause.

**Key behaviours**:
- Topic access is validated: user must own the topic or topic must be global
- Sessions are created with status `CREATED` — never `ACTIVE` directly
- State transitions are enforced (cannot skip states)
- Soft delete support via `deletedAt`

**Endpoints**:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/sessions` | Create a new session |
| `GET` | `/sessions/:id` | Fetch session by ID (must belong to user) |
| `PUT` | `/sessions/:id/start` | `CREATED → ACTIVE` |
| `PUT` | `/sessions/:id/complete` | `ACTIVE → COMPLETED` |

---

### 5.3 Questions Module

**Path**: `src/modules/questions/`

Generates the next question in a session. Integrates with the AdaptiveEngine when `session.adaptive = true`.

**Logic flow**:
1. Validate session is `ACTIVE` and belongs to user
2. Count existing questions (enforce max 20)
3. Determine difficulty:
   - If `adaptive = true` → ask `AdaptiveEngineService.determineNextDifficulty(sessionId)`
   - If `adaptive = false` → use session's base difficulty
4. Generate question content (currently stubbed)
5. Persist `QuestionInstance` with `sequenceOrder`

**Stub**: Question content is currently a template string. Real implementation will call the AI provider with topic + difficulty context.

---

### 5.4 Responses Module

**Path**: `src/modules/responses/`

Handles answer submission for a specific question.

**Validation chain**:
1. Question must exist and belong to the requesting user (via nested session ownership)
2. Session must be `ACTIVE`
3. No duplicate response for the same question (unique constraint + service guard)

**What is stored at submission time**:
- `answerText`, `audioUrl`, `responseTimeMs`, `thinkingTimeMs`, `answerLength`
- All signal scores (`clarityScore`, `overallScore`, etc.) are **null** — set later by EvaluationService

---

### 5.5 AI Module

**Path**: `src/modules/ai/`

The architectural boundary between domain logic and AI intelligence. **Nothing outside this module knows which AI provider is active.**

#### Core Interface: `AnswerEvaluationProvider`

```typescript
interface AnswerEvaluationProvider {
    evaluate(input: EvaluationInput): Promise<PerformanceSignal>;
}
```

#### Input: `EvaluationInput`

```typescript
interface EvaluationInput {
    question: string;
    text?: string;           // Text answer
    audioUrl?: string;       // Audio answer URL (future: Whisper)
    questionType: 'behavioral' | 'technical';
    difficulty: DifficultyLevel;
}
```

#### Output: `PerformanceSignal`

```typescript
interface PerformanceSignal {
    clarityScore: number;        // 0–100: coherence and ease of understanding
    structureScore: number;      // 0–100: STAR / logical flow
    depthScore: number;          // 0–100: quality and completeness
    confidenceScore: number;     // 0–100: assertiveness and tone
    communicationScore: number;  // 0–100: filler density, pacing
    hesitationScore: number;     // 0–100: INVERSE — lower is better
    technicalScore: number|null; // 0–100: factual correctness (null for behavioral)
    overallScore: number;        // 0–100: weighted composite
    explanation: string;
}
```

#### DI Token: `AI_EVALUATION_PROVIDER`

Providers are bound in `ai.module.ts`:

```typescript
{
    provide: AI_EVALUATION_PROVIDER,
    useClass: StubEvaluationProvider,  // ← Change this one line to swap providers
}
```

#### Current Provider: `StubEvaluationProvider`

A deterministic, zero-cost implementation using text heuristics:

| Score | Heuristic |
|---|---|
| `clarityScore` | Word count bands (short=30, ideal=75, rambling=65) |
| `structureScore` | STAR keyword detection: `situation`, `task`, `action`, `result`, `because`, `therefore`, `finally` (base 30, +10 per keyword) |
| `depthScore` | Word count: <20=25, <80=55, <200=80, 200+=90 |
| `confidenceScore` | Hedge phrase detection: `i think`, `i guess`, `maybe`, etc. (base 80, -10 per hedge, floor 30) |
| `communicationScore` | Filler density: `um`, `uh`, `like`, `you know`, `basically` |
| `hesitationScore` | Filler count + ellipsis patterns × 15 (cap 100) |
| `technicalScore` | Technical vocabulary: `algorithm`, `cache`, `api`, `async`, etc. |
| `overallScore` | Weighted sum (different weights for behavioral vs technical) |

**Behavioral weighting**:
```
20% clarity + 20% structure + 20% depth + 20% confidence + 10% communication + 10% (100 - hesitation)
```

**Technical weighting**:
```
20% clarity + 15% structure + 20% depth + 15% confidence + 10% communication + 20% technical - (hesitation × 10%)
```

---

### 5.6 Evaluation Module

**Path**: `src/modules/evaluation/`

Orchestrates the full evaluation pipeline when a session is completed.

**`POST /sessions/:id/evaluation/analyze`**:
1. Validate session is `COMPLETED` and belongs to user
2. Check no evaluation already exists (idempotent guard → 409)
3. Load all questions + responses for the session
4. Validate all questions have responses
5. For each question, call `aiProvider.evaluate(input)` sequentially
6. Persist per-response `PerformanceSignal` scores to `ResponseInstance`
7. Aggregate all signals → session-level averages
8. Atomically create `EvaluationReport` + transition session to `ANALYZED`
9. Return `SessionEvaluationResponseDto`

**`GET /sessions/:id/evaluation`**:
- Fetches an existing `EvaluationReport` for a session
- Returns the same `SessionEvaluationResponseDto`
- Returns 404 if session hasn't been analyzed yet

#### Response DTO: `SessionEvaluationResponseDto`

```typescript
{
    sessionId: string;
    overallScore: number;       // 0–100

    summary: string;            // 1–2 sentence feedback

    dimensions: {
        clarity: number;
        structure: number;
        depth: number;
        confidence: number;
        communication: number;
        hesitation: number;     // INVERTED here: 100 = no hesitation (better UX)
        technical: number|null;
    };

    strengths: string[];        // Dimensions scoring ≥ 70
    improvements: string[];     // Actionable suggestions from weak dimensions

    difficultyProgression: {
        startedAt: DifficultyLevel;  // Session base difficulty
        endedAt: DifficultyLevel;    // Difficulty of last question asked
    };

    evaluatedAt: string;        // ISO timestamp
}
```

**Strength detection** (threshold: 70):
> "Clear and coherent communication" / "Well-structured answers (STAR format)" / etc.

**Improvement generation** (triggered below threshold 60):
> structure < 60 → "Use the STAR format..." / confidence < 60 → "Eliminate hedging phrases..."

---

### 5.7 Adaptive Engine Module

**Path**: `src/modules/adaptive/`

Reads signal history and determines the difficulty of the **next** question.

**Algorithm**:

```
1. Fetch session base difficulty
2. Fetch last 3 answered questions with responses
3. If no answered questions → return base difficulty
4. Use difficulty of most recent question as current baseline
5. Filter responses where overallScore is not null (AI-evaluated)
6. If fewer than MIN_SCORED_RESPONSES (2) evaluated → hold (no premature transitions)
7. Compute rolling average of overallScore (last 3)
8. if avg > 72  → increase difficulty
   if avg < 55  → decrease difficulty
   else         → hold
```

**Transition table**:

| Current | Increase | Decrease |
|---|---|---|
| BEGINNER | INTERMEDIATE | BEGINNER (floor) |
| INTERMEDIATE | ADVANCED | BEGINNER |
| ADVANCED | ADVANCED (ceiling) | INTERMEDIATE |

**Tuned thresholds** (validated via `simulate-archetypes.ts`):

| Threshold | Value | Rationale |
|---|---|---|
| `INCREASE_ABOVE` | 72 | Was 75 — strong candidates no longer stall at the boundary |
| `DECREASE_BELOW` | 55 | Was 50 — catches genuinely weak performers averaging ~52 |
| `MIN_SCORED_RESPONSES` | 2 | Prevents transitions before sufficient signal exists |

---

## 6. Core Flows

### Complete Interview Flow

```
POST /auth/register or /auth/login
        ↓ JWT token returned
POST /sessions  { topicId, mode, difficulty, adaptive: true, durationMinutes }
        ↓ session.status = CREATED
PUT  /sessions/:id/start
        ↓ session.status = ACTIVE, startedAt = now

  [Loop: repeat for each question]
  POST /sessions/:id/questions/next
        ↓ AdaptiveEngine calculates difficulty
        ↓ Question generated, saved with sequenceOrder + difficulty
  POST /questions/:questionId/responses
        ↓ Answer saved (scores null at this point)
  [End Loop]

PUT  /sessions/:id/complete
        ↓ session.status = COMPLETED, endedAt = now
POST /sessions/:id/evaluation/analyze
        ↓ AI evaluates each answer → PerformanceSignal per response
        ↓ Per-response scores persisted to ResponseInstance
        ↓ Session-level aggregation computed
        ↓ EvaluationReport created
        ↓ session.status = ANALYZED
        ← SessionEvaluationResponseDto returned

GET  /sessions/:id/evaluation
        ← Same DTO (cached, no re-evaluation)
```

---

## 7. Session Lifecycle State Machine

```
                   ┌─────────┐
                   │ CREATED │
                   └────┬────┘
                        │  PUT /start
                        ▼
                   ┌────────┐
                   │ ACTIVE │ ←── Questions generated here
                   └────┬───┘     Responses submitted here
                        │  PUT /complete
                        ▼
                  ┌───────────┐
                  │ COMPLETED │ ←── Evaluation triggered here
                  └─────┬─────┘
                        │  POST /evaluation/analyze
                        ▼
                  ┌──────────┐
                  │ ANALYZED │ ←── Report available
                  └──────────┘

  CANCELLED  ← future (timeout, user exit)
```

**State transition rules** (all enforced at service layer):
- Cannot start a non-`CREATED` session
- Cannot complete a non-`ACTIVE` session
- Cannot analyze a non-`COMPLETED` session
- Cannot analyze twice (409 Conflict)

---

## 8. Evaluation Pipeline

```
Session COMPLETED
        │
        ▼
EvaluationService.analyzeSession()
        │
        ├── For each QuestionInstance (ordered by sequenceOrder):
        │       │
        │       ├── Build EvaluationInput {
        │       │       question, text, audioUrl,
        │       │       questionType, difficulty
        │       │   }
        │       │
        │       ├── aiProvider.evaluate(input)
        │       │   └── Returns PerformanceSignal
        │       │
        │       └── UPDATE ResponseInstance SET
        │               clarityScore, structureScore, depthScore,
        │               confidenceScore, communicationScore,
        │               hesitationScore, technicalScore,
        │               overallScore, evaluationExplanation
        │
        ├── aggregateSignals(all signals)
        │   ├── Average each dimension across all responses
        │   ├── Build feedbackSummary (score-band based text)
        │   └── Build improvementSuggestions (keyed by weak dimension)
        │
        └── $transaction([
                CREATE EvaluationReport,
                UPDATE InterviewSession SET status = ANALYZED
            ])
```

**Why per-response scoring matters**:
- Each answer is individually evaluated and scored
- This enables future analytics: *"Your confidence improved from Q1 to Q5"*
- The session report is derived from individual records — no information is lost

---

## 9. Adaptive Difficulty Engine

### What It Reads
`ResponseInstance.overallScore` — the composite AI signal.

### Why not `answerLength` or `responseTime`?
These are **proxy metrics**, not performance metrics. A candidate can write 500 words of confused rambling (long + slow) and score badly — or write 80 words of crisp, structured response and score highly. The old logic wouldn't distinguish these.

`overallScore` is a weighted composite of clarity, structure, depth, confidence, communication, and hesitation — a true performance signal.

### Simulation Results (3 Archetypes)

| Archetype | Avg Score | Final Difficulty | Transitions |
|---|---|---|---|
| 🟢 Strong (STAR, no hedges, 150+ words) | 73.8 | ADVANCED | 2 — BEGINNER→INTERMEDIATE→ADVANCED |
| 🔴 Struggling (short, hedges, fillers) | 53.6 | BEGINNER | 0 — decrease triggered at Q5 |
| 🟡 Inconsistent (alternates strong/weak) | 63.4 | BEGINNER | 0 — neutral band, no reward for inconsistency |

Run simulation anytime: `npm run simulate:archetypes`

---

## 10. API Reference

All routes (except auth) require `Authorization: Bearer <JWT>` header.

### Auth

| Method | Endpoint | Body | Response |
|---|---|---|---|
| POST | `/auth/register` | `{ email?, phoneNumber?, password? }` | `{ access_token, user }` |
| POST | `/auth/login` | `{ email?, phoneNumber?, password }` | `{ access_token, user }` |
| POST | `/auth/otp/request` | `{ identifier }` | `{ message }` |
| POST | `/auth/otp/verify` | `{ identifier, code }` | `{ access_token, user }` |
| POST | `/auth/google` | `{ token }` | `{ access_token, user }` |

### Sessions

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions` | Create session |
| GET | `/sessions/:id` | Get session |
| PUT | `/sessions/:id/start` | `CREATED → ACTIVE` |
| PUT | `/sessions/:id/complete` | `ACTIVE → COMPLETED` |

### Questions

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions/:sessionId/questions/next` | Generate next question |

### Responses

| Method | Endpoint | Body | Description |
|---|---|---|---|
| POST | `/questions/:questionId/responses` | `{ answerText?, audioUrl?, responseTimeMs, thinkingTimeMs }` | Submit answer |

### Evaluation

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions/:sessionId/evaluation/analyze` | Run evaluation (session must be COMPLETED) |
| GET | `/sessions/:sessionId/evaluation` | Fetch existing evaluation report |

---

## 11. What Is Stubbed vs Real

| Component | Status | Notes |
|---|---|---|
| Auth (JWT, bcrypt, OTP, Google) | ✅ Real | Fully implemented |
| Session lifecycle | ✅ Real | State machine enforced |
| Question sequencing | ✅ Real | Order + adaptive hook implemented |
| Response ingestion | ✅ Real | Validation + persistence complete |
| AI Provider interface | ✅ Real | `AnswerEvaluationProvider` — swap-ready |
| Evaluation pipeline | ✅ Real | Per-response + aggregated, persisted |
| Adaptive engine | ✅ Real | Signal-driven, tuned thresholds |
| OTP delivery (SMS/Email) | 🔶 Stub | Logs to console — needs provider |
| Question generation content | 🔶 Stub | Template string — needs LLM call |
| OpenAI / real LLM evaluation | 🔶 Stub | `StubEvaluationProvider` is active |
| Audio transcription | 🔶 Not built | `audioUrl` stored, not processed |

---

## 12. What Comes Next

### Immediate (Production Surface Hardening)
- [ ] `GET /sessions` — list user's sessions with pagination
- [ ] `GET /sessions/:id/questions` — list questions in a session
- [ ] OTP delivery via real SMS/email provider (Twilio, SendGrid)
- [ ] Global error filter / consistent error response shape

### Intelligence Layer
- [ ] `OpenAIEvaluationProvider` — implement `AnswerEvaluationProvider` with GPT
- [ ] Real question generation via LLM (replace stub in `QuestionsService`)
- [ ] Audio transcription via Whisper API → feed transcript into evaluation

### Analytics Layer (enabled by current schema)
- [ ] `GET /users/me/analytics` — avg scores over time, confidence trend
- [ ] Per-dimension trend: "Your structure score improved 15 points over 5 sessions"
- [ ] Topic weakness detection: "Leadership answers score lower than Technical"

### Platform Expansion
- [ ] Topic management: `POST /topics`, `GET /topics`
- [ ] Question bank: user-submitted questions, AI deduplication
- [ ] Group sessions: multiple users in one session (multi-agent design)
- [ ] Async evaluation queue (for scale — evaluate in background after COMPLETED)
