# BrainTrain — The Story of What We Built 🧠

> *Imagine you're learning to ride a bike. Every time you fall, a coach watches you, scores how well you balanced, and gives you tips. BrainTrain does that — but for job interviews.*

---

## 🌍 The Big Idea

Most people who fail interviews **know the right answer**. They just freeze up, speak nervously, or ramble when it matters most.

BrainTrain is an **AI-powered interview training platform** that:

1. Gives you practice interview questions
2. Listens to your answers
3. Scores you on 6 dimensions (clarity, confidence, structure, depth, communication, technical)
4. Also watches *how* you answer — did you rush? Did you pause to think?
5. Gets harder or easier depending on how well you're doing
6. Shows you your progress over time

---

## Think of BrainTrain like a **video game for interviews**:

- 🎮 **Session** = One round of the game
- ❓ **Question** = A challenge thrown at you
- 💬 **Response** = Your answer to the challenge
- 🏆 **Score** = How well you did (0–100)
- 📈 **Analytics** = Your stats screen showing improvement
- 🤖 **AI** = The super-smart robot coach scoring you

The game **adapts** — if you score above 72, the next question gets harder. Below 55, it gets easier. Just like how a good video game balances difficulty to keep you in the zone.

---

## 🗺️ The Journey — Phase by Phase

We built this in **3 Phases**, each one adding a new layer of power.

```
Phase 1 → Build the foundation
Phase 2 → Make it smarter
Phase 3 → Make it production-ready (real AI, real money)
```

---

## 🏗️ Phase 1 — Building the Foundation

> *"Lay the tracks before the train can run."*

### What We Built

| What | In Plain English |
|---|---|
| **Database** | The memory of the app — stores users, sessions, questions, and answers |
| **User Accounts** | Sign up with email, phone (OTP), or Google |
| **Sessions** | A user can start a practice interview on any topic |
| **Questions** | The app generates interview questions for you |
| **Responses** | You type your answer (or record audio later) |
| **Evaluation** | The app scores your answer on multiple dimensions |
| **Adaptive Engine** | Questions get harder/easier based on your performance |
| **Analytics** | See how you're improving across sessions |

### The Database Tables We Created

| Table | What it Stores |
|---|---|
| `User` | Your account info — email, name, plan |
| `Topic` | Subjects you want to practice (React, System Design, Leadership...) |
| `QuestionBank` | A library of pre-written good questions |
| `InterviewSession` | One practice interview — stores difficulty, topic, status |
| `QuestionInstance` | The specific question asked in that session |
| `ResponseInstance` | Your answer to that question, with timing data |
| `EvaluationReport` | Your full scorecard for that session |

### The Session Lifecycle (like a board game)

```
You create a session
       ↓
  [CREATED] — ready to start
       ↓  press Start
  [ACTIVE] — questions are flying!
       ↓  press Complete
  [COMPLETED] — all answered
       ↓  AI evaluates
  [ANALYZED] — scorecard ready
```

### The 9 Things We Score You On

| Score | What It Measures |
|---|---|
| **Clarity** | Was your answer easy to understand? |
| **Structure** | Did you follow a logical flow (like STAR method)? |
| **Depth** | Did you give meaningful detail? |
| **Confidence** | Did you sound sure of yourself? |
| **Communication** | Was your delivery smooth, no filler words? |
| **Technical** | Did you use correct technical knowledge? (for tech questions) |
| **Hesitation** | Did you um/uh too much? (lower = more hesitation) |
| **Pressure** | Did you rush or ramble? (optimal answer time: 15–45 seconds) |
| **Thinking Depth** | Did you pause to think before answering? (optimal: 4–12 seconds) |

> 💡 **Important design choice:** The last two scores (Pressure + Thinking Depth) are computed by the **server from your timing data**, not by AI. This makes them predictable, cheap, and trustworthy.

### How the Adaptive Engine Works

```
After you answer 2+ questions:

  Average score > 72  →  Next question gets HARDER 📈
  Average score < 55  →  Next question gets EASIER 📉
  Between 55–72       →  Same difficulty (hold steady) ➡️
```

It uses the average of your **last 3 responses** — so one bad answer doesn't immediately drop you.

---

## 🧠 Phase 2 — Making It Smarter

> *"The skeleton is ready. Now give it a brain."*

### What We Added

| Feature | What Changed |
|---|---|
| **QuestionBank** | A real library of interview questions indexed by topic and difficulty |
| **Bank-First Selection** | Always pick from the bank first — only generate if no match found |
| **OTP Delivery** | Real SMS (Twilio) and Email (Nodemailer) OTP instead of fake codes |
| **Interview Levels** | SCREENING, TECHNICAL_L1, TECHNICAL_L2, HR, SYSTEM_DESIGN |
| **Skill Preferences** | Users declare their skills (React: Intermediate, etc.) |
| **Behavioral Timing** | Started recording *how long* people take to answer |
| **Pressure Score** | Computed from response time — trained eye for rushed answers |
| **Thinking Depth Score** | Computed from pre-answer pause — rewards deliberate thinking |

### The Question Generation Flow

```
User asks for next question
         ↓
Try the QuestionBank first
  (free, instant, curated)
         ↓ if nothing matches
Generate with AI (gpt-4o-mini)
  (costs money, auto-saves to bank)
         ↓ if AI fails
Use Stub (template string)
  (always works, less creative)
```

> 💡 Every AI-generated question is **saved back to the bank** automatically. Over time, the bank fills up and AI is called less and less. **This is called a flywheel.**

---

## 🚀 Phase 3 — Production Hardening

> *"Make it bulletproof and charge money for it."*

This is where we turned a working prototype into a **real SaaS product** — one that can handle real users, real AI costs, and real failures.

### The 6 Tracks We Completed

---

### Track 1 — Async Evaluation (Don't Make Users Wait)

**The problem:** When a session finishes, scoring 5 questions through AI takes 10–20 seconds. You can't make the user just stare at a loading spinner.

**The solution:** **Background jobs.**

```
User clicks "Complete Session"
         ↓
API instantly responds: "Got it! ✅"
         ↓ quietly, in the background…
Worker picks up the job
         ↓
AI scores everything
         ↓
Scores saved to database
         ↓
Frontend polls: "Is it ready yet?"
         ↓ when ready
Show the scorecard 🎉
```

**New pieces we built:**

| Piece | What It Does |
|---|---|
| `EvaluationJob` table | Stores each pending evaluation job |
| `EvaluationWorker` | Runs every 10 seconds, picks up pending jobs, processes them |
| `GET /sessions/:id/status` | Lets the frontend poll "is the evaluation done yet?" |

**The Job Lifecycle:**

```
PENDING → PROCESSING → COMPLETED
                ↓ (if it fails)
            PENDING (retry in 30s)
                ↓ (2nd failure)
            PENDING (retry in 2 min)
                ↓ (3rd failure)
            FAILED permanently
```

**Zombie protection:** If a job gets stuck in PROCESSING for more than 10 minutes (worker crashed), a separate cron job resets it automatically every 5 minutes.

**Idempotency protection:** If the AI finishes but the worker crashes before saving the "COMPLETED" status — on the next retry, the system detects the report already exists and marks the job COMPLETED instead of trying to run AI again. No duplicate charges.

---

### Track 2 — Real AI Evaluation (gpt-4o-mini)

**The problem:** The stub evaluator was just counting words and checking for filler phrases. Not smart enough.

**What we changed:**

| Setting | Value | Why |
|---|---|---|
| Model | `gpt-4o-mini` | Cheapest good model ($0.15/1M tokens) |
| Temperature | `0.1` | Low = consistent, not creative |
| Max tokens | `150` | Hard cap — we only need a tiny JSON response |
| Response format | JSON mode | Forces pure JSON, no markdown |

**What the AI scores (only 6 things):**

```
clarityScore
structureScore
depthScore
confidenceScore
communicationScore
technicalScore (null for behavioral questions)
```

> 💡 We deliberately **do not** ask the AI to score pressure or thinkingDepth. Those come from timing data on the server. Cheaper, faster, and not something AI can predict accurately anyway.

**Retry logic:**

```
Call AI → bad JSON? → retry once → still bad? → use Stub (degraded mode)
```

**Difficulty bias:** For ADVANCED questions, all scores get +4 before being clamped to 100. Because it's harder — gives candidates a fair break.

**Prompt version `v1.0.0` is saved to every report** so if we change the prompt later, we can still compare old and new scores properly.

---

### Track 3 — Real Question Generation (gpt-4o-mini)

**What we built:**

- `OpenAIQuestionGenerationProvider` — calls GPT with topic/difficulty/level context
- Returns `{ questionText, expectedAnswerTraits, estimatedDifficulty }`
- **Auto-saves every generated question** to the QuestionBank with `source: GENERATED`

**Why auto-save?**

> After 6 months, you'll have thousands of AI-curated questions. That's proprietary intellectual property that gets better over time without spending more money.

---

### Track 4 — SaaS Pricing & Abuse Controls

**The Plan System:**

| Plan | Sessions/Month | Evaluation Quality |
|---|---|---|
| **FREE** | 3 | Stub (heuristic scoring) |
| **PRO** | 20 | Real AI (gpt-4o-mini) |

**How it works:**

```
User tries to create a session
         ↓
Check: monthlySessionCount >= planLimit?
         ↓ YES
     403 Forbidden: "Upgrade to PRO"
         ↓ NO
Create session, then increment count
```

**Rate limiting:** No single IP can make more than 30 requests per 60 seconds. Protects against bots and abuse.

**Monthly reset:** On the 1st of every month, a cron job resets everyone's session count to 0.

---

### Track 5 — Observability & Stability

**GlobalExceptionFilter:** Every single error in the API now returns the same shape:

```json
{
  "code": "FORBIDDEN",
  "message": "Monthly session limit reached",
  "details": { ... }
}
```

No more random error formats depending on which endpoint you hit.

**CORS enabled:** The frontend (running on localhost:5173) can now talk to the backend without browser security blocks.

---

### Track 6 — The Dopamine Loop

**New endpoint: `GET /analytics/progression`**

```json
{
  "latestScore": 74,
  "previousScore": 61,
  "delta": 13,
  "improved": true,
  "message": "You improved by 13 points since your last session!"
}
```

This is the "you're getting better!" banner that makes people want to come back tomorrow.

---

## 🗄️ The Database — Full Picture

### All 11 Tables

| Table | Purpose | Key Fields |
|---|---|---|
| `User` | Account + plan | `planType`, `monthlySessionCount`, `monthlyEvaluationCredits` |
| `OtpCode` | One-time passwords | `identifier`, `code`, `expiresAt`, `isUsed` |
| `SkillTag` | Skill catalog | `name`, `isGlobal` |
| `UserSkillPreference` | User's declared skills | `userId`, `skillTagId`, `level` |
| `Topic` | Interview subjects | `name`, `isGlobal`, `parentTopicId` |
| `QuestionBank` | Question library | `topicId`, `difficulty`, `source` (HUMAN / GENERATED) |
| `InterviewSession` | One interview round | `userId`, `status`, `adaptive`, `difficulty` |
| `QuestionInstance` | A question in a session | `sessionId`, `content`, `sequenceOrder` |
| `ResponseInstance` | A user's answer | `responseTimeMs`, `thinkingTimeMs`, all 9 scores |
| `EvaluationReport` | Session scorecard | `overallScore`, `modelUsed`, `estimatedCostUsd` |
| `EvaluationJob` | Background job tracker | `status`, `attempts`, `nextRetryAt` |

### The Indexes We Added (and Why)

> Indexes are like a book's index — instead of reading every page, you jump straight to the right one.

| Table | Index | Why It Matters |
|---|---|---|
| `InterviewSession` | `(userId, status, deletedAt)` | Every time someone opens their session list — fast! |
| `InterviewSession` | `(userId, createdAt)` | Analytics trend chart needs sessions in date order |
| `EvaluationJob` | `(status, nextRetryAt, createdAt)` | Worker finds next job to process instantly |
| `EvaluationJob` | `(status, evaluationStartedAt)` | Finds zombie jobs stuck for too long |
| `QuestionBank` | `(topicId, difficulty, deletedAt)` | Bank-first question lookup runs thousands of times/day |
| `EvaluationReport` | `(modelUsed, createdAt)` | See how much we spent on gpt-4o-mini this month |
| `OtpCode` | `(identifier, isUsed, expiresAt)` | OTP login validation in milliseconds |

---

## 🔌 The API — What You Can Call

### Endpoints at a Glance

| Section | Endpoints |
|---|---|
| **Auth** | Register, Login, OTP (email/SMS), Google OAuth |
| **Profile** | Get/Update profile, manage skill preferences |
| **Topics** | Create/list/delete topics |
| **Sessions** | Create, start, complete, list, get, poll status |
| **Questions** | Generate next question (bank → AI → stub) |
| **Question Bank** | Add/list/get questions |
| **Responses** | Submit answer with timing data |
| **Evaluation** | Manual trigger, get report |
| **Analytics** | Cross-session trends, progression delta |

### The Full Happy Path (Step by Step)

```
Step 1:  POST /identity/login             → get your token
Step 2:  POST /sessions                   → create a session on a topic
Step 3:  PUT  /sessions/:id/start         → begin the interview
Step 4:  POST /sessions/:id/questions/next → get first question
Step 5:  POST /questions/:id/responses    → send your answer + timing
Step 6:  (repeat 4+5 for each question)
Step 7:  PUT  /sessions/:id/complete      → end the session (AI job queued)
Step 8:  GET  /sessions/:id/status        → poll until evaluationStatus = COMPLETED
Step 9:  GET  /sessions/:id/evaluation    → read your full scorecard
Step 10: GET  /analytics/progression      → see if you improved 🎉
```

---

## 🤖 The AI Layer — How the Brain Works

```
You answer a question
        ↓
EvaluationWorker picks up the job
        ↓
Credit check: are you on PRO plan with credits?
        ↓ YES     ↓ NO
     OpenAI     Stub (heuristic)
     (real AI)  (fast, free)
        ↓
AI scores 6 content dimensions (JSON response, 150 tokens)
        ↓
Server computes:
  - pressureScore    (from how fast you answered)
  - thinkingDepth    (from how long you paused before speaking)
  - overallScore     (weighted formula, not AI's guess)
        ↓
Difficulty bias: ADVANCED questions get +4 boost (fairness)
        ↓
Save all scores to ResponseInstance
        ↓
Aggregate across all questions → EvaluationReport
```

### Why Not Let AI Score Everything?

| Dimension | Who Scores It | Why |
|---|---|---|
| Clarity, Structure, Depth, Confidence, Communication, Technical | **AI** (GPT) | Only AI can read meaning from text |
| Pressure, Thinking Depth | **Server** (math formula) | These come from timing data — cheaper, faster, perfectly consistent |
| Overall Score | **Server** (weighted formula) | Prevents AI from gaming the aggregate; consistent across all sessions |

---

## 💰 The Business Model

```
FREE Plan:
  - 3 sessions per month
  - Stub evaluation (heuristic only)
  - Basic analytics

PRO Plan (~₹999–1499/month):
  - 20 sessions per month
  - Real OpenAI evaluation
  - Full analytics
  - Progression tracking
```

### Unit Economics (per session)

| Item | Cost |
|---|---|
| 5 questions × gpt-4o-mini evaluation | ~$0.01–0.03 |
| Question generation (bank hit = $0) | ~$0.002 if AI needed |
| **Total per session** | **~$0.03–0.05** |
| PRO plan price | ~$15–20/month |
| Sessions allowed | 20 |
| Revenue per session | ~$0.75–1.00 |

> ✅ Very healthy margin. Tracking `estimatedCostUsd` per job makes billing intelligence trivial.

---

## 🛡️ How We Handle Failures

| Failure | What Happens |
|---|---|
| AI returns bad JSON | Retry once → if still bad, use Stub (degraded mode) |
| Worker process crashes | Zombie recovery cron resets stuck jobs every 5 minutes |
| Crash after saving report | On retry: ConflictException detected → mark COMPLETED (no duplicate charge) |
| User exceeds plan limit | 403 Forbidden with clear upgrade message |
| Rate limit hit | 429 Too Many Requests |
| Any unexpected error | `GlobalExceptionFilter` returns `{ code, message }` — never a raw stack trace |

---

## 📁 Where Everything Lives

```
apps/backend/
│
├── prisma/schema.prisma    ← The database blueprint (11 tables, 11+ indexes)
├── ARCHITECTURE.md         ← Deep technical documentation
├── STORY.md                ← This file (what you're reading!)
├── postman_collection.json ← All API endpoints to test with
│
└── src/
    ├── main.ts             ← App starts here (CORS, rate limits, error filter)
    ├── app.module.ts       ← Wires all modules together
    │
    ├── filters/            ← GlobalExceptionFilter
    ├── workers/            ← EvaluationWorker (background job processor)
    │
    └── modules/
        ├── identity/       ← Login, register, OTP, Google, profiles
        ├── sessions/       ← The interview lifecycle
        ├── questions/      ← Question generation (bank → AI → stub)
        ├── question-bank/  ← The question library
        ├── responses/      ← Answer submission
        ├── evaluation/     ← Scoring + report generation
        ├── evaluation-job/ ← Async job lifecycle management
        ├── adaptive/       ← Difficulty adjustment engine
        ├── analytics/      ← Progress tracking + dopamine loop
        ├── usage/          ← Plan limits + monthly reset
        └── ai/             ← OpenAI providers + prompts
            ├── providers/  ← OpenAI and Stub implementations
            └── prompts/    ← Versioned prompt definitions (v1.0.0)
```

---

## 🌟 What Makes This Special

| Feature | Why It's Cool |
|---|---|
| **Timing signals** | Most interview tools only read text. We also measure *how* you answer — timing is behavioral data that text can't fake |
| **Server-computed scores** | Pressure and thinking depth are computed deterministically — no hallucination, no variance, totally auditable |
| **Dataset flywheel** | Every AI-generated question auto-saves to the bank. Over time the system gets cheaper to run, not more expensive |
| **Env-driven AI swap** | One environment variable switches between real AI and stub. Zero code changes. Great for development and cost control |
| **Idempotent workers** | If the worker crashes at exactly the wrong moment, the system self-heals. No duplicate charges, no lost data |
| **Exponential backoff** | Failures don't hammer the system. 30s → 2min → 10min retry delays respect API rate limits |

---

## 📊 Summary: What We Built Phase by Phase

| Phase | What We Built | Lines of Code Impact |
|---|---|---|
| **Phase 1** | Full API skeleton: auth, sessions, questions, responses, evaluation, adaptive engine, analytics | ~3000 lines |
| **Phase 2** | QuestionBank, OTP delivery, behavioral timing, pressure/thinking scores, interview levels | ~1000 lines |
| **Phase 3** | Async eval jobs, OpenAI providers, SaaS limits, rate limiting, GlobalExceptionFilter, database indexes, progression endpoint | ~2000 lines |

**Total: A production-ready AI SaaS backend with real users, real AI, and real money in mind. Built by one person. No shortcuts on the important stuff.**

---

*Last updated: Phase 3 complete — Feb 2026*
