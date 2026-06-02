Listed directory braintrain
Listed directory packages
Listed directory apps
Listed directory api
Listed directory app
Listed directory ai
Listed directory core
Listed directory modules
Listed directory orchestrators
Listed directory intelligence
Listed directory providers
Listed directory memory
Listed directory retrieval
Listed directory behavior
Listed directory orchestrator
Listed directory strategic
Listed directory state
Listed directory session
Listed directory policies
Listed directory prompts
Listed directory communication
Listed directory knowledge
Listed directory adaptive
Listed directory ingestion
Listed directory retrieval
Listed directory rules
Listed directory clients
Listed directory coaching
Listed directory evaluation
Viewed model_orchestrator.py:1-657
Viewed instrumentation.py:1-382
Viewed retrieval_pipeline.py:1-412
Viewed context_orchestrator.py:1-779
Viewed model_clients.py:1-368
Viewed hallucination_rules.py:1-371
Viewed turn_orchestrator.py:1-582
Viewed evaluation_orchestrator.py:1-570
Viewed realtime_orchestrator.py:1-684
Viewed session_coverage_planner.py:1-560
Viewed pressure_escalation_engine.py:1-266
Viewed behavior_engine.py:1-271
Viewed rule_engine.py:1-187
Viewed langchain_coach.py:1-78
Listed directory usage
Viewed recovery_tracker.py:1-350

Based on thorough exploration of the codebase, here is the complete list of AI Engineering and LLM concepts implemented in the BrainTrain application:

---

## AI Engineering & LLM Concepts Implemented

### Core LLM Infrastructure
1. **Multi-Provider LLM Routing** — OpenAI, NVIDIA NIM, Groq, local vLLM via a unified client
2. **Model Orchestration** — Task-based routing to optimal models per task type
3. **Fallback Chains** — Cascading provider fallbacks (primary → secondary → rule-based)
4. **Latency Budget Enforcement** — Per-provider latency budgets with SLA tracking
5. **Retry Logic with Exponential Backoff**
6. **Provider Health Monitoring** — Real-time health scores per provider
7. **Streaming Completions** — SSE-based token streaming
8. **JSON Mode / Structured Output** — Enforced structured responses from LLMs

### RAG (Retrieval-Augmented Generation)
9. **Vector Similarity Search** — pgvector cosine distance for semantic retrieval
10. **Hybrid Retrieval** — Semantic + keyword (full-text) search fusion
11. **Reranking Pipeline** — Score boosting by domain/topic + diversity filtering
12. **Token-Budgeted Context Assembly** — Priority-weighted multi-source context packing

### Prompt Engineering
13. **Task-Specific System Prompts** — Per-task context injection (evaluation, coaching, follow-up, etc.)
14. **Structured Prompt Templates** — LangChain-based template system with STAR/PREP frameworks
15. **Dynamic Prompt Construction** — Phase-aware and pressure-level-aware prompt building

### Agents & Orchestration
16. **Multi-Layer Orchestrator Architecture** — Turn → Session → Evaluation → Context → Realtime layers
17. **Deterministic Turn Decision Engine** — Rule-based routing overrides LLM routing decisions
18. **Session Coverage Planner** — Competency breadth tracking with deterministic pivot directives
19. **Speculative Pre-Generation** — Predicts likely next actions and pre-generates responses
20. **Parallel Pipeline Execution** — STT, Evaluation, and Context Assembly run concurrently

### Guardrails & Safety
21. **Hallucination Prevention Rules** — Verified candidate profile enforcement; blocks unverified entity references
22. **Rule Engine** — Blocker/Warning severity rules evaluated pre-generation
23. **Topic Boundary Rules** — Prevents out-of-scope questions
24. **Realism Rules** — Enforces interview realism constraints
25. **Evaluation Rules** — Consistent scoring guard-rails

### Evaluation Systems
26. **Hybrid Evaluation** — Rule-based (60%) + LLM-based (40%) score fusion
27. **Multi-Dimensional Scoring** — Communication, STAR structure, technical depth, ownership, impact
28. **Evaluation Caching** — Dedup identical evaluations for latency reduction
29. **Disagreement Detection** — Flags rule vs. LLM score divergence > 20 points
30. **Batch Evaluation** — Parallel `asyncio.gather` over multiple answers

### Cognitive / Behavioral Systems
31. **Behavior Engine** — Company-culture-specific interviewer personality (Amazon, Google, Meta, Netflix)
32. **Adaptive Pressure Escalation** — 5-level pressure curve (Warm-up → Adversarial → Recovery)
33. **Topic Fixation Detection** — Breadth guard; redirects candidate when fixated on a single concept
34. **Recovery Arc State Machine** — STABLE → STUMBLE → RECOVERY_ATTEMPT → RECOVERED/COLLAPSED
35. **Stumble Attribution** — Labels stumbles as candidate-error vs interviewer-loop vs pressure-induced
36. **Escalation Policy** — Detects stuck/confused/off-topic patterns and overrides turn action

### Communication Intelligence
37. **Uncertainty Language Detection** — Filler word and hedge scoring
38. **Executive Presence Scoring** — Ownership and impact language detection
39. **STAR/PREP Structure Analysis** — Narrative structure scoring
40. **Narrative Flow Analysis** — Fragmentation and rambling detection
41. **Strategic Reasoning Path Analysis** — Tradeoff thinking and reasoning sequence detection

### LLMOps / Observability
42. **OpenTelemetry Distributed Tracing** — Spans across all orchestrator operations
43. **Custom Metrics (Histograms + Counters)** — Latency histograms, fallback counters, active session gauges
44. **OTLP Export** — Jaeger-compatible trace/metric export
45. **Token Usage Tracking** — Per-call token estimation and tracking
46. **Provider Stats Dashboard** — Success rate, p95 latency, health score per provider

### Knowledge Management
47. **Knowledge Document Ingestion Pipeline** — Chunking and embedding storage
48. **Knowledge Playbooks** — Domain-specific interview knowledge bases
49. **Embedding-based Chunk Storage** — pgvector with 1536-dim embeddings

### Framework Integrations
50. **LangChain Integration** — `ChatOpenAI` with conversation memory for coaching
51. **Groq Transcription** — STT via Groq API
52. **OpenAI Whisper Transcription** — STT fallback via OpenAI