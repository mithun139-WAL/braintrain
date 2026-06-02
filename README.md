# BrainTrain

**AI-powered mock interview training platform that actually makes you interview-ready.**

BrainTrain simulates realistic mock interviews, evaluates your performance across multiple dimensions using large language models, tracks your progression over time, and generates personalized coaching and training plans to close the gap between where you are and where you need to be.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Why Not Just Use ChatGPT?](#why-not-just-use-chatgpt)
- [Existing Alternatives and How BrainTrain Differs](#existing-alternatives-and-how-braintrain-differs)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture Overview](#architecture-overview)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Billing Plans](#billing-plans)
- [Deployment](#deployment)

---

## Problem Statement

Every year, millions of candidates fail interviews — not because they lack the skills, but because they lack structured, honest, and repeatable preparation.

The traditional preparation cycle looks like this:

1. Read a book or watch a YouTube playlist
2. Scroll through Glassdoor interview questions
3. Mentally "rehearse" answers in your head
4. Show up to the actual interview and freeze, ramble, or lose structure under pressure

This cycle produces candidates who *know* things but cannot *communicate* them under pressure. The critical gap is not knowledge — it is **performance under realistic interview conditions**.

What candidates actually need:

- A safe, repeatable environment to practice speaking answers out loud
- Objective, honest feedback — not the vague "great job" of a friend or the generic tips of a blog post
- Measurement of the exact dimensions interviewers judge: clarity, structure, depth, confidence, communication, and technical accuracy
- A feedback loop that identifies weaknesses, trains those weaknesses, and confirms whether they have improved
- Enough repetitions with spaced variation in difficulty and question type to build interview muscle memory

BrainTrain was built to fill that gap. It is not a study tool. It is a **performance training system** for interviews.

---

## Why Not Just Use ChatGPT?

This is the most common question, and it deserves a direct, honest answer.

You can absolutely open ChatGPT, paste a job description, and ask it to interview you. People do this. It even works — to a point. But there is a fundamental architectural difference between an ad-hoc chat session and what BrainTrain is built to do.

### What a Chat Session With an LLM Gives You

| What you get | Reality |
|---|---|
| A question-and-answer conversation | You ask the model to act as an interviewer; it tries |
| Some feedback if you ask for it | The model will say "good answer, here are some improvements" |
| A generic experience | The same questions, no memory, no progression |
| One-off usage | Nothing is stored, scored, or tracked |

### What That Approach is Missing

**No structured evaluation.** When you type an answer into ChatGPT and ask for feedback, the model produces prose. That prose is helpful, but it is not a scored, calibrated, multi-dimensional evaluation. You get an essay about your answer, not a signal you can act on. There is no number, no trend, no comparison to your previous session.

**No longitudinal tracking.** Every conversation starts fresh. ChatGPT has no memory of how you performed last Tuesday vs. today. It cannot tell you that your structural score improved by 8 points but your confidence has been flat for three sessions. That data does not exist because nothing is being measured.

**No adaptive difficulty.** A chat session does not know that your last four answers scored above 72 and it should move you to harder territory. It does not model your skill level over time. The difficulty is whatever you happen to prompt it to be.

**No audio.** Real interviews are spoken. Your ability to answer a question in text is not the same as your ability to answer it out loud under a time constraint. BrainTrain accepts audio responses and transcribes them, because typing an answer and speaking one are two completely different cognitive and performance tasks.

**No follow-up probing.** A real interviewer does not accept your first answer and move on. They push: "Can you walk me through that in more detail?" or "What would you do differently now?" BrainTrain fires real-time AI follow-up probes after each answer, the same way a real panel would.

**No training plan.** After your ChatGPT session ends, there is nothing actionable on the other side. BrainTrain generates a 7-day personalized training plan based on your actual weakness signals from the evaluation — with day-by-day tasks, exercise types, and estimated durations.

**No coaching continuity.** BrainTrain's AI coaching sessions are linked to your interview session data. The coach knows which dimensions are weak, which sessions triggered a drop, and what your trend looks like across time. A raw ChatGPT conversation has none of that context unless you manually paste it in.

**The core difference:** A chat session is a tool you use. BrainTrain is a system that trains you.

---

## Existing Alternatives and How BrainTrain Differs

There are a handful of tools in this space. Here is an honest comparison.

### Pramp / Interviewing.io

**What they do:** Peer-to-peer mock interviews. You get matched with another human candidate, one plays interviewer, one plays interviewee, then you swap.

**The problem:** Humans are inconsistent, biased, and unavailable on demand. The quality of your practice session depends entirely on the person you are matched with. You cannot practice at 11 PM without waiting for someone else. You cannot repeat the same scenario five times in a row. The feedback is one human's subjective impression.

**How BrainTrain differs:** Always available, always consistent, always scored by the same calibrated rubric. No scheduling, no waiting, no dependency on another person's time or effort.

### LeetCode / HackerRank (Behavioral Practice)

**What they do:** Excellent for coding and DSA. Their behavioral practice features are secondary, thin, and produce no real evaluation.

**The problem:** These platforms optimize for code correctness, not communication performance. There is no structured evaluation of how you explain your thinking, how confident you sound, or how your answers are structured. There is no coaching for the soft-skill dimensions that decide most behavioral round outcomes.

**How BrainTrain differs:** BrainTrain is built specifically for the communication performance layer of interviewing — the part that LeetCode does not touch.

### Interview Warmup (Google)

**What they do:** A Google product that lets you speak answers to behavioral questions and get basic transcription and keyword feedback.

**The problem:** The feedback model is shallow. It identifies whether you used certain "good" keywords and whether you spoke for a long enough duration. It does not evaluate the structure of your argument, the depth of your insight, your confidence signals, or your technical accuracy. It generates no progression tracking, no weakness identification, and no training plan.

**How BrainTrain differs:** BrainTrain evaluates seven dimensions per response with calibrated LLM scoring, tracks those dimensions across every session you run, and routes your weaknesses into personalized coaching and training.

### Big Interview / Yoodli

**What they do:** Pre-recorded video interview practice platforms with some AI feedback on filler words, pacing, and eye contact.

**The problem:** These tools focus on presentation mechanics (are you saying "um" too much, is your posture good) rather than content quality and reasoning depth. They do not generate questions dynamically, they do not adapt difficulty based on your performance, and they do not connect your practice sessions to a training loop.

**How BrainTrain differs:** BrainTrain evaluates the *substance* of your answers — the clarity of your argument, the depth of your thinking, the structure of your reasoning — not just surface delivery signals. It also generates questions dynamically using LLMs, ensuring you never see the same question twice and that every session is realistic.

### Summary Comparison

| Capability | ChatGPT | Pramp | Interview Warmup | Big Interview | **BrainTrain** |
|---|---|---|---|---|---|
| On-demand availability | Yes | No | Yes | Yes | Yes |
| Multi-dimensional scoring | No | No | No | Partial | **Yes** |
| Longitudinal tracking | No | No | No | No | **Yes** |
| Adaptive difficulty | No | No | No | No | **Yes** |
| Audio response support | No | Yes | Yes | Yes | **Yes** |
| AI follow-up probing | No | Human | No | No | **Yes** |
| Personalized training plan | No | No | No | No | **Yes** |
| AI coaching linked to your data | No | No | No | No | **Yes** |
| Panel interview simulation | No | No | No | No | **Yes** |
| Technical + behavioral coverage | Partial | Partial | Behavioral only | Behavioral only | **Yes** |

---

## Features

### Authentication
- Email and password registration and login
- OTP-based login via email or SMS
- Google OAuth single sign-on
- JWT-based session management (7-day tokens)

### Interview Session System
- Multi-step session builder: choose topic, interview type, mode, difficulty, duration, and adaptive toggle
- **Interview types**: Technical, Behavioral, Mixed, Group Discussion, Rapid Fire
- **Interview modes**: 1-on-1 AI, Panel AI (simulated multi-interviewer panel), Hybrid
- **Difficulty levels**: Easy, Medium, Hard
- Adaptive difficulty that automatically adjusts based on your rolling performance average
- Text and audio response submission
- Audio transcription via Groq Whisper (fastest) with OpenAI Whisper-1 fallback
- Real-time AI follow-up probing after each answer
- Session state machine: `CREATED → ACTIVE → COMPLETED → ANALYZED`

### AI Evaluation Engine
- Per-response scoring across seven dimensions:
  - **Clarity** — how clearly the answer is expressed
  - **Structure** — logical organization of the response
  - **Depth** — depth of insight and completeness
  - **Confidence** — perceived confidence in delivery
  - **Communication** — overall communication quality
  - **Technical Accuracy** — correctness of technical content (technical interviews)
  - **Hesitation** — computed from timing and response signals
- Pressure and thinking depth scores computed from response timing data
- Session-level evaluation report with aggregated weighted overall score (0–100 scale)
- Calibration anchors: 50 = average candidate, 70 = strong hire, 85+ = exceptional
- AI-generated feedback summary and improvement suggestions per dimension
- Asynchronous background evaluation with worker job queue
- Cost and token tracking per evaluation for transparency

### AI Question Generation
- LLM-generated questions contextualized by topic, difficulty, and interview type
- STAR-method framing for behavioral questions
- Deep practical framing for technical questions
- No question repetition within a session
- Generated questions contribute to a growing question bank

### Analytics Dashboard
- Overall score, confidence, clarity, and technical depth stat cards with trend deltas
- Historical performance trend charts across all dimensions
- Per-topic drill-down analytics
- Session-over-session progression tracking (dopamine-loop progress banner)
- Interview readiness score (0–100)
- AI-generated "Next Best Move" coaching tip based on your analytics data
- Weakness and improvement identification across dimensions

### AI Coaching
- Conversational AI coach backed by LangChain or NVIDIA NIM
- Coaching sessions optionally linked to a specific interview session for context
- Focus areas: general interview coaching or specific dimension improvement
- Full message history stored per coaching session

### AI Training Plans
- 7-day personalized training plan generated from your evaluation signals
- Day-by-day task breakdown with exercise types and estimated durations
- Task completion tracking
- Plan history

### Question Bank
- Curated global question library filterable by topic, interview type, and difficulty
- User-created question support
- 16 pre-seeded topic areas across Technical Skills, Behavioral Skills, and Domain Expertise

### Topics
- Global topic taxonomy: DSA, System Design, Database Design, Frontend, Backend, DevOps & Cloud, ML & AI, Leadership & Teamwork, Problem Solving, Communication, API Design, Security & Auth, Mobile Development, and more
- User-created custom topics

### Billing
- Free plan: 3 sessions per month
- Pro plan: 20 sessions per month, 100 evaluation credits per month
- Stripe Checkout and Customer Portal integration
- Subscription lifecycle management via Stripe webhooks

### Settings
- Profile management (name, bio, avatar, email, phone)
- Skill preference tagging with proficiency levels
- Subscription and billing management

---

## Tech Stack

### Monorepo
| Tool | Purpose |
|---|---|
| pnpm workspaces | Package management |
| `apps/web` | Next.js frontend |
| `apps/api` | FastAPI backend |
| `packages/shared` | Shared TypeScript types and DTOs |

### Frontend
| Technology | Role |
|---|---|
| Next.js 15 (App Router) | Framework |
| TypeScript 5 | Language |
| Tailwind CSS 3 | Styling |
| TanStack React Query v5 | Server state management |
| Zustand v5 | Client state management |
| Recharts | Performance charts |
| Axios | HTTP client |

### Backend
| Technology | Role |
|---|---|
| FastAPI 0.115+ | API framework |
| Python 3.12 | Language |
| SQLAlchemy 2.0 async | ORM |
| PostgreSQL + asyncpg | Database |
| Alembic | Database migrations |
| APScheduler | Background job scheduling |
| python-jose + bcrypt | JWT auth and password hashing |
| Pydantic v2 | Validation and settings |
| SlowAPI | Rate limiting |
| aiosmtplib | Email delivery |
| Twilio | SMS OTP |
| Stripe | Billing |

### AI Providers
| Provider | Role | Priority |
|---|---|---|
| NVIDIA NIM (`llama-3.1-nemotron-70b-instruct`) | LLM evaluation, question gen, coaching | Highest |
| OpenAI GPT-4o-mini | LLM fallback | Second |
| Groq (`whisper-large-v3`) | Audio transcription | Highest |
| OpenAI Whisper-1 | Audio transcription fallback | Second |
| Stub providers | Zero-cost offline development | Fallback |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Next.js Frontend                   │
│  React Query (server state) + Zustand (client state) │
└─────────────────────┬───────────────────────────────┘
                      │ REST API (JSON)
┌─────────────────────▼───────────────────────────────┐
│                  FastAPI Backend                      │
│  Router → Service → Repository pattern per module    │
│                                                      │
│  Modules: identity, sessions, questions, responses,  │
│  evaluation, analytics, coaching, training_plans,    │
│  topics, question_bank, billing                      │
└──────┬──────────────┬──────────────┬────────────────┘
       │              │              │
┌──────▼──────┐ ┌─────▼─────┐ ┌────▼────────────────┐
│ PostgreSQL  │ │ AI Factory │ │ Background Worker    │
│ (16 tables) │ │ NIM →      │ │ APScheduler          │
│ Alembic     │ │ OpenAI →   │ │ Evaluation job queue │
│ migrations  │ │ Stub       │ │ (SELECT FOR UPDATE   │
└─────────────┘ └─────┬─────┘ │  SKIP LOCKED)        │
                       │       └─────────────────────┘
              ┌────────▼──────────────┐
              │  Audio: Groq → OpenAI │
              └───────────────────────┘
```

**Evaluation pipeline:**

1. User completes a session → `PUT /sessions/:id/complete`
2. API transitions session to `COMPLETED` and enqueues an `EvaluationJob` (status: `PENDING`)
3. APScheduler worker polls every 10 seconds, claims unclaimed jobs via `SELECT ... FOR UPDATE SKIP LOCKED` (safe for multi-process deployments)
4. Worker calls the AI evaluation provider per response, scores 6 LLM dimensions, computes 2 server-side timing dimensions, aggregates a weighted overall score
5. Session transitions to `ANALYZED`, report written to `evaluation_reports`
6. Frontend polls `GET /sessions/:id/status` with React Query and navigates to the report when ready

---

## Getting Started

### Prerequisites

- Node.js 20+
- pnpm 10+
- Python 3.12+
- PostgreSQL 15+
- `uv` (Python package manager) — `pip install uv`

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd braintrain

# Install frontend and shared package dependencies
pnpm install
```

### 2. Set up the backend

```bash
cd apps/api

# Install Python dependencies
uv sync

# Copy and fill in environment variables
cp .env.example .env.development
# Edit .env.development with your values
```

### 3. Set up the database

```bash
# In apps/api
uv run alembic upgrade head
```

### 4. Start the backend

```bash
# In apps/api
uv run uvicorn app.main:app --reload --port 8000
```

The API runs at `http://localhost:8000`. Swagger docs are available at `http://localhost:8000/docs` in development.

### 5. Set up the frontend

```bash
cd apps/web

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### 6. Start the frontend

```bash
# In apps/web
pnpm dev
```

The app runs at `http://localhost:3000`.

### Running Without API Keys (Stub Mode)

If you leave `OPENAI_API_KEY`, `NVIDIA_API_KEY`, and `GROQ_API_KEY` empty in your `.env.development`, the backend automatically uses stub providers. Stub providers return deterministic fake responses — questions, evaluations, transcriptions — with zero API cost. This is the intended mode for local development and testing.

---

## Environment Variables

### Backend (`apps/api/.env.development`)

```env
# App
APP_ENV=development
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/braintrain_api_dev

# Auth
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# AI Providers (all optional — leave empty for stub mode)
OPENAI_API_KEY=sk-...
NVIDIA_API_KEY=nvapi-...
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
GROQ_API_KEY=gsk_...
GROQ_WHISPER_MODEL=whisper-large-v3

# Email OTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=noreply@braintrain.ai

# SMS OTP (optional)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# CORS
FRONTEND_URL=http://localhost:3000

# Stripe Billing (optional)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRO_PRICE_ID=
STRIPE_SUCCESS_URL=http://localhost:3000/dashboard/settings?billing=success
STRIPE_CANCEL_URL=http://localhost:3000/dashboard/settings?billing=cancelled
STRIPE_PORTAL_RETURN_URL=http://localhost:3000/dashboard/settings
PRO_MONTHLY_EVALUATION_CREDIT_LIMIT=100

# Usage Limits
FREE_MONTHLY_SESSION_LIMIT=3
PRO_MONTHLY_SESSION_LIMIT=20

# Rate Limiting
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW_SECONDS=60
```

### Frontend (`apps/web/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## API Reference

### Identity

| Method | Endpoint | Description |
|---|---|---|
| POST | `/identity/register` | Register with email and password |
| POST | `/identity/login` | Login with email and password |
| POST | `/identity/request-otp` | Request OTP via email or phone |
| POST | `/identity/verify-otp` | Verify OTP and receive JWT |
| POST | `/identity/google` | Login with Google ID token |
| GET | `/identity/me` | Get current user profile |
| PUT | `/identity/me` | Update profile |
| GET | `/identity/skill-tags` | List available skill tags |
| POST | `/identity/me/skills` | Add skill preference |
| DELETE | `/identity/me/skills/{skill_tag_id}` | Remove skill preference |

### Sessions

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions` | Create a new interview session |
| GET | `/sessions` | List sessions (paginated) |
| GET | `/sessions/{id}` | Get session detail |
| PUT | `/sessions/{id}/start` | Start session (CREATED → ACTIVE) |
| PUT | `/sessions/{id}/complete` | Complete session (ACTIVE → COMPLETED) |
| GET | `/sessions/{id}/status` | Poll evaluation job status |
| POST | `/sessions/{id}/questions/next` | Generate next AI question |

### Responses

| Method | Endpoint | Description |
|---|---|---|
| POST | `/questions/{id}/responses` | Submit answer (text or audio URL) |
| POST | `/questions/{id}/responses/{rid}/followup` | Request real-time follow-up probe |

### Evaluation

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions/{id}/evaluation/analyze` | Trigger AI evaluation (idempotent) |
| GET | `/sessions/{id}/evaluation` | Retrieve evaluation report |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/me` | Full user performance analytics |
| GET | `/analytics/progression` | Score delta vs. previous session |
| GET | `/analytics/topics/{id}` | Topic-level analytics |

### Coaching

| Method | Endpoint | Description |
|---|---|---|
| POST | `/coaching` | Create AI coaching session |
| GET | `/coaching` | List coaching sessions |
| GET | `/coaching/{id}` | Get session with message history |
| POST | `/coaching/{id}/messages` | Send message, receive AI reply |
| PUT | `/coaching/{id}/end` | End coaching session |

### Training Plans

| Method | Endpoint | Description |
|---|---|---|
| POST | `/training-plans/generate` | Generate 7-day AI training plan |
| GET | `/training-plans/current` | Get active training plan |
| GET | `/training-plans` | List plan history |
| POST | `/training-plans/tasks/{id}/complete` | Mark task complete |

### Topics

| Method | Endpoint | Description |
|---|---|---|
| GET | `/topics` | List global and user-owned topics |
| POST | `/topics` | Create user-owned topic |
| GET | `/topics/{id}` | Get topic |
| DELETE | `/topics/{id}` | Soft-delete topic |

### Question Bank

| Method | Endpoint | Description |
|---|---|---|
| POST | `/question-bank` | Create question |
| GET | `/question-bank` | List questions (filterable by topic, type, difficulty) |
| GET | `/question-bank/{id}` | Get question |

### Billing

| Method | Endpoint | Description |
|---|---|---|
| GET | `/billing/status` | Current plan and usage |
| POST | `/billing/checkout` | Create Stripe Checkout session |
| POST | `/billing/portal` | Create Stripe Customer Portal session |
| POST | `/billing/webhook` | Stripe webhook receiver |

All API responses follow a standard envelope format:

```json
{
  "success": true,
  "data": { ... }
}
```

---

## Billing Plans

| Feature | Free | Pro |
|---|---|---|
| Sessions per month | 3 | 20 |
| Evaluation credits per month | Included | 100 |
| AI coaching | Yes | Yes |
| Training plans | Yes | Yes |
| Analytics | Yes | Yes |
| Custom topics | Yes | Yes |
| Audio responses | Yes | Yes |
| Panel interview mode | Yes | Yes |

---

## Deployment

### Backend — Render

The API is deployed as a Python web service on Render with an always-on instance (required for the APScheduler evaluation worker).

Start command:
```
uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set all environment variables from the backend `.env` reference in the Render service dashboard.

Swagger and Redoc documentation endpoints (`/docs`, `/redoc`) are disabled in production.

### Frontend — Vercel

Deploy `apps/web` as a Vercel project with root directory set to `apps/web`.

Set `NEXT_PUBLIC_API_URL` to your Render API service URL in Vercel's environment variable settings.

### CI/CD

- GitHub Actions CI runs on every push: builds the shared package, builds the Next.js app, installs Python dependencies, and smoke-imports `app.main` to catch import errors.
- GitHub Actions deploy workflow runs on push to `main`: deploys to Render and Vercel, then health-checks both services.

---

## Project Structure

```
braintrain/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py         # App factory and router registration
│   │   │   ├── core/           # Config, middleware, security, rate limiting
│   │   │   ├── db/
│   │   │   │   └── models/     # SQLAlchemy ORM models (16 tables)
│   │   │   ├── modules/        # Feature modules (router/service/repository)
│   │   │   │   ├── identity/
│   │   │   │   ├── sessions/
│   │   │   │   ├── questions/
│   │   │   │   ├── responses/
│   │   │   │   ├── evaluation/
│   │   │   │   ├── analytics/
│   │   │   │   ├── coaching/
│   │   │   │   ├── training_plans/
│   │   │   │   ├── topics/
│   │   │   │   ├── question_bank/
│   │   │   │   └── billing/
│   │   │   ├── ai/
│   │   │   │   ├── factory.py      # Provider selection (NIM > OpenAI > Stub)
│   │   │   │   ├── protocols.py    # Typed AI provider interfaces
│   │   │   │   ├── providers/      # 15 provider implementations
│   │   │   │   └── prompts/        # Versioned LLM prompt definitions
│   │   │   ├── adaptive/
│   │   │   │   └── engine.py       # Adaptive difficulty algorithm
│   │   │   └── workers/
│   │   │       └── evaluation_worker.py
│   │   └── alembic/            # Database migrations
│   ├── web/                    # Next.js frontend
│   │   ├── app/
│   │   │   ├── (auth)/         # Login, register, verify-otp
│   │   │   ├── (dashboard)/    # Main app (analytics, coach, training, settings)
│   │   │   └── (session)/      # Active interview, evaluation report, session builder
│   │   ├── components/         # Reusable UI components
│   │   ├── features/           # Auth, onboarding, training feature modules
│   │   ├── hooks/              # React Query query and mutation hooks
│   │   └── lib/
│   │       ├── api/            # Axios API clients (one per domain)
│   │       └── store/          # Zustand stores (auth, sessionBuilder, ui)
│   └── mobile/                 # Placeholder
└── packages/
    └── shared/                 # Shared TypeScript types, enums, and DTOs
```
