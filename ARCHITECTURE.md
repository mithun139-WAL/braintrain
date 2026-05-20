# BrainTrain — Project Architecture

BrainTrain is a confidence-first interview training platform. This repository is a **monorepo** managed with `pnpm`, housing the web application, backend API, and shared packages.

## Monorepo Structure

```text
.
├── apps/
│   ├── api/              # FastAPI backend (Behavioral Evaluation Engine)
│   └── web/              # Next.js Application (Dashboard & Interview UI)
├── packages/
│   └── shared/           # Common TypeScript types, DTOs, and Enums
├── package.json          # Root workspace configuration
└── pnpm-workspace.yaml   # pnpm workspace definition
```

## Core Components

### 1. API (`apps/api`)
The backend is a **FastAPI** (Python) application responsible for:
- Session management and interview lifecycle state machines.
- AI-driven participant evaluation (Clarity, Structure, Confidence, etc.).
- Adaptive difficulty engine (adjusts question difficulty based on performance).
- Integration with external services (OpenAI GPT-4o-mini, Whisper-1, Twilio, aiosmtplib).

For detailed backend architecture, see `apps/api/`.

### 2. Web (`apps/web`)
The frontend is a **Next.js** application providing:
- Candidate dashboard for tracking progression.
- Real-time interview interface with voice/text response submission.
- AI-generated performance reports and analytics.
- Centralized user settings, subscription management, and AI behavior preferences.

### 3. Shared (`packages/shared`)
A library containing shared logic and types used by both the API and frontend to ensure type safety and contract consistency.
- **DTOs**: Standardized API request/response shapes.
- **Enums**: Shared states like `SessionStatus` or `DifficultyLevel`.

## Technology Stack

| Layer | Technology |
|---|---|
| **Monorepo Manager** | pnpm |
| **Frontend Language** | TypeScript |
| **Backend Language** | Python 3.12 |
| **Frontend** | Next.js (App Router), Tailwind CSS, React Query, Zustand (Session Builder) |
| **Backend** | FastAPI, SQLAlchemy 2.0 async, PostgreSQL, APScheduler |
| **AI** | OpenAI GPT-4o-mini (evaluation), Whisper-1 (transcription) |
| **Shared** | TypeScript |

## Deployment & Environments

- **Development**: Local environment with `.env.development`.
- **Production**: Deployed infrastructure with environment-specific secrets.
- **CI/CD**: Automated testing and linting enforced via GitHub Actions (or similar).
