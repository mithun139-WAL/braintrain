# BrainTrain — Project Architecture

BrainTrain is a confidence-first interview training platform. This repository is a **monorepo** managed with `pnpm`, housing the web application, backend services, and shared packages.

## Monorepo Structure

```text
.
├── apps/
│   ├── backend/          # NestJS API (Behavioral Evaluation Engine)
│   └── web/              # Next.js Application (Dashboard & Interview UI)
├── packages/
│   └── shared/           # Common TypeScript types, DTOs, and Enums
├── package.json          # Root workspace configuration
└── pnpm-workspace.yaml   # pnpm workspace definition
```

## Core Components

### 1. Backend (`apps/backend`)
The backend is a **NestJS** application responsible for:
- Session management and interview lifecycle state machines.
- AI-driven participant evaluation (Clarity, Structure, Confidence, etc.).
- Adaptive difficulty engine (adjusts question difficulty based on performance).
- Integration with external services (OpenAI, Twilio, Nodemailer).

For detailed backend architecture, see [apps/backend/ARCHITECTURE.md](file:///Users/mithun/Downloads/braintrain/apps/backend/ARCHITECTURE.md).

### 2. Web (`apps/web`)
The frontend is a **Next.js** application providing:
- Candidate dashboard for tracking progression.
- Real-time interview interface with voice/text response submission.
- AI-generated performance reports and analytics.
- Centralized user settings, subscription management, and AI behavior preferences.

### 3. Shared (`packages/shared`)
A library containing shared logic and types used by both the backend and frontend to ensure type safety and contract consistency.
- **DTOs**: Standardized API request/response shapes.
- **Enums**: Shared states like `SessionStatus` or `DifficultyLevel`.

## Technology Stack

| Layer | Technology |
|---|---|
| **Monorepo Manager** | pnpm |
| **Language** | TypeScript |
| **Frontend** | Next.js (App Router), Tailwind CSS, React Query, Zustand |
| **Backend** | NestJS, Prisma (PostgreSQL), OpenAI API |
| **Shared** | TypeScript |

## Deployment & Environments

- **Development**: Local environment with `.env.development`.
- **Production**: Deployed infrastructure with environment-specific secrets.
- **CI/CD**: Automated testing and linting enforced via GitHub Actions (or similar).
