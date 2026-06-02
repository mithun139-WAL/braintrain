# BrainTrain 🚀

**The AI-Powered Technical Communication & Interview Training Platform for Modern Teams.**

*Substantially built for the hackathon theme: **AI at Work: Productivity & Teamwork Reimagined**, leveraging the **Microsoft AI Stack** via **Azure AI Foundry (GitHub Models)**.*

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Platform Compliance](https://img.shields.io/badge/microsoft--ai--stack-compliant-blue.svg)]()
[![Theme](https://img.shields.io/badge/theme-AI--at--Work-orange.svg)]()

---

## 🎯 Problem Statement & Intent

### The Problem: The High Cost of Engineering Communication Gaps
In the modern workplace, technical communication is the single biggest bottleneck to team productivity. High-growth engineering teams suffer from:
1. **Manual Coaching Drudgery**: Senior engineers spend countless hours conducting mock interviews, giving design feedback, or onboarding new hires.
2. **Inconsistent Alignment**: Engineers struggle to articulate complex system architectures (e.g., database isolation levels, caching strategies, asynchronous message routing) under pressure.
3. **Context Drift**: Standard study guides are generic and fail to train engineers on a team's actual proprietary technical stack.

This cycle drains senior productivity, increases onboarding time, and results in costly communication gaps during critical design reviews.

### The Intent: Automating Performance Readiness
**BrainTrain re-imagines team productivity and collaboration.** Instead of wasting senior engineers' valuable time on manual peer coaching, BrainTrain automates technical mock interviews, system design practice, and communication leveling using an **always-on, conversational voice agent**.

By enabling engineers to upload internal specifications and coding rubrics into a **retrieval-augmented knowledge base**, BrainTrain generates contextual, grounded questions and provides structured, multi-dimensional feedback. It eliminates repetitive onboarding overhead, helps professionals master technical alignment, and elevates team performance.

---

## 🏆 Hackathon Theme & Microsoft AI Stack Integration

### 1. Theme Alignment: AI at Work
BrainTrain transforms chaotic, manual peer-coaching loops into an automated, shared clarity system.
- **Intelligent Workflows**: Evaluates spoken answers across 7 performance dimensions (Clarity, Structure, Depth, Confidence, Communication, Technical Accuracy, Hesitation) and drafts a personalized 7-day training plan.
- **Real-Time Knowledge Sharing**: Integrates architectural RAG so engineers train directly against team-specific technical guidelines.
- **Teamwork Productivity**: Senior engineers define custom mock interviewer personas and rubrics, allowing juniors to onboard and upskill asynchronously.

### 2. Powered by the Microsoft AI Stack
BrainTrain is fully integrated with the **Microsoft AI Stack** via **Azure AI Foundry (GitHub Models)**:
- **Core LLM Processing**: Question generation, response evaluations, coaching, and turn decisions are powered by Azure AI-backed inference models (e.g., Llama-3.1-Nemotron, GPT-4o) using the GitHub Models endpoint (`models.inference.ai.azure.com`).
- **Azure AI Foundry Compliance**: Setting the `GITHUB_TOKEN` environment variable automatically routes all LLM prompts to Azure AI Foundry models in the backend factory.
- **Development Tooling**: Built using GitHub Copilot for maximum token efficiency and rapid iteration.

---

## 💡 Why BrainTrain is Different

| Feature | ChatGPT | Google Interview Warmup | **BrainTrain** |
|---|---|---|---|
| **Multi-Dimensional Scoring** | No (Generates prose) | No (Keywords only) | **Yes (7 calibrated metrics)** |
| **Longitudinal Tracking** | No (Fresh session every time) | No (One-off) | **Yes (Progress over time)** |
| **Real-time Voice Probing** | No (Text/Voice chatbot) | No (Pre-recorded prompt) | **Yes (Asynchronous voice agent)** |
| **Personalized Training Plan** | No | No | **Yes (7-day workout generation)** |
| **Knowledge Base (RAG)** | No | No | **Yes (Semantic + Keyword search)** |

---

## 🛠️ Tech Stack

### Monorepo
- **Package Management**: `pnpm` workspaces
- **Frontend App**: `apps/web` (Next.js 15, React, Tailwind CSS 3, Zustand v5, React Query v5, Recharts)
- **Backend API**: `apps/api` (FastAPI, Python 3.12, SQLAlchemy 2.0, PostgreSQL + asyncpg, Alembic)
- **Shared Contracts**: `packages/shared` (Shared TypeScript types and DTOs)

### AI & Media Integration
- **LLM Pipeline**: Azure AI Foundry / GitHub Models (Primary), NVIDIA NIM, OpenAI fallback
- **Audio & WebRTC**: LiveKit (real-time voice streaming), Edge-TTS, Groq Whisper (transcription)
- **Vector Search**: PostgreSQL `pgvector` index (IVFFlat with cosine distance)

---

## 📁 Getting Started

### Prerequisites
- Node.js 20+
- pnpm 10+
- Python 3.12+
- PostgreSQL 15+ with `pgvector` extension
- `uv` (Python package manager)

### 1. Installation
```bash
git clone <repo-url>
cd braintrain
pnpm install
```

### 2. Backend Setup
```bash
cd apps/api
uv sync
cp .env.example .env.development
# Edit .env.development and configure your GITHUB_TOKEN
```

### 3. Database Migration & Seed
```bash
# Run database migrations
uv run alembic upgrade head

# Ingest curated mock interview Q&A pairs into RAG
uv run python -m app.ai.rag.ingest
```

### 4. Start the Application
```bash
# Start backend (from apps/api)
uv run uvicorn app.main:app --reload --port 8000

# Start frontend (from apps/web)
pnpm dev
```
The application will run at `http://localhost:3000`.

---

## 🔑 Environment Variables (`apps/api/.env.development`)

```env
# Azure AI Foundry / GitHub Models
GITHUB_TOKEN=ghu_...
GITHUB_MODEL=meta-llama-3.1-70b-instruct
GITHUB_MODELS_BASE_URL=https://models.inference.ai.azure.com

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/braintrain_api_dev

# WebRTC & Media
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...

# Groq Transcription
GROQ_API_KEY=gsk_...
```

---

## 📂 Project Structure

```
braintrain/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── ai/
│   │   │   │   ├── rag/        # Ingest and retrieval modules
│   │   │   │   ├── voice/      # Conversational agent & policies
│   │   │   │   └── providers/  # Azure AI Foundry model connectors
│   │   │   ├── db/             # Models and migrations
│   │   │   └── modules/        # API Routers & Services
│   │   └── tests/              # 11 unit test modules
│   ├── web/                    # Next.js frontend app
│   └── mobile/                 # Mobile client
├── docs/                       # Core system architecture guides
└── packages/
    └── shared/                 # Shared TS types
```
