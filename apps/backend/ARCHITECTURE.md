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
   - [Question Bank Module](#54-question-bank-module)
   - [Responses Module](#55-responses-module)
   - [AI Module](#56-ai-module)
   - [Evaluation Module](#57-evaluation-module)
   - [Adaptive Engine Module](#58-adaptive-engine-module)
   - [Topics Module](#59-topics-module)
   - [Analytics Module](#510-analytics-module)
   - [Usage Module](#511-usage-module)
   - [EvaluationJob Module](#512-evaluationjob-module)
6. [Core Flows](#6-core-flows)
7. [Session Lifecycle State Machine](#7-session-lifecycle-state-machine)
8. [Evaluation Pipeline](#8-evaluation-pipeline)
9. [Adaptive Difficulty Engine](#9-adaptive-difficulty-engine)
10. [Database Index Strategy](#10-database-index-strategy)
11. [API Reference](#11-api-reference)
12. [What Is Stubbed vs Real](#12-what-is-stubbed-vs-real)
13. [Phase 3 — Production Hardening](#13-phase-3--production-hardening)

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
│  clarityScore, structureScore, depthScore,      │
│  pressureScore, thinkingDepthScore, ...         │
├─────────────────────────────────────────────────┤
│  Layer 2 — Evaluation Layer                     │
│  AnswerEvaluationProvider (AI abstraction)      │
│  OpenAIEvaluationProvider (active, gpt-4o-mini) │
│  StubEvaluationProvider   (offline fallback)    │
├─────────────────────────────────────────────────┤
│  Layer 1 — Session Layer                        │
│  Text + Audio responses + Behavioral timing     │
└─────────────────────────────────────────────────┘
```

**Phase 3 addition — Async Evaluation Layer:**

```
PUT /complete
    ↓
EvaluationJob (PENDING) created atomically
    ↓
EvaluationWorker (cron poll, every 10s)
    ↓ exponential backoff (30s → 2min → 10min)
    ↓ zombie recovery (every 5min, resets stuck jobs)
OpenAIEvaluationProvider (gpt-4o-mini)
    ↓
EvaluationReport persisted
    ↓
EvaluationJob → COMPLETED
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
| AI Evaluation | `OpenAIEvaluationProvider` (gpt-4o-mini, env-driven swap) |
| AI Question Gen | `OpenAIQuestionGenerationProvider` (gpt-4o-mini, auto-saves to QuestionBank) |
| Scheduling | `@nestjs/schedule` — evaluation worker + usage reset cron |
| Rate Limiting | `@nestjs/throttler` — 30 req/60s per IP globally |
| Package Manager | pnpm (monorepo) |

---

## 3. Project Structure

```
apps/backend/
├── prisma/
│   ├── schema.prisma              ← Single source of truth for DB shape + indexes
│   └── migrations/                ← Auto-generated migration history
│
├── src/
│   ├── app.module.ts              ← Root module (ThrottlerModule, UsageModule, WorkerModule)
│   ├── main.ts                    ← Bootstrap + GlobalExceptionFilter + CORS
│   │
│   ├── filters/
│   │   └── global-exception.filter.ts  ← Standardised { code, message, details? } errors
│   │
│   ├── prisma/                    ← Prisma client wrapper (singleton)
│   │
│   ├── workers/
│   │   └── evaluation.worker.ts  ← Cron-based eval processor + zombie recovery
│   │
│   ├── modules/
│   │   ├── identity/              ← Auth + User Profile + Skill Preferences
│   │   ├── sessions/              ← Session lifecycle management + LIST
│   │   ├── topics/                ← Topic CRUD (global + user-owned)
│   │   ├── questions/             ← Question generation (bank-first → LLM → stub)
│   │   ├── question-bank/         ← Reusable question bank CRUD
│   │   ├── responses/             ← Answer submission + timing ingestion
│   │   ├── usage/                 ← SaaS plan limits + monthly reset cron
│   │   ├── evaluation-job/        ← Job CRUD + backoff + zombie recovery helpers
│   │   ├── ai/                    ← AI abstraction layer
│   │   │   ├── interfaces/
│   │   │   │   ├── answer-evaluation-provider.interface.ts
│   │   │   │   ├── question-generation-provider.interface.ts
│   │   │   │   ├── evaluation-input.interface.ts
│   │   │   │   └── performance-signal.interface.ts
│   │   │   ├── providers/
│   │   │   │   ├── openai-evaluation.provider.ts      ← gpt-4o-mini, retry, backoff
│   │   │   │   ├── stub-evaluation.provider.ts
│   │   │   │   ├── openai-question-generation.provider.ts
│   │   │   │   └── stub-question-generation.provider.ts
│   │   │   ├── prompts/
│   │   │   │   ├── evaluation.prompts.ts              ← v1.0.0, 6-field schema
│   │   │   │   └── question-generation.prompts.ts
│   │   │   ├── ai.module.ts       ← Env-driven DI (OPENAI_API_KEY → real / absent → stub)
│   │   │   └── ai.tokens.ts
│   │   ├── evaluation/            ← Session analysis + report generation
│   │   ├── adaptive/              ← Difficulty transition engine
│   │   └── analytics/             ← Cross-session insights + progression endpoint
│   │
│   └── simulation/
│       └── simulate-archetypes.ts  ← Offline engine validation tool
```

---

## 4. Database Schema

### `User`

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `email` | String? | Unique |
| `phoneNumber` | String? | Unique |
| `googleId` | String? | Unique |
| `planType` | String | `FREE` \| `PRO` (default: FREE) |
| `monthlySessionCount` | Int | Incremented on session create |
| `monthlyEvaluationCredits` | Int | Decremented on LLM evaluation |
| `usagePeriodStart` | DateTime | Reset monthly by cron |
| `deletedAt` | DateTime? | Soft delete |

---

### `QuestionBank`

| Field | Notes |
|---|---|
| `content` | The question text |
| `topicId` | Associated topic |
| `difficulty` | `BEGINNER` \| `INTERMEDIATE` \| `ADVANCED` |
| `questionType` | `behavioral` \| `technical` |
| `source` | `HUMAN` (manual) \| `GENERATED` (LLM auto-saved) |
| `usageCount` | Incremented each time picked during session |

---

### `InterviewSession`

| Field | Notes |
|---|---|
| `userId` | Tenant isolation — strictly enforced |
| `topicId` | Topic being interviewed on |
| `status` | State machine: `CREATED → ACTIVE → COMPLETED → ANALYZED` |
| `interviewLevel` | `SCREENING` \| `TECHNICAL_L1` \| `TECHNICAL_L2` \| `HR` \| `SYSTEM_DESIGN` |
| `difficulty` | Base difficulty |
| `adaptive` | If true, AdaptiveEngine drives difficulty per question |

---

### `EvaluationReport`

| Field | Notes |
|---|---|
| `overallScore` | **Server-computed weighted aggregate** (not LLM-supplied) |
| `clarityScore` … `communicationScore` | LLM-scored (6 content dimensions) |
| `pressureScore` | Server-computed from `responseTimeMs` timing curve |
| `thinkingDepthScore` | Server-computed from `thinkingTimeMs` timing curve |
| `promptVersion` | e.g. `v1.0.0` — for score traceability across prompt changes |
| `modelUsed` | e.g. `gpt-4o-mini`, `stub` |
| `inputTokens` / `outputTokens` / `estimatedCostUsd` | Billing intelligence |

---

### `EvaluationJob`

| Field | Notes |
|---|---|
| `sessionId` | Unique — one job per session |
| `status` | `PENDING → PROCESSING → COMPLETED \| FAILED` |
| `attempts` | Current attempt count (max 3) |
| `nextRetryAt` | NULL = ready now. Set for exponential backoff (30s/2min/10min) |
| `evaluationStartedAt` | Used by zombie recovery (stuck > 10min → reset to PENDING) |

---

## 5. Module Breakdown

### 5.1 Identity Module

**Path**: `src/modules/identity/`

**Auth Endpoints** (public):

| Method | Endpoint | Description |
|---|---|---|
| POST | `/identity/register` | Creates user, returns JWT |
| POST | `/identity/login` | Validates credentials, returns JWT |
| POST | `/identity/request-otp` | Generates 6-digit OTP (hashed, rate-limited 1/60s) |
| POST | `/identity/verify-otp` | Validates OTP, creates user if new, returns JWT |
| POST | `/identity/google` | Verifies Google ID token, links/creates account |

**Profile Endpoints** (JWT-protected):

| Method | Endpoint | Description |
|---|---|---|
| GET | `/identity/me` | Full profile with skill preferences + plan info |
| PUT | `/identity/me` | Update `displayName`, `bio`, `avatarUrl` |
| GET | `/identity/skill-tags` | List global skill tag catalog |
| POST | `/identity/me/skills` | Upsert `(skillTagId, level)` preference |
| DELETE | `/identity/me/skills/:skillTagId` | Remove skill preference |

---

### 5.2 Sessions Module

**Path**: `src/modules/sessions/`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions` | Create session (usage limit checked first) |
| GET | `/sessions` | List user sessions (paginated, optional `?status=&page=&limit=`) |
| GET | `/sessions/:id` | Fetch session by ID |
| PUT | `/sessions/:id/start` | `CREATED → ACTIVE` |
| PUT | `/sessions/:id/complete` | `ACTIVE → COMPLETED` + creates `EvaluationJob(PENDING)` atomically |
| GET | `/sessions/:id/status` | Poll evaluation job status (for frontend polling) |

**`GET /sessions/:id/status` response**:
```json
{ "sessionStatus": "COMPLETED", "evaluationStatus": "PROCESSING", "sessionId": "..." }
```

---

### 5.3 Questions Module

**Path**: `src/modules/questions/`

Generates the next question using **bank-first → LLM → stub** selection:

1. Validate session is `ACTIVE` and belongs to user
2. Count existing questions (enforce max 20)
3. Determine difficulty (adaptive or static)
4. **Try `QuestionBankService.pickQuestion()`** — bank question if available
5. **Fall back to `OpenAIQuestionGenerationProvider`** — LLM generates + auto-saves to bank
6. Final fallback to `StubQuestionGenerationProvider`
7. Persist `QuestionInstance`

---

### 5.4 Question Bank Module

**Path**: `src/modules/question-bank/`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/question-bank` | Contribute a human question (`source: HUMAN`) |
| GET | `/question-bank?topicId=&difficulty=` | List questions |
| GET | `/question-bank/:id` | Fetch a single question |

LLM-generated questions are auto-saved with `source: GENERATED` and `createdByUserId: null`.

---

### 5.5 Responses Module

**Path**: `src/modules/responses/`

| Method | Endpoint | Body | Description |
|---|---|---|---|
| POST | `/questions/:questionId/responses` | `{ answerText?, audioUrl?, responseTimeMs, thinkingTimeMs }` | Submit answer |

`responseTimeMs` and `thinkingTimeMs` flow directly into server-computed `pressureScore` and `thinkingDepthScore`.

---

### 5.6 AI Module

**Path**: `src/modules/ai/`

#### Env-Driven Provider Selection

```
OPENAI_API_KEY set       → OpenAIEvaluationProvider + OpenAIQuestionGenerationProvider
OPENAI_API_KEY absent    → StubEvaluationProvider + StubQuestionGenerationProvider
```

Zero code changes to swap. Logged at boot:
```
AI Providers: OpenAI (gpt-4o-mini) | Prompt: v1.0.0
```

#### Scoring Architecture

**LLM scores** (6 content dimensions only):
- `clarityScore`, `structureScore`, `depthScore`, `confidenceScore`, `communicationScore`, `technicalScore`

**Server-computed** (deterministic, not LLM):
- `pressureScore` — timing curve from `responseTimeMs` (peak: 15–45s)
- `thinkingDepthScore` — timing curve from `thinkingTimeMs` (peak: 4–12s)
- `overallScore` — weighted server-side formula (behavioral vs technical weights)

#### Evaluation Prompt (v1.0.0)

- Model: `gpt-4o-mini`
- Temperature: `0.1`
- Max tokens: `150`
- `response_format: json_object`
- Calibration anchors: `50=avg, 70=strong, 85+=exceptional`
- Difficulty bias: `ADVANCED` → +4 to all content scores before clamp

#### Retry + Fallback

```
Attempt 1 → parse + validate 6-field JSON
Attempt 2 → retry if malformed
Fallback   → StubEvaluationProvider (degraded: true in __meta)
```

---

### 5.7 Evaluation Module

**Path**: `src/modules/evaluation/`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions/:id/evaluation/analyze` | Manual trigger (admin/debug) |
| GET | `/sessions/:id/evaluation` | Fetch saved evaluation report |

#### Response DTO

```typescript
{
  sessionId: string;
  overallScore: number;         // server-computed weighted aggregate
  summary: string;
  modelUsed: string;            // "gpt-4o-mini" | "stub"
  promptVersion: string;        // "v1.0.0"
  estimatedCostUsd: number;

  dimensions: {
    clarity: number;
    structure: number;
    depth: number;
    confidence: number;
    communication: number;
    technical: number | null;
    pressure: number;           // computed from responseTimeMs
    thinkingDepth: number;      // computed from thinkingTimeMs
  };

  improvements: {
    structure?: string[];
    confidence?: string[];
    depth?: string[];
    communication?: string[];
    pace?: string[];            // from pressureScore < 50
    composure?: string[];       // from thinkingDepthScore < 50
  };
}
```

---

### 5.8 Adaptive Engine Module

**Path**: `src/modules/adaptive/`

Reads `overallScore` (server-computed weighted aggregate) to drive difficulty transitions.

| Threshold | Value |
|---|---|
| `INCREASE_ABOVE` | 72 |
| `DECREASE_BELOW` | 55 |
| `MIN_SCORED_RESPONSES` | 2 |

Uses smoothed average of last 3 responses to prevent volatility.

---

### 5.9 Topics Module

**Path**: `src/modules/topics/`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/topics` | Create user-owned topic |
| GET | `/topics` | List global + user-owned topics |
| GET | `/topics/:id` | Get single topic |
| DELETE | `/topics/:id` | Soft-delete (owner only) |

---

### 5.10 Analytics Module

**Path**: `src/modules/analytics/`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/me` | Cross-session trend + improvement delta + per-topic |
| GET | `/analytics/progression` | Score delta between last 2 sessions ("dopamine loop") |

**`GET /analytics/progression` response**:
```json
{
  "latestScore": 74,
  "previousScore": 61,
  "delta": 13,
  "improved": true,
  "message": "You improved by 13 points since your last session!"
}
```

---

### 5.11 Usage Module

**Path**: `src/modules/usage/`

Enforces SaaS plan limits. Called from `SessionsService.createSession()`.

| Plan | Sessions/month | LLM Evaluation |
|---|---|---|
| FREE | 3 | Stub only (degraded mode) |
| PRO | 20 | Real OpenAI evaluation |

- `checkSessionLimit()` — throws `403 ForbiddenException` if limit reached
- `incrementSessionCount()` — non-blocking post-creation increment
- `resetMonthlyUsage()` — cron (1st of each month, midnight) resets all counters

---

### 5.12 EvaluationJob Module

**Path**: `src/modules/evaluation-job/`

Manages the async evaluation job lifecycle.

| Method | Notes |
|---|---|
| `createJob(sessionId)` | Called atomically when session completes |
| `claimNextPendingJob()` | Transaction: `PENDING` (where `nextRetryAt <= now`) → `PROCESSING` |
| `markCompleted(jobId)` | Sets `COMPLETED + evaluationCompletedAt` |
| `markFailed(jobId, error)` | Increments attempts. Sets exponential `nextRetryAt`. After 3 → `FAILED` permanently |
| `recoverZombieJobs()` | Resets `PROCESSING` jobs stuck > 10min back to `PENDING` with 30s delay |

---

## 6. Core Flows

### Complete Interview Flow (Phase 3 — Async)

```
POST /identity/login
        ↓ JWT token
POST /sessions  { topicId, mode, difficulty, adaptive, interviewLevel? }
        ↓ UsageService.checkSessionLimit() → 403 if exceeded
        ↓ session.status = CREATED
        ↓ UsageService.incrementSessionCount() (non-blocking)
PUT  /sessions/:id/start
        ↓ session.status = ACTIVE

  [Loop: repeat per question]
  POST /sessions/:id/questions/next
        ↓ QuestionBank.pickQuestion()  ← bank hit (zero cost)
        ↓ OpenAIQuestionGenerationProvider  ← LLM if bank miss + auto-saves to bank
        ↓ StubQuestionGenerationProvider    ← final fallback
  POST /questions/:questionId/responses  { answerText, responseTimeMs, thinkingTimeMs }
  [End Loop]

PUT  /sessions/:id/complete
        ↓ session.status = COMPLETED
        ↓ EvaluationJob(PENDING) created atomically ← non-blocking
        ↓ API responds 200 immediately

[Background — EvaluationWorker polls every 10s]
        ↓ claimNextPendingJob() (transaction, atomic)
        ↓ Credit check: PRO + credits > 0 → OpenAI, else → stub
        ↓ Per-response: LLM scores 6 dimensions; server computes pressure + thinkingDepth + overall
        ↓ EvaluationReport created
        ↓ EvaluationJob → COMPLETED

GET  /sessions/:id/status       ← frontend polls until evaluationStatus = COMPLETED
GET  /sessions/:id/evaluation   ← fetch report
GET  /analytics/me              ← cross-session trend
GET  /analytics/progression     ← dopamine loop delta
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
               │ ACTIVE │ ←── Questions + Responses here
               └────┬───┘
                    │  PUT /complete
                    ▼
              ┌───────────┐     ┌────────────────────────┐
              │ COMPLETED │────→│ EvaluationJob: PENDING  │
              └───────────┘     └────────────┬───────────┘
                                             │  Worker processes
                                             ▼
                                   ┌──────────────────┐
                                   │ EvaluationJob:   │
                                   │ PROCESSING       │
                                   └────────┬─────────┘
                                            │ success
                                            ▼
              ┌──────────┐     ┌────────────────────────┐
              │ ANALYZED │←────│ EvaluationJob: COMPLETED│
              └──────────┘     └────────────────────────┘
```

---

## 8. Evaluation Pipeline

```
Session COMPLETED
        │
        ▼  [atomically in completeSession()]
EvaluationJob(PENDING) created
        │
        ▼  [EvaluationWorker polls every 10s, batch 3 jobs/tick]
claimNextPendingJob() — atomic transaction (prevents double-claim)
        │
        ▼  [Credit check]
PRO + credits > 0? → OpenAIEvaluationProvider
            else  → StubEvaluationProvider (degraded mode)
        │
        ├── For each QuestionInstance (ordered by sequenceOrder):
        │       ├── Build EvaluationInput { question, text, responseTimeMs, thinkingTimeMs }
        │       ├── LLM → { clarityScore, structureScore, depthScore,
        │       │            confidenceScore, communicationScore, technicalScore }
        │       │   (retry once if JSON malformed; fallback to stub after 2 failures)
        │       ├── Server-compute: pressureScore(responseTimeMs), thinkingDepthScore(thinkingTimeMs)
        │       ├── Server-compute: overallScore (weighted formula per questionType)
        │       │     Behavioral: content 45% + confidence 20% + communication 15% + timing 10%
        │       │     Technical:  content 45% + technical 30% + communication 10% + timing 10%
        │       ├── ADVANCED difficulty: +4 boost to all content scores (fairness)
        │       └── UPDATE ResponseInstance SET all scores
        │
        ├── aggregateSignals(all responses) → session-level averages
        │
        └── $transaction([
                CREATE EvaluationReport { all scores, promptVersion, modelUsed, costFields },
                UPDATE InterviewSession SET status = ANALYZED
            ])

On failure:
  attempt 1 → PENDING, retry in 30s
  attempt 2 → PENDING, retry in 2min
  attempt 3 → FAILED permanently
  zombie     → recoverZombieJobs() (every 5min): stuck PROCESSING > 10min → PENDING + 30s delay
  crash-after-save → ConflictException caught → markCompleted() (idempotent recovery)
```

---

## 9. Adaptive Difficulty Engine

### Algorithm
```
1. Fetch session base difficulty
2. Fetch last 3 answered questions with responses (explicit ORDER BY createdAt DESC LIMIT 3)
3. If no answered questions → return base difficulty
4. Filter responses where overallScore is not null
5. If fewer than MIN_SCORED_RESPONSES (2) evaluated → hold
6. Compute rolling average of overallScore (last 3)
7. if avg > 72  → increase difficulty (BEGINNER→INTERMEDIATE, INTERMEDIATE→ADVANCED)
   if avg < 55  → decrease difficulty
   else         → hold
```

Smoothed average over last 3 responses prevents single-question volatility.

---

## 10. Database Index Strategy

Every index is motivated by a specific query pattern.

### `InterviewSession`

| Index | Query it serves |
|---|---|
| `(userId, status, deletedAt)` | `GET /sessions?status=COMPLETED` — hot path for every user |
| `(userId, createdAt)` | Analytics trend queries (order by date) |
| `(topicId, userId)` | Per-topic session breakdown in analytics |

### `EvaluationJob`

| Index | Query it serves |
|---|---|
| `(status, nextRetryAt, createdAt)` | Worker claim: `WHERE status=PENDING AND (nextRetryAt IS NULL OR nextRetryAt <= now())` |
| `(status, evaluationStartedAt)` | Zombie recovery: `WHERE status=PROCESSING AND evaluationStartedAt < 10min ago` |

### `QuestionBank`

| Index | Query it serves |
|---|---|
| `(topicId, difficulty, deletedAt)` | Bank-first question selection — executed on every question generation |
| `(source, topicId)` | Filter HUMAN vs GENERATED questions for analytics / admin |

### `EvaluationReport`

| Index | Query it serves |
|---|---|
| `(createdAt)` | Cross-session trend sorted by date |
| `(modelUsed, createdAt)` | Billing intelligence: cost per model over time |

### `OtpCode`

| Index | Query it serves |
|---|---|
| `(identifier, isUsed, expiresAt)` | OTP validation: find active, non-expired code for identifier |

### `QuestionInstance`

| Index | Query it serves |
|---|---|
| `(sessionId, sequenceOrder, deletedAt)` | Load all questions for a session in order (most common query) |

### `ResponseInstance`

| Index | Query it serves |
|---|---|
| `(questionId, overallScore)` | Adaptive engine reads last N overallScore values per session |

---

## 11. API Reference

All routes except auth endpoints require `Authorization: Bearer <JWT>` header.
All errors return `{ code, message, details? }` via `GlobalExceptionFilter`.
Global rate limit: **30 requests / 60 seconds per IP**.

### Identity

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/identity/register` | — | Register |
| POST | `/identity/login` | — | Login |
| POST | `/identity/request-otp` | — | Request OTP |
| POST | `/identity/verify-otp` | — | Verify OTP |
| POST | `/identity/google` | — | Google OAuth |
| GET | `/identity/me` | ✅ | Get profile (includes plan + usage) |
| PUT | `/identity/me` | ✅ | Update profile |
| GET | `/identity/skill-tags` | ✅ | List global skill tags |
| POST | `/identity/me/skills` | ✅ | Add skill preference |
| DELETE | `/identity/me/skills/:skillTagId` | ✅ | Remove skill preference |

### Topics

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/topics` | ✅ | Create topic |
| GET | `/topics` | ✅ | List global + user-owned |
| GET | `/topics/:id` | ✅ | Get topic |
| DELETE | `/topics/:id` | ✅ | Soft-delete (owner only) |

### Sessions

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/sessions` | ✅ | Create (plan limit checked) |
| GET | `/sessions` | ✅ | List (paginated, filterable by status) |
| GET | `/sessions/:id` | ✅ | Get session |
| PUT | `/sessions/:id/start` | ✅ | `CREATED → ACTIVE` |
| PUT | `/sessions/:id/complete` | ✅ | `ACTIVE → COMPLETED` + queues eval job |
| GET | `/sessions/:id/status` | ✅ | Poll eval job status |

### Questions

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/sessions/:sessionId/questions/next` | ✅ | Generate next question (bank → LLM → stub) |

### Question Bank

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/question-bank` | ✅ | Add a question |
| GET | `/question-bank?topicId=&difficulty=` | ✅ | List questions |
| GET | `/question-bank/:id` | ✅ | Get question |

### Responses

| Method | Endpoint | Auth | Body | Description |
|---|---|---|---|---|
| POST | `/questions/:questionId/responses` | ✅ | `{ answerText?, audioUrl?, responseTimeMs, thinkingTimeMs }` | Submit answer |

### Evaluation

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/sessions/:sessionId/evaluation/analyze` | ✅ | Manual trigger |
| GET | `/sessions/:sessionId/evaluation` | ✅ | Fetch report |

### Analytics

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/analytics/me` | ✅ | Cross-session trend + improvement delta + per-topic |
| GET | `/analytics/progression` | ✅ | Score delta between last 2 sessions |

---

## 12. What Is Stubbed vs Real

| Component | Status | Notes |
|---|---|---|
| Auth (JWT, bcrypt, OTP, Google) | ✅ Real | Fully implemented |
| User profile (displayName, bio, avatarUrl) | ✅ Real | GET/PUT /identity/me |
| Skill preferences | ✅ Real | Full CRUD |
| Topic CRUD API | ✅ Real | Global + user-owned, subtopic hierarchy |
| Session lifecycle | ✅ Real | State machine enforced |
| Session LIST + pagination | ✅ Real | Filterable by status |
| Interview levels | ✅ Real | Optional field on sessions |
| Question Bank | ✅ Real | Bank-first selection + GENERATED tagging |
| Question sequencing + adaptive hook | ✅ Real | Order + bank-first + adaptive |
| Behavioral tracking (responseTimeMs/thinkingTimeMs) | ✅ Real | Flows into server-computed timing scores |
| Response ingestion | ✅ Real | Validation + persistence |
| AI Provider interface | ✅ Real | `AnswerEvaluationProvider` — env-driven swap |
| OpenAI Evaluation (gpt-4o-mini) | ✅ Real | Active when `OPENAI_API_KEY` set |
| OpenAI Question Generation (gpt-4o-mini) | ✅ Real | Active when `OPENAI_API_KEY` set; auto-saves |
| Async evaluation (EvaluationJob + Worker) | ✅ Real | Non-blocking, retry, zombie recovery |
| SaaS usage limits (FREE/PRO) | ✅ Real | Session caps + monthly reset |
| Global rate limiting | ✅ Real | 30 req/60s per IP |
| Standardised error responses | ✅ Real | `GlobalExceptionFilter` |
| Cross-session analytics | ✅ Real | Trend, improvement delta, per-topic |
| Progression endpoint | ✅ Real | Delta between last 2 sessions |
| OTP delivery (SMS/Email) | ✅ Real | Twilio (SMS) + Nodemailer (SMTP) |
| Audio transcription | 🔶 Not built | `audioUrl` stored, Whisper integration pending |

---

## 13. Phase 3 — Production Hardening

### What Phase 3 Added

| Track | Shipped |
|---|---|
| **Track 1 — Async Eval** | `EvaluationJob` table + cron worker (10s). `completeSession()` atomically creates `PENDING` job. `GET /sessions/:id/status` polling endpoint |
| **Track 2 — OpenAI Evaluation** | `OpenAIEvaluationProvider` — gpt-4o-mini, JSON mode, 6-field schema, retry-once, difficulty bias (+4 ADVANCED), server-computed pressure/thinking/overall. Cost tracking in `EvaluationReport` |
| **Track 3 — OpenAI Question Gen** | `OpenAIQuestionGenerationProvider` — auto-saves to `QuestionBank` with `source=GENERATED` (dataset flywheel). Bank-first → LLM → stub |
| **Track 4 — SaaS Controls** | `UsageService`: FREE (3/mo), PRO (20/mo). Monthly reset cron. `ThrottlerModule` (30/60s per IP). Credit check before LLM call |
| **Track 5 — Observability** | `GlobalExceptionFilter` (`{code, message}` on all errors). CORS. Structured Logger |
| **Track 6 — Product** | `GET /analytics/progression` — dopamine loop score delta |

### Migrations Applied (Phase 3)

| Migration | Changes |
|---|---|
| `phase3_async_evaluation_job` | `EvaluationJob` table, cost fields on `EvaluationReport`, score fields on `ResponseInstance` |
| `phase3_usage_limits` | `planType`, `monthlySessionCount`, `monthlyEvaluationCredits`, `usagePeriodStart` on `User` |
| `phase3_model_used_and_qbank_source` | `modelUsed` on `EvaluationReport`, `source` on `QuestionBank` |
| `phase3_evaluation_job_retry_at` | `nextRetryAt` on `EvaluationJob` |
| `phase3_indexing_strategy` | All database indexes across all 11 models |

### Async Evaluation State Machine

```
PENDING ──[worker claims]──► PROCESSING ──[success]──► COMPLETED
   ▲                              │
   │   [attempts < 3]             │ [failure]
   └──── retry (backoff) ─────────┘
                                  │ [attempts >= 3]
                                  ▼
                               FAILED

Zombie recovery (every 5min):
  PROCESSING stuck > 10min → PENDING + 30s nextRetryAt

Idempotency protection:
  ConflictException on duplicate report → markCompleted() (not markFailed)
```

### Environment Variables

```env
# Required
DATABASE_URL=postgresql://...
JWT_SECRET=...

# AI (leave unset for stub mode)
OPENAI_API_KEY=sk-...

# Optional
FRONTEND_URL=http://localhost:5173    # CORS allow-origin
PORT=3000
```
