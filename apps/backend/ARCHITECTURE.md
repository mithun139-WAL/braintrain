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
│  clarityScore, structureScore, depthScore,      │
│  pressureScore, thinkingDepthScore, ...         │
├─────────────────────────────────────────────────┤
│  Layer 2 — Evaluation Layer                     │
│  AnswerEvaluationProvider (AI abstraction)      │
│  StubEvaluationProvider (current)               │
│  ← OpenAIEvaluationProvider (future)            │
├─────────────────────────────────────────────────┤
│  Layer 1 — Session Layer                        │
│  Text + Audio responses + Behavioral timing     │
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
│   │   ├── identity/              ← Auth + User Profile + Skill Preferences
│   │   ├── sessions/              ← Session lifecycle management + LIST
│   │   ├── topics/                ← Topic CRUD (global + user-owned)
│   │   ├── questions/             ← Question generation (bank-first + stub fallback)
│   │   ├── question-bank/         ← Reusable question bank CRUD
│   │   ├── responses/             ← Answer submission + timing ingestion
│   │   ├── ai/                    ← AI abstraction layer (interface + providers)
│   │   │   ├── interfaces/
│   │   │   │   ├── answer-evaluation-provider.interface.ts
│   │   │   │   ├── evaluation-input.interface.ts  ← includes responseTimeMs/thinkingTimeMs
│   │   │   │   └── performance-signal.interface.ts ← includes pressureScore/thinkingDepthScore
│   │   │   ├── providers/
│   │   │   │   └── stub-evaluation.provider.ts
│   │   │   ├── ai.module.ts
│   │   │   └── ai.tokens.ts
│   │   ├── evaluation/            ← Session analysis + report generation
│   │   ├── adaptive/              ← Difficulty transition engine
│   │   └── analytics/             ← Cross-session insights + trend analytics
│   │
│   └── simulation/
│       └── simulate-archetypes.ts  ← Offline engine validation tool
```

---

## 4. Database Schema

### `User`
Identity + profile fields. Supports email/password, phone number, and Google OAuth sign-in.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `email` | String? | Unique, optional |
| `phoneNumber` | String? | Unique, optional |
| `googleId` | String? | Unique, for OAuth |
| `passwordHash` | String? | bcrypt hashed |
| `displayName` | String? | User's display name |
| `bio` | String? | Short bio |
| `avatarUrl` | String? | Profile image URL |
| `deletedAt` | DateTime? | Soft delete |

---

### `SkillTag`
Global catalog of skill labels (e.g., "React", "System Design", "Leadership").

| Field | Notes |
|---|---|
| `name` | Unique skill name |
| `isGlobal` | Platform-defined = true |

---

### `UserSkillPreference`
Join table — user's self-declared skill proficiency.

| Field | Notes |
|---|---|
| `userId` + `skillTagId` | Unique pair |
| `level` | `BEGINNER` \| `INTERMEDIATE` \| `ADVANCED` |

---

### `Topic`
The interview subject. Can be global (platform-defined) or user-created.

| Field | Notes |
|---|---|
| `name` | e.g. "React", "System Design", "Leadership" |
| `isGlobal` | Platform topic = true, User topic = false |
| `parentTopicId` | Supports subtopic hierarchy |

---

### `QuestionBank`
Reusable questions contributed by users or the platform. Indexed by `(topicId, difficulty)` for fast retrieval during session question generation.

| Field | Notes |
|---|---|
| `content` | The question text |
| `topicId` | Associated topic |
| `difficulty` | `BEGINNER` \| `INTERMEDIATE` \| `ADVANCED` |
| `questionType` | `behavioral` \| `technical` |
| `isGlobal` | Platform question = true |
| `usageCount` | incremented each time picked during session |

---

### `InterviewSession`
The central entity. One session = one focused interview on one topic.

| Field | Notes |
|---|---|
| `userId` | Tenant isolation — strictly enforced |
| `topicId` | Topic being interviewed on |
| `mode` | `ONE_ON_ONE_AI`, `GROUP_AI`, `HYBRID` |
| `interviewLevel` | `SCREENING` \| `TECHNICAL_L1` \| `TECHNICAL_L2` \| `HR` \| `SYSTEM_DESIGN` (optional) |
| `difficulty` | Base difficulty: `BEGINNER`, `INTERMEDIATE`, `ADVANCED` |
| `adaptive` | If true, AdaptiveEngine drives difficulty per question |
| `durationMinutes` | Intended session length |
| `status` | State machine: see Section 7 |
| `personalityConfig` | JSON — future AI interviewer persona |

---

### `QuestionInstance`
A single question generated within a session. Not reusable across sessions by design.

| Field | Notes |
|---|---|
| `sessionId` | Parent session |
| `content` | The actual question text (may come from QuestionBank) |
| `difficulty` | Difficulty at which this specific question was asked |
| `sequenceOrder` | 1-indexed; unique per session |

**Max 20 questions per session** (enforced at service layer).

---

### `ResponseInstance`
The user's answer to a single question. **One response per question** (enforced via unique constraint).

| Field | Notes |
|---|---|
| `answerText` | Text answer |
| `audioUrl` | URL to audio recording |
| `responseTimeMs` | Total time taken to answer — **now flows into evaluation** |
| `thinkingTimeMs` | Pause before starting to answer — **now flows into evaluation** |
| `answerLength` | Character count of text answer |
| `clarityScore` … `overallScore` | Set by EvaluationService |

---

### `EvaluationReport`
Session-level aggregated scores. One report per session (enforced via unique constraint).

| Field | Notes |
|---|---|
| `overallScore` | Average of per-response `overallScore` |
| `clarityScore` … `technicalScore` | Averaged per-response dimensions |
| `pressureScore` | Avg `pressureScore` from behavioral timing |
| `thinkingDepthScore` | Avg `thinkingDepthScore` from pre-answer pause |
| `feedbackSummary` | One-paragraph feedback text |
| `improvementSuggestions` | JSON: keyed by dimension |

---

## 5. Module Breakdown

### 5.1 Identity Module

**Path**: `src/modules/identity/`

Handles authentication and user profile management.

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
| GET | `/identity/me` | Full profile with skill preferences |
| PUT | `/identity/me` | Update `displayName`, `bio`, `avatarUrl` |
| GET | `/identity/skill-tags` | List global skill tag catalog |
| POST | `/identity/me/skills` | Upsert `(skillTagId, level)` preference |
| DELETE | `/identity/me/skills/:skillTagId` | Remove skill preference |

---

### 5.2 Sessions Module

**Path**: `src/modules/sessions/`

Manages the full lifecycle of an `InterviewSession`.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions` | Create session (with optional `interviewLevel`) |
| GET | `/sessions` | List user sessions (paginated, optional `?status=&page=&limit=`) |
| GET | `/sessions/:id` | Fetch session by ID |
| PUT | `/sessions/:id/start` | `CREATED → ACTIVE` |
| PUT | `/sessions/:id/complete` | `ACTIVE → COMPLETED` |

**`GET /sessions` response shape**:
```json
{
  "data": [{ "id", "status", "interviewLevel", "topic": { "name" }, "evaluation": { "overallScore" }, "_count": { "questions" } }],
  "meta": { "total", "page", "limit", "totalPages" }
}
```

---

### 5.3 Questions Module

**Path**: `src/modules/questions/`

Generates the next question in a session using **bank-first selection**:

1. Validate session is `ACTIVE` and belongs to user
2. Count existing questions (enforce max 20)
3. Determine difficulty (adaptive or static)
4. **Try `QuestionBankService.pickQuestion(topicId, difficulty)`** — use bank question if available, incrementing `usageCount`
5. Fall back to stub generation if bank has no match
6. Persist `QuestionInstance`

---

### 5.4 Question Bank Module

**Path**: `src/modules/question-bank/`

Reusable question repository. Questions here are permanent and indexed for fast retrieval.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/question-bank` | Contribute a question |
| GET | `/question-bank?topicId=&difficulty=` | List questions for a topic |
| GET | `/question-bank/:id` | Fetch a single question |

The `pickQuestion` method selects a random question from matching candidates and increments `usageCount`.

---

### 5.5 Responses Module

**Path**: `src/modules/responses/`

Handles answer submission for a specific question.

| Method | Endpoint | Body | Description |
|---|---|---|---|
| POST | `/questions/:questionId/responses` | `{ answerText?, audioUrl?, responseTimeMs, thinkingTimeMs }` | Submit answer |

`responseTimeMs` and `thinkingTimeMs` are **now consumed** during evaluation — passed to `EvaluationInput` and computed into `pressureScore` and `thinkingDepthScore`.

---

### 5.6 AI Module

**Path**: `src/modules/ai/`

The architectural boundary between domain logic and AI intelligence.

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
    text?: string;
    audioUrl?: string;
    questionType: 'behavioral' | 'technical';
    difficulty: DifficultyLevel;
    responseTimeMs?: number;    // ← NEW: Behavioral timing signal
    thinkingTimeMs?: number;    // ← NEW: Pre-answer pause signal
}
```

#### Output: `PerformanceSignal`

```typescript
interface PerformanceSignal {
    clarityScore: number;
    structureScore: number;
    depthScore: number;
    confidenceScore: number;
    communicationScore: number;
    hesitationScore: number;
    technicalScore: number | null;
    pressureScore: number;        // ← NEW: 0–100, calm under time pressure
    thinkingDepthScore: number;   // ← NEW: 0–100, deliberate pre-answer composure
    overallScore: number;
    explanation: string;
}
```

#### StubEvaluationProvider Heuristics

| Score | Heuristic |
|---|---|
| `clarityScore` | Word count bands |
| `structureScore` | STAR keyword detection (+10 per marker, base 30) |
| `depthScore` | Word count tiers |
| `confidenceScore` | Hedge phrase detection (-10 per hedge, base 80) |
| `communicationScore` | Filler density penalty |
| `hesitationScore` | Filler + ellipsis count × 15 (INVERSE) |
| `technicalScore` | Tech term vocabulary count |
| `pressureScore` | responseTimeMs: <5s=20, 10–45s=85 (optimal), >90s=40 |
| `thinkingDepthScore` | thinkingTimeMs: <1s=30, 6–12s=90 (optimal), >20s=35 |

**Behavioral weighting** (90% text + 10% timing):
```
18% clarity + 18% structure + 18% depth + 18% confidence + 8% communication
+ 8% (100-hesitation) + 5% pressureScore + 5% thinkingDepthScore
```

---

### 5.7 Evaluation Module

**Path**: `src/modules/evaluation/`

**`POST /sessions/:id/evaluation/analyze`**: Runs full evaluation pipeline.

**`GET /sessions/:id/evaluation`**: Returns existing `SessionEvaluationResponseDto`.

#### Response DTO

```typescript
{
  sessionId: string;
  overallScore: number;         // 0–100
  summary: string;

  dimensions: {
    clarity: number;
    structure: number;
    depth: number;
    confidence: number;
    communication: number;
    hesitation: number;         // INVERTED: 100 = no hesitation (better UX)
    technical: number | null;
    pressure: number;           // ← NEW: calm under time pressure
    thinkingDepth: number;      // ← NEW: deliberate pre-answer composure
  };

  strengths: string[];
  improvements: string[];
  difficultyProgression: { startedAt, endedAt };
  evaluatedAt: string;
}
```

---

### 5.8 Adaptive Engine Module

**Path**: `src/modules/adaptive/`

Algorithm unchanged. Reads `overallScore` (now incorporating behavioral signals) from responses to drive difficulty transitions.

| Threshold | Value |
|---|---|
| `INCREASE_ABOVE` | 72 |
| `DECREASE_BELOW` | 55 |
| `MIN_SCORED_RESPONSES` | 2 |

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

Cross-session intelligence. Reads from `EvaluationReport` across all sessions for the authenticated user.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/me` | Full cross-session analytics |

**Response shape**:
```typescript
{
  totalSessions: number;
  analyzedSessions: number;

  trend: Array<{
    sessionId, topicName, interviewLevel,
    analyzedAt, overallScore, confidenceScore,
    clarityScore, structureScore, depthScore
  }>;

  improvement: {
    overallDelta: number;       // latest - first session score
    confidenceDelta: number;
    clarityDelta: number;
    topImprovedDimension: string | null;
    topWeakDimension: string | null;
  };

  byTopic: Array<{
    topicId, topicName, sessionCount, avgOverallScore
  }>;
}
```

---

## 6. Core Flows

### Complete Interview Flow

```
POST /identity/register or /identity/login
        ↓ JWT token returned
POST /sessions  { topicId, mode, difficulty, adaptive, interviewLevel? }
        ↓ session.status = CREATED
PUT  /sessions/:id/start
        ↓ session.status = ACTIVE, startedAt = now

  [Loop: repeat for each question]
  POST /sessions/:id/questions/next
        ↓ QuestionBank.pickQuestion() — bank-first selection
        ↓ Fall back to stub if no bank match
  POST /questions/:questionId/responses  { answerText, responseTimeMs, thinkingTimeMs }
        ↓ Answer saved with timing data
  [End Loop]

PUT  /sessions/:id/complete
        ↓ session.status = COMPLETED
POST /sessions/:id/evaluation/analyze
        ↓ EvaluationInput includes responseTimeMs + thinkingTimeMs
        ↓ pressureScore + thinkingDepthScore computed per response
        ↓ EvaluationReport created with all dimensions
        ↓ session.status = ANALYZED
        ← SessionEvaluationResponseDto (9 dimensions)

GET  /analytics/me
        ← Cross-session trend + improvement delta + per-topic breakdown
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
               └────┬───┘     (timing data captured here)
                    │  PUT /complete
                    ▼
              ┌───────────┐
              │ COMPLETED │ ←── Evaluation triggered here
              └─────┬─────┘
                    │  POST /evaluation/analyze
                    ▼
              ┌──────────┐
              │ ANALYZED │ ←── Report + Analytics available
              └──────────┘

  CANCELLED  ← future (timeout, user exit)
```

---

## 8. Evaluation Pipeline

```
Session COMPLETED
        │
        ▼
EvaluationService.analyzeSession()
        │
        ├── For each QuestionInstance (ordered by sequenceOrder):
        │       ├── Build EvaluationInput {
        │       │       question, text, audioUrl,
        │       │       questionType, difficulty,
        │       │       responseTimeMs,     ← from ResponseInstance
        │       │       thinkingTimeMs      ← from ResponseInstance
        │       │   }
        │       ├── aiProvider.evaluate(input)
        │       │   └── Returns PerformanceSignal (9 dimensions)
        │       └── UPDATE ResponseInstance SET scores
        │
        ├── aggregateSignals(all signals)
        │   ├── Average each dimension across all responses
        │   ├── Average pressureScore + thinkingDepthScore
        │   ├── Build feedbackSummary
        │   └── Build improvementSuggestions
        │
        └── $transaction([
                CREATE EvaluationReport (with pressureScore, thinkingDepthScore),
                UPDATE InterviewSession SET status = ANALYZED
            ])
```

---

## 9. Adaptive Difficulty Engine

### What It Reads
`ResponseInstance.overallScore` — the composite AI signal (now includes 10% behavioral weight).

### Algorithm
```
1. Fetch session base difficulty
2. Fetch last 3 answered questions with responses
3. If no answered questions → return base difficulty
4. Use difficulty of most recent question as current baseline
5. Filter responses where overallScore is not null
6. If fewer than MIN_SCORED_RESPONSES (2) evaluated → hold
7. Compute rolling average of overallScore (last 3)
8. if avg > 72  → increase difficulty
   if avg < 55  → decrease difficulty
   else         → hold
```

---

## 10. API Reference

All routes (except `/identity/register`, `/identity/login`, `/identity/request-otp`, `/identity/verify-otp`, `/identity/google`) require `Authorization: Bearer <JWT>` header.

### Identity

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/identity/register` | — | Register |
| POST | `/identity/login` | — | Login |
| POST | `/identity/request-otp` | — | Request OTP |
| POST | `/identity/verify-otp` | — | Verify OTP |
| POST | `/identity/google` | — | Google OAuth |
| GET | `/identity/me` | ✅ | Get profile |
| PUT | `/identity/me` | ✅ | Update profile |
| GET | `/identity/skill-tags` | ✅ | List global skill tags |
| POST | `/identity/me/skills` | ✅ | Add skill preference |
| DELETE | `/identity/me/skills/:skillTagId` | ✅ | Remove skill preference |

### Topics

| Method | Endpoint | Description |
|---|---|---|
| POST | `/topics` | Create topic |
| GET | `/topics` | List global + user-owned |
| GET | `/topics/:id` | Get topic |
| DELETE | `/topics/:id` | Soft-delete (owner only) |

### Sessions

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions` | Create session |
| GET | `/sessions` | List user sessions (paginated, filterable) |
| GET | `/sessions/:id` | Get session |
| PUT | `/sessions/:id/start` | `CREATED → ACTIVE` |
| PUT | `/sessions/:id/complete` | `ACTIVE → COMPLETED` |

### Questions

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions/:sessionId/questions/next` | Generate next question (bank-first) |

### Question Bank

| Method | Endpoint | Description |
|---|---|---|
| POST | `/question-bank` | Add a reusable question |
| GET | `/question-bank?topicId=&difficulty=` | List questions |
| GET | `/question-bank/:id` | Get question |

### Responses

| Method | Endpoint | Body | Description |
|---|---|---|---|
| POST | `/questions/:questionId/responses` | `{ answerText?, audioUrl?, responseTimeMs, thinkingTimeMs }` | Submit answer |

### Evaluation

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions/:sessionId/evaluation/analyze` | Run evaluation |
| GET | `/sessions/:sessionId/evaluation` | Fetch evaluation report |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/me` | Cross-session trend, delta, per-topic breakdown |

---

## 11. What Is Stubbed vs Real

| Component | Status | Notes |
|---|---|---|
| Auth (JWT, bcrypt, OTP, Google) | ✅ Real | Fully implemented |
| User profile (displayName, bio, avatarUrl) | ✅ Real | GET/PUT /identity/me |
| Skill preferences | ✅ Real | Full CRUD |
| Topic CRUD API | ✅ Real | Global + user-owned, subtopic hierarchy |
| Session lifecycle | ✅ Real | State machine enforced |
| Session LIST + pagination | ✅ Real | Filterable by status |
| Interview levels | ✅ Real | Optional field on sessions |
| Question Bank | ✅ Real | Bank-first question selection |
| Question sequencing + adaptive hook | ✅ Real | Order + bank-first + adaptive |
| Behavioral tracking (responseTimeMs/thinkingTimeMs) | ✅ Real | Flows into pressureScore + thinkingDepthScore |
| Response ingestion | ✅ Real | Validation + persistence complete |
| AI Provider interface | ✅ Real | `AnswerEvaluationProvider` — swap-ready |
| Evaluation pipeline | ✅ Real | 9-dimension per-response + aggregated |
| Adaptive engine | ✅ Real | Signal-driven, tuned thresholds |
| Cross-session analytics | ✅ Real | Trend, improvement delta, per-topic |
| OTP delivery (SMS/Email) | 🔶 Stub | Logs to console — needs provider |
| Question generation content | 🔶 Stub | Bank-first, then template string — needs LLM |
| OpenAI / real LLM evaluation | 🔶 Stub | `StubEvaluationProvider` is active |
| Audio transcription | 🔶 Not built | `audioUrl` stored, Whisper integration pending |

---

## 12. What Comes Next (Tier 3)

### Real AI Integration
- [ ] `OpenAIEvaluationProvider` — implement `AnswerEvaluationProvider` with GPT-4o
- [ ] Real question generation via LLM (replace stub in `QuestionsService`)
- [ ] Audio transcription via Whisper API → feed transcript into evaluation

### Platform Expansion
- [ ] Group/Panel session modes (multi-user, multi-agent design)
- [ ] Micro-drills from improvement suggestions
- [ ] Session recommendations (suggest next topic/level based on analytics)
- [ ] Fear/stress metric (voice analysis, pause spike detection)

### Infrastructure
- [ ] Async evaluation queue (evaluate in background after COMPLETED)
- [ ] OTP delivery via real SMS/email provider (Twilio, SendGrid)
- [ ] Global error filter / consistent error response shape
