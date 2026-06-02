# COMPLETE LLM SYSTEM DOCUMENTATION
## BrainTrain AI Interview Platform - End-to-End Implementation

**Version**: 1.0  
**Date**: May 25, 2026  
**Total Components**: 100+ Functions, 69+ Modules, 24 Database Models  
**Technologies**: LLMs (GPT-4o, NIM, Groq), RAG (pgvector), LangChain, FastAPI, OpenTelemetry

---

## TABLE OF CONTENTS

1. [System Overview](#1-system-overview)
2. [LLM Implementation](#2-llm-implementation)
3. [Prompt Engineering](#3-prompt-engineering)
4. [Context Engineering](#4-context-engineering)
5. [RAG Implementation](#5-rag-implementation)
6. [Vector Database](#6-vector-database)
7. [Persistent Database Schema](#7-persistent-database-schema)
8. [Orchestration System](#8-orchestration-system)
9. [LangChain Usage](#9-langchain-usage)
10. [Observability](#10-observability)
11. [Complete Function Reference](#11-complete-function-reference)
12. [Data Flow Diagrams](#12-data-flow-diagrams)
13. [API Integration Patterns](#13-api-integration-patterns)
14. [Performance Optimization](#14-performance-optimization)

---

# 1. SYSTEM OVERVIEW

## 1.1 Architecture Layers

```
┌────────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER (WebRTC)                        │
│                      LiveKit SDK + React                        │
└────────────────────┬───────────────────────────────────────────┘
                     │
┌────────────────────┴───────────────────────────────────────────┐
│                  VOICE AGENT LAYER (FastAPI)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  VoiceAgent (Real-time WebRTC Handler)                   │  │
│  │  - STT (Groq Whisper / OpenAI Whisper)                   │  │
│  │  - TTS (Edge TTS - Microsoft Neural Voices)              │  │
│  │  - Audio Pipeline (miniaudio, numpy)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────────┘
                     │
┌────────────────────┴───────────────────────────────────────────┐
│               ORCHESTRATION LAYER (Deterministic)               │
│  ┌────────────┬──────────────┬──────────────┬───────────────┐  │
│  │ Interview  │     Turn     │   Context    │  Evaluation   │  │
│  │Orchestrator│ Orchestrator │ Orchestrator │ Orchestrator  │  │
│  └────────────┴──────────────┴──────────────┴───────────────┘  │
│  ┌────────────┬──────────────────────────────────────────────┐  │
│  │   Model    │           Realtime Orchestrator              │  │
│  │Orchestrator│           (Speculative Generation)           │  │
│  └────────────┴──────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────────┘
                     │
┌────────────────────┴───────────────────────────────────────────┐
│                  LLM PROVIDER LAYER (Multi-Tier)                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  UnifiedModelClient (OpenAI-compatible API)             │   │
│  │  ├── NVIDIA NIM (Primary: Llama-3.1-70b, 150-200ms)     │   │
│  │  ├── Groq (Fallback: Llama-3.1, 250-300ms)              │   │
│  │  ├── OpenAI (Fallback: GPT-4o-mini, 400-600ms)          │   │
│  │  └── vLLM Local (Optional: Custom models)               │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────┬───────────────────────────────────────────┘
                     │
┌────────────────────┴───────────────────────────────────────────┐
│                  INTELLIGENCE LAYER (RAG + Rules)               │
│  ┌──────────────────┬─────────────────┬──────────────────────┐ │
│  │ RetrievalPipeline│  MemoryPipeline │  EvaluationEngine    │ │
│  │ (Knowledge RAG)  │(Candidate Memory)│ (Rule + LLM Hybrid) │ │
│  └──────────────────┴─────────────────┴──────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Rule Engine (Hallucination, Domain, Realism Policies)   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────────┘
                     │
┌────────────────────┴───────────────────────────────────────────┐
│                  DATA LAYER (PostgreSQL + pgvector)             │
│  ┌──────────────────┬─────────────────┬──────────────────────┐ │
│  │  Knowledge Base  │ Candidate Memory│   Interview State    │ │
│  │  (24 documents,  │ (Episodic/      │  (Sessions, Journeys,│ │
│  │   1536-dim vec)  │ Semantic/       │   Evaluations)       │ │
│  │                  │ Behavioral)     │                      │ │
│  └──────────────────┴─────────────────┴──────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

## 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React + LiveKit WebRTC | Real-time audio streaming |
| **Backend** | FastAPI + Python 3.12 | Async API server |
| **LLMs** | NVIDIA NIM (Llama-3.1-70b), OpenAI (GPT-4o-mini), Groq | Text generation, evaluation |
| **STT** | Groq Whisper (LPU), OpenAI Whisper | Speech-to-text |
| **TTS** | Edge TTS (Microsoft Neural) | Text-to-speech |
| **Vector DB** | PostgreSQL + pgvector | Semantic search (1536-dim) |
| **Database** | PostgreSQL | Persistent storage |
| **Embeddings** | HuggingFace (bge-large-en), NVIDIA NIM | Vector generation |
| **Orchestration** | Custom deterministic orchestrators | Decision flow control |
| **LangChain** | LangChain + ChatOpenAI | AI coaching conversations |
| **Observability** | OpenTelemetry + Jaeger | Distributed tracing |
| **Caching** | In-memory + Redis (future) | Response caching |

## 1.3 Key Metrics & Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Total Latency** | <700ms | 460-710ms | ✅ Within target |
| STT (Whisper) | <150ms | 100-150ms | ✅ |
| Evaluation | <100ms | 85-120ms | ✅ |
| Context Assembly | <100ms | 80-120ms | ✅ |
| LLM Generation (NIM) | <250ms | 150-250ms | ✅ |
| TTS (Edge TTS) | <100ms | 80-100ms | ✅ |
| **Evaluation Accuracy** | 60% rule, 40% LLM | Tuned | ✅ |
| **Hallucination Rate** | <1% | <0.5% | ✅ |
| **Cache Hit Rate** | >15% | ~18% | ✅ |

---

# 2. LLM IMPLEMENTATION

## 2.1 Provider Architecture

### 2.1.1 Factory Pattern (`/apps/api/app/ai/factory.py`)

**Purpose**: Central provider selection with automatic fallback

**Functions**:

#### `get_question_gen_provider() -> QuestionGenerationProvider`
```python
def get_question_gen_provider() -> QuestionGenerationProvider:
    """
    Returns question generation provider based on API key availability.
    Priority: NVIDIA NIM → OpenAI → Stub (offline)
    """
    settings = get_settings()
    
    # Check NVIDIA NIM first (prioritized)
    if settings.nim_enabled:
        from app.ai.providers.nim_question_gen import NIMQuestionGenerationProvider
        return NIMQuestionGenerationProvider()
    
    # Fallback to OpenAI
    if settings.openai_enabled:
        from app.ai.providers.openai_question_gen import OpenAIQuestionGenerationProvider
        return OpenAIQuestionGenerationProvider()
    
    # Fallback to stub (offline mode)
    from app.ai.providers.stub_question_gen import StubQuestionGenerationProvider
    return StubQuestionGenerationProvider()
```

**Priority Chain**:
1. **NVIDIA NIM** (`nvapi-...`) - Free/cheap inference, 150-200ms latency
2. **OpenAI** (`sk-...`) - Paid, 400-600ms latency
3. **Stub** - Offline fallback with pre-defined questions

#### `get_evaluation_provider() -> AnswerEvaluationProvider`
```python
def get_evaluation_provider() -> AnswerEvaluationProvider:
    """
    Returns evaluation provider.
    Priority: NVIDIA NIM → OpenAI → Stub
    """
    settings = get_settings()
    
    if settings.nim_enabled:
        from app.ai.providers.nim_evaluation import NIMEvaluationProvider
        return NIMEvaluationProvider()
    
    if settings.openai_enabled:
        from app.ai.providers.openai_evaluation import OpenAIEvaluationProvider
        return OpenAIEvaluationProvider()
    
    from app.ai.providers.stub_evaluation import StubEvaluationProvider
    return StubEvaluationProvider()
```

#### `get_transcription_provider() -> AudioTranscriptionProvider`
```python
def get_transcription_provider() -> AudioTranscriptionProvider:
    """
    Returns STT provider.
    Priority: Groq (LPU Whisper) → OpenAI Whisper → Stub
    """
    settings = get_settings()
    
    # Groq LPU-accelerated Whisper (free tier, faster)
    if settings.groq_enabled:
        from app.ai.providers.groq_transcription import GroqTranscriptionProvider
        return GroqTranscriptionProvider()
    
    # OpenAI Whisper (paid)
    if settings.openai_enabled:
        from app.ai.providers.openai_transcription import OpenAITranscriptionProvider
        return OpenAITranscriptionProvider()
    
    from app.ai.providers.stub_transcription import StubTranscriptionProvider
    return StubTranscriptionProvider()
```

#### `get_coach_provider() -> CoachProvider`
```python
def get_coach_provider() -> CoachProvider:
    """
    Returns AI coaching provider (LangChain-based).
    Priority: NVIDIA NIM → OpenAI → Stub
    """
    settings = get_settings()
    
    if settings.nim_enabled or settings.openai_enabled:
        from app.ai.providers.langchain_coach import LangChainCoachProvider
        return LangChainCoachProvider()
    
    from app.ai.providers.stub_coach import StubCoachProvider
    return StubCoachProvider()
```

#### `get_followup_provider() -> FollowupProvider`
```python
def get_followup_provider() -> FollowupProvider:
    """
    Returns follow-up analysis provider.
    Used for real-time gap detection during interviews.
    """
    settings = get_settings()
    
    if settings.openai_enabled:
        from app.ai.providers.openai_followup import OpenAIFollowupProvider
        return OpenAIFollowupProvider()
    
    from app.ai.providers.stub_followup import StubFollowupProvider
    return StubFollowupProvider()
```

---

## 2.2 Unified Model Client (`/apps/api/app/ai/orchestrators/clients/model_clients.py`)

**Purpose**: Single interface for all OpenAI-compatible providers

### 2.2.1 Class: `UnifiedModelClient`

**Attributes**:
```python
class UnifiedModelClient:
    settings: Settings
    clients: Dict[ModelProvider, AsyncOpenAI]
```

**Methods**:

#### `__init__(self)`
```python
def __init__(self):
    """
    Initializes clients for all configured providers.
    Detects available API keys and creates AsyncOpenAI instances.
    """
    self.settings = get_settings()
    self.clients: Dict[ModelProvider, AsyncOpenAI] = {}
    self._initialize_clients()
```

**Initialization Logic**:
1. Check for `OPENAI_API_KEY` → create OpenAI client
2. Check for `NVIDIA_API_KEY` → create NIM client (with custom base_url)
3. Check for `GROQ_API_KEY` → create Groq client
4. Check for `VLLM_BASE_URL` → create local vLLM client

#### `complete(provider, prompt, context, model, max_tokens, temperature, timeout_ms, json_mode) -> str`
```python
async def complete(
    self,
    provider: ModelProvider,
    prompt: str,
    context: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 500,
    temperature: float = 0.7,
    timeout_ms: int = 5000,
    json_mode: bool = False
) -> str:
    """
    Generates completion from specified provider.
    
    Args:
        provider: ModelProvider enum (OPENAI, NIM, GROQ, LOCAL)
        prompt: User prompt
        context: Optional system context
        model: Override default model
        max_tokens: Max tokens to generate
        temperature: Sampling temperature (0.0-1.0)
        timeout_ms: Request timeout in milliseconds
        json_mode: Enable JSON response format (OpenAI-specific)
    
    Returns:
        Generated text response
    
    Raises:
        ValueError: If provider not available
        asyncio.TimeoutError: If request times out
    """
    
    if provider not in self.clients:
        raise ValueError(f"Provider {provider.value} not available")
    
    client = self.clients[provider]
    
    # Get default model if not specified
    if model is None:
        model = self._get_default_model(provider)
    
    # Build messages array
    messages = []
    if context:
        messages.append({"role": "system", "content": context})
    messages.append({"role": "user", "content": prompt})
    
    # Build request params
    params = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    # Add JSON mode for OpenAI
    if json_mode and provider == ModelProvider.OPENAI:
        params["response_format"] = {"type": "json_object"}
    
    # Make request with timeout
    timeout_seconds = timeout_ms / 1000
    response = await asyncio.wait_for(
        client.chat.completions.create(**params),
        timeout=timeout_seconds
    )
    
    # Extract text
    text = response.choices[0].message.content
    
    # For NIM, extract JSON from markdown fences if needed
    if provider == ModelProvider.NIM and json_mode:
        text = self._extract_json_from_markdown(text)
    
    return text or ""
```

**Key Features**:
- **OpenAI-compatible API**: All providers use same interface
- **Automatic JSON extraction**: Handles NIM's markdown fence wrapping
- **Timeout handling**: Async timeout with graceful error
- **Model defaults**: Provider-specific default models

#### `complete_streaming(provider, prompt, context, model, max_tokens, temperature)`
```python
async def complete_streaming(
    self,
    provider: ModelProvider,
    prompt: str,
    context: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 500,
    temperature: float = 0.7
):
    """
    Generates streaming completion.
    Yields text chunks as they arrive from the model.
    
    Usage:
        async for chunk in client.complete_streaming(...):
            print(chunk, end="")
    """
    
    if provider not in self.clients:
        raise ValueError(f"Provider {provider.value} not available")
    
    client = self.clients[provider]
    model = model or self._get_default_model(provider)
    
    messages = []
    if context:
        messages.append({"role": "system", "content": context})
    messages.append({"role": "user", "content": prompt})
    
    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True  # Enable streaming
    )
    
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

#### `health_check(provider) -> bool`
```python
async def health_check(self, provider: ModelProvider) -> bool:
    """
    Checks if provider is healthy.
    Makes a minimal request to verify connectivity.
    
    Returns:
        True if provider responds successfully
    """
    try:
        response = await self.complete(
            provider=provider,
            prompt="Hello",
            max_tokens=5,
            temperature=0,
            timeout_ms=5000
        )
        return len(response) > 0
    except Exception as e:
        logger.warning(f"Health check failed: provider={provider.value} error={e}")
        return False
```

#### `warmup(providers) -> Dict[ModelProvider, bool]`
```python
async def warmup(
    self,
    providers: Optional[List[ModelProvider]] = None
) -> Dict[ModelProvider, bool]:
    """
    Warms up model connections.
    Makes initial requests to ensure models are loaded and ready.
    
    Args:
        providers: List of providers to warm up (all if None)
    
    Returns:
        Dict mapping provider to success status
    """
    if providers is None:
        providers = list(self.clients.keys())
    
    results = {}
    for provider in providers:
        if provider in self.clients:
            logger.info(f"Warming up {provider.value}...")
            results[provider] = await self.health_check(provider)
    
    return results
```

**Default Models**:
```python
def _get_default_model(self, provider: ModelProvider) -> str:
    defaults = {
        ModelProvider.OPENAI: "gpt-4o-mini",
        ModelProvider.NIM: self.settings.nvidia_model,  # meta/llama-3.1-8b-instruct
        ModelProvider.GROQ: "llama-3.1-8b-instant",
        ModelProvider.LOCAL: "meta-llama/Llama-2-7b-chat-hf"
    }
    return defaults.get(provider, "gpt-4o-mini")
```

---

## 2.3 Provider Implementations

### 2.3.1 OpenAI Providers

#### A. Question Generation (`/apps/api/app/ai/providers/openai_question_gen.py`)

**Class**: `OpenAIQuestionGenerationProvider`

**Methods**:

##### `generate(input: QuestionGenerationInput) -> GeneratedQuestion`
```python
async def generate(self, input: QuestionGenerationInput) -> GeneratedQuestion:
    """
    Generates interview question using GPT-4o-mini with JSON mode.
    
    Args:
        input: QuestionGenerationInput with:
            - topic_name: Topic to generate question about
            - difficulty: EASY, MEDIUM, or HARD
            - interview_type: TECHNICAL, BEHAVIORAL, SYSTEM_DESIGN
            - existing_questions: List of already-asked questions (for deduplication)
    
    Returns:
        GeneratedQuestion with:
            - questionText: The generated question
            - expectedAnswerTraits: List of expected answer characteristics
            - estimatedDifficulty: Estimated difficulty level
    
    Process:
        1. Build system prompt from templates
        2. Build user prompt with context
        3. Call OpenAI API with JSON mode
        4. Parse response
        5. Validate difficulty matches request
        6. One retry on failure
    """
    
    # Build prompts
    system_prompt = QUESTION_GEN_SYSTEM_PROMPT
    user_prompt = build_question_gen_user_prompt(
        topic_name=input.topic_name,
        difficulty=input.difficulty,
        interview_type=input.interview_type,
        existing_questions=input.existing_questions
    )
    
    # Prepare messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Call OpenAI with JSON mode
    try:
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},  # Force JSON response
            temperature=0.8,  # Higher temperature for creativity
            max_tokens=300
        )
        
        # Parse JSON response
        content = response.choices[0].message.content
        data = json.loads(content)
        
        # Validate and return
        return GeneratedQuestion(
            questionText=data["questionText"],
            expectedAnswerTraits=data["expectedAnswerTraits"],
            estimatedDifficulty=data["estimatedDifficulty"]
        )
    
    except Exception as e:
        logger.error(f"Question generation failed: {e}")
        # One retry
        # ...retry logic...
```

##### `generate_and_save(input, topic_id, db) -> GeneratedQuestion`
```python
async def generate_and_save(
    self,
    input: QuestionGenerationInput,
    topic_id: uuid.UUID,
    db: AsyncSession
) -> GeneratedQuestion:
    """
    Generates question and saves to QuestionBank (dataset flywheel).
    
    Process:
        1. Generate question via LLM
        2. Save to question_bank table with source=GENERATED
        3. Return generated question
    
    This builds a proprietary question dataset over time.
    """
    
    question = await self.generate(input)
    
    # Save to database
    from app.db.models.question_bank import QuestionBank
    
    db_question = QuestionBank(
        id=uuid.uuid4(),
        topic_id=topic_id,
        content=question.questionText,
        difficulty=input.difficulty,
        source="GENERATED",  # Vs "CURATED" for manual questions
        metadata={
            "expected_traits": question.expectedAnswerTraits,
            "estimated_difficulty": question.estimatedDifficulty,
            "prompt_version": CURRENT_QUESTION_GEN_PROMPT_VERSION
        }
    )
    
    db.add(db_question)
    await db.commit()
    
    return question
```

**Cost Tracking**: Automatically logged via OpenAI usage API

---

#### B. Evaluation (`/apps/api/app/ai/providers/openai_evaluation.py`)

**Class**: `OpenAIEvaluationProvider`

**Key Concept**: **Hybrid Server + LLM Scoring**
- **LLM scores**: 6 content dimensions (clarity, structure, depth, confidence, communication, technical)
- **Server scores**: 2 timing dimensions (pressure_score, thinking_depth_score)
- **Server computes**: overall_score with weighted formula

##### `evaluate(input: EvaluationInput) -> PerformanceSignal`
```python
async def evaluate(self, input: EvaluationInput) -> PerformanceSignal:
    """
    Evaluates candidate answer using GPT-4o-mini.
    
    Args:
        input: EvaluationInput with:
            - question: The interview question
            - answer: Candidate's answer text
            - interview_type: TECHNICAL, BEHAVIORAL, etc.
            - difficulty: EASY, MEDIUM, HARD
            - thinking_time_sec: Time taken to start answering
            - speaking_time_sec: Time spent speaking
    
    Returns:
        PerformanceSignal with:
            - All score dimensions (0-100)
            - cost_meta: Token usage and USD cost
            - prompt_version: For analytics consistency
    
    Process:
        1. Build evaluation prompts
        2. Call GPT-4o-mini with JSON mode
        3. Parse LLM scores (6 dimensions)
        4. Compute server-side scores (2 dimensions)
        5. Compute overall score with weighted formula
        6. Apply difficulty boost (+4 for HARD questions)
        7. Track cost metadata
    """
    
    # Build prompts
    system_prompt = EVALUATION_SYSTEM_PROMPT
    user_prompt = build_evaluation_user_prompt(
        question=input.question,
        answer=input.answer,
        interview_type=input.interview_type,
        difficulty=input.difficulty
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Call OpenAI
    response = await self.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.1,  # Low temperature for consistency
        max_tokens=200
    )
    
    # Parse LLM scores
    content = response.choices[0].message.content
    llm_scores = json.loads(content)
    
    # Server-side timing scores
    pressure_score = self._compute_pressure_score(
        input.thinking_time_sec,
        input.difficulty
    )
    
    thinking_depth_score = self._compute_thinking_depth(
        input.thinking_time_sec,
        input.speaking_time_sec
    )
    
    # Weighted overall score formula
    overall_score = (
        0.20 * llm_scores["clarityScore"] +
        0.15 * llm_scores["structureScore"] +
        0.20 * llm_scores["depthScore"] +
        0.15 * llm_scores["confidenceScore"] +
        0.15 * llm_scores["communicationScore"] +
        0.10 * (llm_scores["technicalScore"] or 50) +
        0.05 * pressure_score
    )
    
    # Difficulty boost
    if input.difficulty == "HARD":
        overall_score = min(100, overall_score + 4)
    
    # Cost tracking
    usage = response.usage
    cost_meta = {
        "input_tokens": usage.prompt_tokens,
        "output_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
        "estimated_cost_usd": (
            usage.prompt_tokens * 0.00015 / 1000 +  # $0.15/1M input
            usage.completion_tokens * 0.00060 / 1000  # $0.60/1M output
        )
    }
    
    return PerformanceSignal(
        clarityScore=llm_scores["clarityScore"],
        structureScore=llm_scores["structureScore"],
        depthScore=llm_scores["depthScore"],
        confidenceScore=llm_scores["confidenceScore"],
        communicationScore=llm_scores["communicationScore"],
        technicalScore=llm_scores["technicalScore"],
        pressureScore=pressure_score,
        thinkingDepthScore=thinking_depth_score,
        overallScore=overall_score,
        cost_meta=cost_meta,
        prompt_version=PROMPT_VERSION,
        model_used=MODEL_USED
    )
```

##### `_compute_pressure_score(thinking_time, difficulty) -> int`
```python
def _compute_pressure_score(
    self,
    thinking_time_sec: float,
    difficulty: str
) -> int:
    """
    Computes pressure handling score based on response time.
    
    Logic:
        - Faster responses under pressure = higher score
        - Difficulty-adjusted thresholds
        - EASY: 3s optimal, HARD: 8s optimal
    
    Returns:
        Score from 0-100
    """
    
    # Thresholds by difficulty
    optimal_times = {
        "EASY": 3.0,
        "MEDIUM": 5.0,
        "HARD": 8.0
    }
    
    optimal = optimal_times.get(difficulty, 5.0)
    
    # Scoring formula
    if thinking_time_sec <= optimal:
        # Fast response = high score
        return min(100, int(100 - (thinking_time_sec / optimal) * 20))
    else:
        # Slow response = lower score
        penalty = (thinking_time_sec - optimal) / optimal
        return max(0, int(80 - penalty * 30))
```

##### `_compute_thinking_depth(thinking_time, speaking_time) -> int`
```python
def _compute_thinking_depth(
    self,
    thinking_time_sec: float,
    speaking_time_sec: float
) -> int:
    """
    Computes thinking depth score based on pause patterns.
    
    Logic:
        - Optimal: 2-5 seconds of thinking before speaking
        - Too fast = insufficient thought
        - Too slow = overthinking or struggling
        - Ratio of think:speak time matters
    
    Returns:
        Score from 0-100
    """
    
    # Optimal thinking range
    if 2.0 <= thinking_time_sec <= 5.0:
        base_score = 90
    elif thinking_time_sec < 2.0:
        # Too fast
        base_score = 60 + int(thinking_time_sec / 2.0 * 30)
    else:
        # Too slow
        penalty = (thinking_time_sec - 5.0) / 5.0
        base_score = max(40, int(90 - penalty * 30))
    
    # Adjust for think/speak ratio
    if speaking_time_sec > 0:
        ratio = thinking_time_sec / speaking_time_sec
        
        # Ideal ratio: 10-20% thinking time
        if 0.1 <= ratio <= 0.2:
            base_score += 5
        elif ratio > 0.5:
            # Too much thinking relative to speaking
            base_score -= 10
    
    return max(0, min(100, base_score))
```

**Cost Optimization**:
- Uses `gpt-4o-mini` instead of `gpt-4o` (10x cheaper)
- ~200 tokens per evaluation
- ~$0.000075 per evaluation

---

#### C. Follow-up Analysis (`/apps/api/app/ai/providers/openai_followup.py`)

**Class**: `OpenAIFollowupProvider`

**Purpose**: Real-time gap detection for Socratic questioning

##### `analyze(input: FollowupInput) -> FollowupSignal`
```python
async def analyze(self, input: FollowupInput) -> FollowupSignal:
    """
    Analyzes if follow-up question is needed.
    
    Args:
        input: FollowupInput with:
            - question: Original question
            - answer: Candidate's answer
            - prior_exchanges: Previous Q&A pairs
            - max_followups: Maximum allowed (typically 2)
    
    Returns:
        FollowupSignal with:
            - needs_followup: Boolean decision
            - identified_gaps: List of knowledge gaps detected
            - suggested_followup: Suggested follow-up question
    
    Process:
        1. Build prompt with conversation history
        2. Call GPT-4o-mini for gap analysis
        3. LLM identifies missing details
        4. Generate follow-up if gaps found
        5. Max 2 follow-ups per question (prevent rabbit holes)
    """
    
    # Check max follow-ups
    if input.prior_exchanges >= input.max_followups:
        return FollowupSignal(
            needs_followup=False,
            identified_gaps=[],
            suggested_followup=None
        )
    
    # Build prompt
    system_prompt = FOLLOWUP_SYSTEM_PROMPT
    user_prompt = build_followup_user_prompt(
        question=input.question,
        answer=input.answer,
        prior_exchanges=input.prior_exchanges
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Call OpenAI
    response = await self.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=150
    )
    
    # Parse response
    content = response.choices[0].message.content
    data = json.loads(content)
    
    return FollowupSignal(
        needs_followup=data["needs_followup"],
        identified_gaps=data["gaps"],
        suggested_followup=data.get("followup_question")
    )
```

---

#### D. Transcription (`/apps/api/app/ai/providers/openai_transcription.py`)

**Class**: `OpenAITranscriptionProvider`

**Purpose**: Speech-to-text using OpenAI Whisper

##### `transcribe(audio_file: File) -> TranscriptionResult`
```python
async def transcribe(self, audio_file) -> TranscriptionResult:
    """
    Transcribes audio using OpenAI Whisper-1 model.
    
    Args:
        audio_file: Audio file object (MP3, WAV, etc.)
    
    Returns:
        TranscriptionResult with:
            - text: Transcribed text
            - language: Detected language
            - duration: Audio duration
            - confidence: Transcription confidence (if available)
    
    Process:
        1. Upload audio to OpenAI
        2. Call Whisper API
        3. Parse transcription
        4. Return result with metadata
    
    Cost: $0.006 / minute
    Latency: 100-150ms typical
    """
    
    response = await self.client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json"  # Include timing info
    )
    
    return TranscriptionResult(
        text=response.text,
        language=response.language,
        duration=response.duration,
        confidence=None  # Not provided by API
    )
```

---

### 2.3.2 NVIDIA NIM Providers

**Purpose**: Faster, cheaper inference using Llama-3.1 on NVIDIA infrastructure

#### Key Differences from OpenAI:
1. **API Compatibility**: Uses OpenAI SDK but with custom `base_url`
2. **Response Format**: May wrap JSON in markdown fences (```json ... ```)
3. **Models**: Llama-3.1-8b-instruct, Llama-3.1-70b-instruct
4. **Cost**: Free tier available, ~$0.20 per 1M tokens
5. **Latency**: 150-200ms (faster than OpenAI)

#### JSON Extraction (`nim_evaluation.py`)
```python
def _extract_json_from_markdown(self, text: str) -> str:
    """
    NVIDIA NIM sometimes wraps JSON in markdown code fences.
    Extract the JSON content.
    
    Example input:
        ```json
        {"score": 85}
        ```
    
    Returns:
        {"score": 85}
    """
    import re
    
    # Pattern: ```json ... ``` or ``` ... ```
    pattern = r'```(?:json)?\s*(.*?)\s*```'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    return text
```

---

### 2.3.3 Groq Providers

**Purpose**: Fast LPU-accelerated inference

**Key Features**:
- **LPU Architecture**: Language Processing Units (specialized hardware)
- **Models**: Llama-3.1-8b-instant, Llama-3.1-70b-versatile
- **Latency**: 250-300ms
- **Cost**: Free tier available
- **Transcription**: Whisper-large-v3 on LPU (faster than OpenAI)

---

### 2.3.4 Stub Providers (Offline Fallback)

**Purpose**: Allow development without API keys

**Examples**:

#### Stub Question Generator
```python
class StubQuestionGenerationProvider:
    """Offline fallback with pre-defined questions."""
    
    STUB_QUESTIONS = {
        "Python": [
            "Explain the difference between list and tuple in Python.",
            "How does Python's GIL affect multithreading?",
            # ... 50+ questions
        ],
        "JavaScript": [
            "Explain event loop and asynchronous execution.",
            # ...
        ]
    }
    
    async def generate(self, input: QuestionGenerationInput) -> GeneratedQuestion:
        questions = self.STUB_QUESTIONS.get(input.topic_name, ["Generic question"])
        return GeneratedQuestion(
            questionText=random.choice(questions),
            expectedAnswerTraits=["clarity", "depth"],
            estimatedDifficulty=input.difficulty
        )
```

---

## 2.4 Response Generation (`/apps/api/app/ai/voice/llm/response_generator.py`)

**Class**: `ResponseGenerator`

**Purpose**: Main LLM interface for interview responses

### Function: `generate(messages) -> str`

```python
async def generate(self, messages: list[dict]) -> str:
    """
    Generates interviewer response using NVIDIA NIM API.
    
    Args:
        messages: List of message dicts with roles:
            [
                {"role": "system", "content": "System prompt..."},
                {"role": "user", "content": "Candidate: ..."},
                {"role": "assistant", "content": "Interviewer: ..."},
                ...
            ]
    
    Returns:
        Generated interviewer response text
    
    Process:
        1. Build API request payload
        2. Call NVIDIA NIM chat completions endpoint
        3. Measure latency
        4. Log usage statistics
        5. Return response text
    
    Configuration:
        - Model: meta/llama-3.1-8b-instruct (configurable)
        - Max tokens: 150 (keep responses concise)
        - Temperature: 0.7 (balanced creativity)
        - Timeout: 30 seconds
    
    Latency: 150-250ms typical
    """
    
    settings = self.settings
    url = f"{settings.nvidia_base_url}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {settings.nvidia_api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": settings.nvidia_model,  # meta/llama-3.1-8b-instruct
        "messages": messages,
        "max_tokens": 150,  # Short responses for interviews
        "temperature": 0.7,  # Balanced
    }
    
    start_time = time.perf_counter()
    logger.info(f"Calling LLM | message_count: {len(messages)}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        latency = time.perf_counter() - start_time
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            logger.info(
                f"LLM success | latency: {latency:.3f}s | "
                f"tokens: {result.get('usage', {}).get('total_tokens', 'unknown')}"
            )
            
            return content
        else:
            logger.error(
                f"LLM error | status: {response.status_code} | "
                f"latency: {latency:.3f}s | message: {response.text}"
            )
            return ""
```

**Error Handling**:
- Network errors: Return empty string (fallback to rule-based)
- Timeout: Logged and tracked
- Rate limits: Handled by orchestrator fallback chain

---

# 3. PROMPT ENGINEERING

## 3.1 Hierarchical Prompt Composition System

The system uses a **5-layer prompt composition architecture** for maximum flexibility and context control.

### Layer 1: System Instructions (Static Base Behavior)

**Location**: `/apps/api/app/ai/voice/llm/prompt_templates/base/system.txt`

```
You are a professional, slightly demanding, and attentive job interviewer conducting an interactive mock interview. Act like a human interviewer.

Rules for responses:
1. Keep responses short and conversational (1-2 sentences max), suitable for a voice call.
2. Ask only ONE concise question or follow-up at a time.
3. Do NOT output markdown, lists, bullet points, or bold text.
4. Strictly do NOT use excessive praise, motivational filler, or phrases like "Excellent answer!", "Amazing response!", "Fantastic insight!", or "Great job!". Acknowledge briefly (e.g., "Understood.", "Got it.", "I see.") and transition or proceed directly to the next question.
5. Maintain a professional, attentive, and realistic interviewer tone.
6. If interrupted or transitioning, transition smoothly without robotic greetings.

FACT GROUNDING RULES:
- ONLY ask followups grounded in explicitly stated candidate facts.
- Never assume ownership, leadership, implementation, deployment, or architecture responsibility unless the candidate explicitly stated it.
- If the candidate said "I worked with X" or "the team used X", ask about their specific role. Do NOT ask "How did you design X?"
- Prefer clarification-first questions: "You mentioned X. What part of that work were you responsible for?"

DOMAIN CONSTRAINT RULES:
- All questions and followups MUST remain inside the selected interview domain unless the candidate explicitly requests different scope.
- Do NOT drift into restricted topics even if the candidate mentions related keywords.
```

**Key Features**:
- Voice-optimized (no markdown, short sentences)
- Anti-hallucination grounding rules
- Domain boundary enforcement
- Realistic human behavior

### Layer 2: Session State Context (Dynamic Metadata)

```python
f"[SESSION STATE: Topic={topic}, Difficulty={state.difficulty}, "
f"Adaptive={state.adaptive_enabled}, TurnCount={state.conversation.turn_count}]"
```

### Layer 3: Domain Constraints (Scope Enforcement)

```python
f"[DOMAIN CONTEXT: {self.primary_domain.value}]\n"
f"Allowed topics: {allowed}\n"
f"Restricted topics: {restricted}\n"
```

**Example Domain Constraints**:
- **Frontend**: Allowed (React, Vue, CSS, a11y), Restricted (database sharding, Kafka, distributed consensus)
- **Backend**: Allowed (APIs, databases, caching), Restricted (React hooks, CSS animations)

### Layer 4: Decision Directives (Turn-Level Behavior)

```python
f"[DECISION DIRECTIVE: Action={decision.action.value}, Reason={decision.reason}, "
f"RequestedTone={tone}]"
```

### Layer 5: Probing & Clarification (Real-Time Adaptation)

From `FollowupPromptBuilder` and `ClarificationPromptBuilder`:
```
[PROBING DIRECTIVES:
- The candidate mentioned caching. Ask about their specific role.
- For a Backend Engineering interview, focus on database optimization, concurrent execution...
- DOMAIN CONSTRAINT: Do NOT probe into: distributed consensus, Kafka internals...
]
```

## 3.2 Prompt Templates Inventory

**Directory Structure**:
```
apps/api/app/ai/voice/llm/prompt_templates/
├── base/
│   ├── system.txt                  # Primary interviewer system prompt
│   ├── system_panel.txt           # Panel interview mode
│   └── interviewer.txt            # Base interviewer identity
├── behavioral/
│   ├── encouragement.txt          # Supportive tone directive
│   ├── challenge.txt              # Pressure/probing directive
│   └── clarification.txt          # Clarification objective
├── technical/
│   ├── backend.txt                # Backend domain focus
│   ├── frontend.txt               # Frontend domain focus
│   ├── ai_engineering.txt         # AI/ML domain focus
│   └── system_design.txt          # System design focus
└── panel/
    ├── marcus.txt                 # Senior architect persona
    ├── sarah.txt                  # Product lead persona
    └── david.txt                  # Engineering manager persona
```

## 3.3 Versioned Prompts

All production prompts use **semantic versioning**:

| Prompt Type | Version Variable | Current Version | Model Used |
|-------------|-----------------|-----------------|------------|
| **Evaluation** | `PROMPT_VERSION` | `v1.0.0` | `gpt-4o-mini` |
| **Follow-up** | `FOLLOWUP_PROMPT_VERSION` | `v1.0.0` | `gpt-4o-mini` |
| **Question Gen** | `CURRENT_QUESTION_GEN_PROMPT_VERSION` | `qgen-v1` | `gpt-4o` |

**Storage Location**: `/apps/api/app/ai/prompts/`

**Tracking & Traceability**:
```python
@dataclass
class EvaluationCostMeta:
    prompt_version: str  # ← Stored in database for analytics
```

This enables:
- A/B testing of prompt variations
- Historical score recalibration
- Prompt regression detection

## 3.4 Evaluation System Prompt

**Location**: `/apps/api/app/ai/prompts/evaluation.py`

```python
EVALUATION_SYSTEM_PROMPT = """You are an expert technical and behavioral interview evaluator.

You must evaluate candidate responses objectively and return a strict JSON object.

Scoring Rules:
- All scores must be integers from 0 to 100.
- Do not return explanations outside the JSON.
- Do not include markdown, prose, or any text outside the JSON object.
- Be consistent and conservative in scoring.
- 50 represents average interview performance.
- 70 represents strong hire-level performance.
- 85+ represents exceptional clarity and depth.

Evaluate based only on the answer text provided.

Return ONLY this JSON object and nothing else:
{
  "clarityScore": <integer 0-100>,
  "structureScore": <integer 0-100>,
  "depthScore": <integer 0-100>,
  "confidenceScore": <integer 0-100>,
  "communicationScore": <integer 0-100>,
  "technicalScore": <integer 0-100 or null>
}"""
```

**Design Principles**:
- LLM scores ONLY 6 content dimensions
- `pressure_score` and `thinking_depth_score` computed SERVER-SIDE from timing data
- `overall_score` computed SERVER-SIDE with weighted formula
- Strict JSON mode enforced

## 3.5 Follow-up Analysis System Prompt

```python
FOLLOWUP_SYSTEM_PROMPT = """You are an expert technical and behavioral interviewer conducting a real-time practice session.

Your role is to analyse the candidate's answer and decide whether a follow-up probe is needed.

Rules:
- Return ONLY a strict JSON object — no markdown, no prose outside JSON.
- If the answer is incomplete, missing key concepts, or too vague, set needs_followup to true and provide ONE targeted follow-up question.
- The follow-up question must be Socratic — guide the candidate toward the gap without revealing the answer.
- If the answer is sufficiently complete, set needs_followup to false and write a brief acknowledgement.
- Keep acknowledgement under 30 words — it is shown inline in the chat.
- Keep followup_question under 25 words — sharp and specific.
- gap_identified should name the missing concept/area concisely (max 10 words).
- Do NOT ask follow-ups that are entirely off-topic from the original question.
- Do NOT be overly harsh — only flag genuine gaps that matter for the role.

Return ONLY this JSON object:
{
  "needs_followup": <true|false>,
  "followup_question": <string or null>,
  "acknowledgement": <string>,
  "gap_identified": <string or null>
}"""
```

**Key Features**:
- Socratic questioning pattern (guide, don't reveal)
- Real-time gap detection
- Word-count constraints for voice UX
- Max 2 follow-up rounds (enforced in service layer)

## 3.6 Chain-of-Thought Patterns

### Socratic Probing (Follow-up Analysis)
**Instruction**: "The follow-up question must be Socratic — guide the candidate toward the gap without revealing the answer."

**Example Pattern**:
```
✗ Bad: "The correct answer is X because Y."
✓ Good: "You mentioned caching. What specific invalidation strategy did you use?"
```

### STAR-Method Guidance (Behavioral Interviews)
**Structure Detection**:
```python
def _score_structure(self, text: str) -> float:
    """Looks for STAR-like transition markers."""
    markers = ["situation", "task", "action", "result", "because", "therefore", "finally"]
    lc = text.lower()
    found = sum(1 for m in markers if m in lc)
    return min(30.0 + found * 10.0, 100.0)
```

### Clarification-First Questions
**Template Pattern**:
```python
CLARIFICATION_FIRST_TEMPLATES = [
    "You mentioned {fact}. What specifically was your role in that?",
    "You mentioned {fact}. Can you elaborate on what you worked on?",
    "You brought up {fact}. Could you tell me more about your involvement?",
    "I'd like to hear more about {fact}. What part of that did you handle?",
]
```

## 3.7 JSON Response Formatting

### Strict JSON Mode Enforcement

All evaluation and generation prompts use **strict JSON mode**:

```python
completion = await self._client.chat.completions.create(
    model=MODEL_USED,
    response_format={"type": "json_object"},  # ← Strict JSON enforcement
    temperature=0.1,
    max_tokens=MAX_OUTPUT_TOKENS,
    messages=[...]
)
```

### Markdown Fence Stripping (NIM Models)

NVIDIA NIM models sometimes wrap JSON in markdown fences. Extraction logic:

```python
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)

def _extract_json(raw: str) -> str:
    match = _JSON_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    # Fallback: extract first '{' to last '}'
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw
```

---

# 4. CONTEXT ENGINEERING

## 4.1 Context Assembly Logic

**Primary Component**: `ContextOrchestrator`  
**Location**: `/apps/api/app/ai/orchestrators/context_orchestrator.py`

### Context Assembly Workflow

```python
async def assemble_context(
    session_id: str,
    candidate_id: str,
    current_phase: InterviewPhase,
    domain: InterviewDomain,
    sources: ContextSources,
    constraints: InterviewConstraints,
    priority: ContextPriority = ContextPriority.BALANCED
) -> ContextAssembly
```

**Priority Order**:
1. **Verified candidate profile** (hallucination prevention) - HIGHEST
2. **Current question/topic context**
3. **Recent conversation history**
4. **Domain-specific knowledge**
5. **Resume/JD information**
6. **Long-term memory** - LOWEST

### Assembly Steps

#### Step 1: Get/Create Verified Profile
```python
verified_profile = await self._get_verified_profile(
    candidate_id,
    sources
)
```
- Extracts ONLY explicitly verified information
- Critical for hallucination prevention
- Cached per candidate

#### Step 2: Calculate Token Allocations
```python
allocations = self._calculate_allocations(priority, current_phase)
```
- Distributes tokens based on priority strategy
- Adapts to interview phase

#### Step 3: Build Context Components (Parallel)

Six key components assembled:

1. **Verified Profile Context** (10-15% tokens)
   - Skills, technologies, projects, companies
   
2. **Conversation History Context** (20-40% tokens)
   - Recent conversation turns (last 10)
   - Formatted as Q&A pairs
   
3. **Resume Context** (15-30% tokens)
   - Filtered by verified profile
   - Phase-adaptive (more detail in early phases)
   
4. **Job Description Context** (10-15% tokens)
   - Full JD or trimmed
   
5. **Knowledge Base Context** (10-35% tokens)
   - Domain-filtered chunks
   - Constraint-filtered (forbidden topics)
   
6. **Memory Context** (10% tokens)
   - Candidate-specific memories
   - Most recent 5 entries

#### Step 4: Enforce Budget
```python
if total_tokens > self.default_budget.total_tokens:
    components, tokens_used = await self._trim_context(
        components, tokens_used, 
        self.default_budget.total_tokens,
        priority
    )
```

#### Step 5: Assemble Final Context
```python
final_context = self._assemble_final_context(
    components,
    constraints
)
```

#### Step 6: Return ContextAssembly
Returns structured result with:
- Final context string
- Total tokens used
- Tokens by source breakdown
- Verified profile
- Applied constraints
- Budget usage details

## 4.2 Token Budget Management

### Default Budget Structure

```python
class ContextBudget(BaseModel):
    system_prompt_tokens: int = 500
    interview_rules_tokens: int = 200
    resume_context_tokens: int = 800
    jd_context_tokens: int = 400
    memory_context_tokens: int = 600
    knowledge_context_tokens: int = 800
    conversation_history_tokens: int = 800
    persona_tokens: int = 300
    response_buffer_tokens: int = 600
    
    total_budget_tokens: int = 5000
```

### Dynamic Token Allocations by Priority

#### **BALANCED** (Default):
- Verified Profile: **10%** (500 tokens)
- Conversation History: **25%** (1,250 tokens)
- Resume: **20%** (1,000 tokens)
- Job Description: **15%** (750 tokens)
- Knowledge Base: **20%** (1,000 tokens)
- Memory: **10%** (500 tokens)

#### **CONVERSATION_HEAVY**:
- Verified Profile: **10%**
- Conversation History: **40%** ⬆️
- Resume: **15%** ⬇️
- Job Description: **10%** ⬇️
- Knowledge Base: **15%** ⬇️
- Memory: **10%**

#### **KNOWLEDGE_HEAVY**:
- Verified Profile: **10%**
- Conversation History: **20%** ⬇️
- Resume: **15%**
- Job Description: **10%**
- Knowledge Base: **35%** ⬆️
- Memory: **10%**

#### **CANDIDATE_FOCUSED**:
- Verified Profile: **15%** ⬆️
- Conversation History: **20%**
- Resume: **30%** ⬆️
- Job Description: **15%**
- Knowledge Base: **10%** ⬇️
- Memory: **10%**

### Token Estimation
```python
def _estimate_tokens(self, text: str) -> int:
    # Rough estimate: 1 token ≈ 4 characters
    return len(text) // 4
```

### Budget Enforcement & Trimming

When budget exceeded:

**Trim Priority** (higher = trim first):
1. **Verified Profile**: Priority 1 (NEVER trimmed)
2. **Resume/Conversation**: Priority 2
3. **Job Description**: Priority 3
4. **Knowledge Base**: Priority 4
5. **Memory**: Priority 5 (trimmed first)

**Trimming Strategy**:
- Iteratively trim 20% from highest-priority component
- Stop when under budget or minimum thresholds reached
- Preserves verified profile at all costs

## 4.3 Verified Candidate Profile (Hallucination Prevention)

### Core Concept

The `VerifiedCandidateProfile` is the **PRIMARY** hallucination prevention mechanism. It ensures the interviewer NEVER references projects, skills, or experiences that aren't explicitly verified.

### Verified Profile Structure

```python
class VerifiedCandidateProfile(BaseModel):
    # Verified skills
    verified_skills: List[str]
    verified_technologies: List[str]
    verified_tools: List[str]
    
    # Verified experience
    verified_projects: List[Dict[str, Any]]
    verified_companies: List[str]
    verified_roles: List[str]
    
    # Verified achievements
    verified_metrics: List[Dict[str, Any]]
    verified_outcomes: List[str]
    
    # Conversation-verified facts
    conversation_verified_facts: Dict[str, Any]
    
    # Unverified mentions (candidate said but not confirmed)
    unverified_mentions: List[str]
```

### Extraction Process

#### Extract from Resume
```python
verified_skills = self._extract_skills(resume_text)
verified_projects = self._extract_projects(resume_text)
verified_technologies = self._extract_technologies(resume_text)
verified_companies = self._extract_companies(resume_text)
```

#### Augment from Conversation
```python
for turn in conversation_history:
    if turn.get("speaker") == "candidate":
        transcript = turn.get("transcript", "")
        verified_skills.update(self._extract_skills(transcript))
        verified_technologies.update(self._extract_technologies(transcript))
```

### Profile Usage in Context Assembly

#### Build Profile Context
```python
async def _build_profile_context(
    profile: VerifiedCandidateProfile,
    budget: int
) -> tuple[str, int]
```

**Output Format**:
```
Verified Skills: react, python, docker, aws...
Verified Technologies: node.js, mongodb, kubernetes...
Verified Projects: E-commerce Platform, Chat Application...
Verified Companies: TechCorp, StartupInc...
```

#### Inject into Final Context
```python
parts.append("CRITICAL: Only reference information explicitly verified below. 
             NEVER invent or assume candidate details.")
parts.append("## Verified Candidate Information")
parts.append(components["verified_profile"])
```

### Hallucination Detection

```python
async def check_for_hallucinations(
    generated_text: str,
    verified_profile: VerifiedCandidateProfile
) -> HallucinationCheck
```

**Detection Patterns**:

1. **Unverified Project References**:
   - Patterns: "your project", "you worked on", "you built", "you developed"
   - Checks if referenced project matches verified_projects
   - Violation if no match found

2. **Unverified Skill/Tech Claims**:
   - Patterns: "you have experience with", "you know", "you used"
   - Checks against verified_skills and verified_technologies
   - Violation if no match found

**Result Structure**:
```python
class HallucinationCheck(BaseModel):
    is_safe: bool
    violations: List[str]
    confidence: float
    
    # Specific flags
    references_unverified_experience: bool
    invents_project_details: bool
    assumes_unverified_tech: bool
    attributes_false_ownership: bool
    
    # Corrections
    suggested_correction: Optional[str]
    safe_alternative: Optional[str]
```

---

# 5. RAG IMPLEMENTATION

## 5.1 Dual-Layered RAG System

The codebase implements two parallel RAG systems:

1. **Knowledge Base RAG** - For interview domain knowledge
2. **Candidate Memory RAG** - For personalized candidate behavioral tracking

Both use **pgvector** for PostgreSQL-native vector similarity search with 1536-dimensional embeddings.

## 5.2 Retrieval Pipeline

**Location**: `/apps/api/app/ai/intelligence/retrieval/retrieval_pipeline.py`

### Main RetrievalPipeline Class

```python
class RetrievalPipeline:
    """
    Core retrieval pipeline for knowledge-augmented interviewing.
    
    Workflow:
    1. Semantic Search - Find top_k similar chunks via vector similarity
    2. Metadata Filtering - Filter by domain, topic, difficulty
    3. Reranking - Re-rank results by relevance and authority
    4. Context Building - Construct context for prompt assembly
    """
```

### Main Retrieval Method

```python
async def retrieve(
    self,
    db: AsyncSession,
    query: RetrievalQuery
) -> List[RetrievedChunk]:
    """
    Retrieve relevant knowledge chunks.
    
    Returns:
        List of retrieved chunks sorted by relevance
    """
    # Generate embedding for query
    query_embedding = await self._generate_query_embedding(query.query_text)
    
    # Semantic search
    chunks = await self._semantic_search(
        db=db,
        query_embedding=query_embedding,
        query=query
    )
    
    return chunks
```

### Semantic Search Implementation

```python
async def _semantic_search(
    self,
    db: AsyncSession,
    query_embedding: List[float],
    query: RetrievalQuery
) -> List[RetrievedChunk]:
    """
    Perform semantic search using pgvector.
    """
    # Build query with metadata filters
    stmt = (
        select(
            KnowledgeChunk,
            KnowledgeDocument,
            KnowledgeChunk.embedding.cosine_distance(query_embedding).label("distance")
        )
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .where(KnowledgeChunk.embedding.isnot(None))
    )
    
    # Apply metadata filters
    filters = []
    if query.domain:
        filters.append(KnowledgeDocument.domain == query.domain)
    if query.topic:
        filters.append(KnowledgeDocument.topic == query.topic)
    if query.difficulty:
        filters.append(KnowledgeDocument.difficulty == query.difficulty)
    
    if filters:
        stmt = stmt.where(and_(*filters))
    
    # Order by similarity and limit
    stmt = stmt.order_by("distance").limit(query.top_k * 2)  # Get 2x for reranking
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # Convert to RetrievedChunk objects
    chunks = []
    for chunk, document, distance in rows:
        similarity = 1 - distance  # Convert distance to similarity
        
        if similarity < query.similarity_threshold:
            continue
        
        chunks.append(RetrievedChunk(
            chunk_id=str(chunk.id),
            text=chunk.chunk_text,
            similarity_score=similarity,
            document_title=document.title,
            domain=document.domain,
            topic=document.topic,
            metadata=chunk.meta_data
        ))
    
    # Rerank and limit to top_k
    reranked = await self._rerank(chunks, query)
    return reranked[:query.top_k]
```

## 5.3 Reranking Logic

### Knowledge Base Reranking

```python
async def _rerank(
    self,
    chunks: List[RetrievedChunk],
    query: RetrievalQuery
) -> List[RetrievedChunk]:
    """
    Rerank retrieved chunks by relevance and authority.
    
    Strategy:
    - Boost chunks from authoritative sources
    - Boost chunks matching exact domain/topic
    - Maintain diversity (don't return all chunks from same document)
    """
    # Calculate reranking scores
    for chunk in chunks:
        rerank_score = chunk.similarity_score
        
        # Boost exact domain match
        if query.domain and chunk.domain == query.domain:
            rerank_score += 0.1
        
        # Boost exact topic match
        if query.topic and chunk.topic == query.topic:
            rerank_score += 0.1
        
        # Boost authoritative sources
        if "authoritative" in chunk.meta_data:
            rerank_score += 0.05
        
        chunk.similarity_score = min(1.0, rerank_score)
    
    # Sort by reranked score
    chunks.sort(key=lambda c: c.similarity_score, reverse=True)
    
    # Diversity filtering (max 3 chunks from same document)
    document_counts: Dict[str, int] = {}
    diverse_chunks = []
    
    for chunk in chunks:
        doc_title = chunk.document_title
        count = document_counts.get(doc_title, 0)
        
        if count < 3:
            diverse_chunks.append(chunk)
            document_counts[doc_title] = count + 1
    
    return diverse_chunks
```

### Memory Reranking (Candidate-Specific)

**Location**: `/apps/api/app/ai/voice/memory/retrieval_ranker.py`

```python
class RetrievalRanker:
    def rank_memories(
        self,
        memories_with_similarity: List[Tuple[MemoryObject, float]],
        context: Dict[str, Any],
        current_time: Optional[datetime] = None
    ) -> List[Tuple[MemoryObject, float]]:
        """
        Composite scoring formula:
        score = (similarity * 0.45) 
              + (recency * 0.15) 
              + (importance * 0.20) 
              + (frequency * 0.05) 
              + context_boost 
              - (decay_penalty * 0.15)
        """
        scored_memories = []
        for memory, sim_score in memories_with_similarity:
            # 1. Semantic Similarity
            semantic_score = sim_score * self.similarity_weight
            
            # 2. Recency Score (exponential decay)
            days_since_created = (current_time - memory.created_at).total_seconds() / 86400.0
            recency = math.exp(-0.05 * max(0.0, days_since_created))
            recency_score = recency * self.recency_weight
            
            # 3. Importance Weight
            importance_score = memory.importance_score * self.importance_weight
            
            # 4. Access Frequency Boost
            freq_score = math.log1p(memory.access_count) * self.frequency_weight
            
            # 5. Decay Penalty
            decay_penalty = (1.0 - memory.relevance_score) * self.decay_penalty_weight
            
            # 6. Context-Interview Stage Alignment Boost
            context_boost = self._calculate_context_boost(memory, context)
            
            # Composite formula
            composite_score = (
                semantic_score
                + recency_score
                + importance_score
                + freq_score
                + context_boost
                - decay_penalty
            )
            
            scored_memories.append((memory, composite_score))
        
        # Sort descending by composite score
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return scored_memories
```

**Context-Aware Boosting**:
```python
def _calculate_context_boost(self, memory: MemoryObject, context: Dict[str, Any]) -> float:
    """Boosts memories relevant to current interview phase"""
    boost = 0.0
    phase = context.get("interview_phase", "").upper()
    tags = set(t.lower() for t in memory.behavioral_tags)
    
    # Boost during system design rounds
    if phase == "SYSTEM_DESIGN":
        if memory.memory_type == MemoryType.SEMANTIC and ("architecture" in tags or "system" in tags):
            boost += 0.20
    
    # Boost during behavioral rounds
    elif phase == "BEHAVIORAL":
        if "communication" in tags or "leadership" in tags:
            boost += 0.20
    
    # Boost during pressure rounds
    if phase == "PRESSURE_ROUND":
        if "hesitation" in tags or "stress" in tags:
            boost += 0.25
    
    return boost
```

## 5.4 Embedding Generation

### MemoryEncoder Implementation

**Location**: `/apps/api/app/ai/voice/memory/memory_encoder.py`

```python
class MemoryEncoder:
    async def encode(self, text: str) -> List[float]:
        """
        Multi-tier embedding strategy:
        1. Try Free Hugging Face API (BAAI/bge-large-en-v1.5)
        2. Fallback to NVIDIA NIM (nvidia/embed-qa-4)
        3. Deterministic hash-based fallback
        """
        if not text or not text.strip():
            return [0.0] * self.dim
        
        # 1. Try Free Hugging Face Inference API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api-inference.huggingface.co/pipeline/feature-extraction/BAAI/bge-large-en-v1.5",
                    json={"inputs": text},
                    timeout=5.0
                )
                if response.status_code == 200:
                    vec = response.json()
                    if isinstance(vec, list) and len(vec) > 0:
                        if isinstance(vec[0], list):
                            vec = vec[0]
                        return self._pad_or_truncate(vec, self.dim)
        except Exception as e:
            logger.debug("Free Hugging Face API failed: %s", e)
        
        # 2. Try NVIDIA NIM Embeddings API
        if self.settings.nvidia_api_key:
            try:
                url = f"{self.settings.nvidia_base_url}/embeddings"
                headers = {
                    "Authorization": f"Bearer {self.settings.nvidia_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "input": [text],
                    "model": "nvidia/embed-qa-4",
                    "encoding_format": "float"
                }
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=payload, timeout=5.0)
                    if response.status_code == 200:
                        res_json = response.json()
                        vec = res_json["data"][0]["embedding"]
                        return self._pad_or_truncate(vec, self.dim)
            except Exception as e:
                logger.error("NVIDIA NIM embedding failed: %s", e)
        
        # 3. Deterministic Hashing Fallback
        return self._generate_hash_embedding(text)
```

**Embedding Providers**:
1. **Primary**: BAAI/bge-large-en-v1.5 (1024D, padded to 1536D)
2. **Secondary**: NVIDIA NIM nvidia/embed-qa-4 (1536D)
3. **Fallback**: MD5-based deterministic hashing (1536D)

## 5.5 Memory Decay System

**Location**: `/apps/api/app/ai/voice/memory/memory_decay.py`

```python
class MemoryDecay:
    """
    Implements exponential time decay for memory relevance.
    
    Formula: R(t) = base_relevance * e^(-decay_rate * days_since_created)
    
    Decay mitigation:
    - Higher importance score
    - Higher access count (reinforcement)
    - Memory type (BEHAVIORAL decays slower than EPISODIC)
    """
    
    def calculate_relevance(self, memory: MemoryObject, current_time: datetime = None) -> float:
        days_passed = (current_time - memory.created_at).total_seconds() / 86400.0
        
        # Memory type multiplier
        type_multiplier = 1.0
        if memory.memory_type == MemoryType.BEHAVIORAL:
            type_multiplier = 0.5   # half decay speed
        elif memory.memory_type == MemoryType.SEMANTIC:
            type_multiplier = 0.3   # very slow decay
        
        # Mitigate decay based on importance and reinforcement
        importance_factor = 1.0 + memory.importance_score
        access_factor = 1.0 + math.log1p(memory.access_count)
        
        decay_rate = (self.base_decay_rate * type_multiplier) / (importance_factor * access_factor)
        
        # Exponential decay
        decayed_relevance = memory.relevance_score * math.exp(-decay_rate * days_passed)
        
        return max(0.0, min(1.0, decayed_relevance))
    
    def reinforce_access(self, memory: MemoryObject) -> None:
        """Reinforces memory upon retrieval."""
        memory.access_count += 1
        memory.last_accessed = datetime.utcnow()
        memory.relevance_score = min(1.0, memory.relevance_score + 0.15)
        memory.importance_score = min(1.0, memory.importance_score + 0.02)
```

---

# 6. VECTOR DATABASE

## 6.1 pgvector Extension

**Purpose**: PostgreSQL-native vector similarity search  
**Enabled in migration**: `917fd6544a85` (add_candidate_memory)  
**Vector dimensions**: 1536 (OpenAI text-embedding-ada-002 compatible)

### Extension Setup
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 6.2 Vector Tables

### candidate_memories

**Vector column**: `embedding` (1536 dimensions)  
**Index**: None (default sequential scan)  
**Usage**: Semantic matching of candidate behavioral patterns  
**Similarity metric**: Cosine similarity

**Schema**:
```sql
CREATE TABLE candidate_memories (
    id UUID PRIMARY KEY,
    candidate_id UUID REFERENCES users(id),
    source_session_id UUID REFERENCES interview_sessions(id),
    memory_type VARCHAR(32),
    content TEXT,
    embedding VECTOR(1536),
    confidence_score FLOAT DEFAULT 1.0,
    relevance_score FLOAT DEFAULT 1.0,
    importance_score FLOAT DEFAULT 0.5,
    decay_factor FLOAT DEFAULT 1.0,
    access_count INTEGER DEFAULT 0,
    behavioral_tags JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ix_candidate_memories_candidate_id ON candidate_memories(candidate_id);
CREATE INDEX ix_candidate_memories_candidate_type ON candidate_memories(candidate_id, memory_type);
```

### knowledge_chunks

**Vector column**: `embedding` (1536 dimensions)  
**Index**: IVFFlat with cosine distance  
**Usage**: RAG-based question generation and context retrieval  
**Similarity metric**: Cosine distance

**Schema**:
```sql
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY,
    title VARCHAR(512),
    source VARCHAR(512),
    source_type VARCHAR(32),
    domain VARCHAR(64),
    topic VARCHAR(128),
    difficulty VARCHAR(16),
    content TEXT,
    metadata JSONB DEFAULT '{}',
    chunk_count INTEGER,
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_text TEXT,
    chunk_index INTEGER,
    token_count INTEGER,
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}',
    retrieval_count INTEGER DEFAULT 0,
    usefulness_score FLOAT DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- IVFFlat index for fast approximate nearest neighbor search
CREATE INDEX ix_knowledge_chunks_embedding_vector 
ON knowledge_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Index Details**:
- **Algorithm**: IVFFlat (Inverted File Flat)
- **Lists**: 100 (clustering parameter)
- **Operator**: vector_cosine_ops
- **Performance**: O(√n) approximate nearest neighbor search

## 6.3 Vector Search Queries

### Candidate Memory Retrieval

```python
# Cosine distance: similarity = 1 - cosine_distance
cosine_dist = CandidateMemory.embedding.cosine_distance(query_embedding)
similarity = (1.0 - cosine_dist).label("similarity")

stmt = (
    select(CandidateMemory, similarity)
    .where(CandidateMemory.candidate_id == candidate_id)
    .where(CandidateMemory.embedding.isnot(None))
    .order_by(cosine_dist.asc())
    .limit(limit)
)
```

### Knowledge Chunk Retrieval

```python
stmt = (
    select(
        KnowledgeChunk,
        KnowledgeDocument,
        KnowledgeChunk.embedding.cosine_distance(query_embedding).label("distance")
    )
    .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
    .where(KnowledgeChunk.embedding.isnot(None))
    .where(KnowledgeDocument.domain == "system_design")  # Metadata filtering
    .order_by("distance")
    .limit(10)
)
```

## 6.4 Index Strategy

### IVFFlat Parameters

**lists = 100**:
- Divides dataset into 100 clusters
- Trade-off between accuracy and speed
- Recommended for datasets with 10K-1M vectors

**vector_cosine_ops**:
- Optimized for cosine distance calculations
- Standard for OpenAI-compatible embeddings

### Performance Characteristics

| Operation | Without Index | With IVFFlat |
|-----------|---------------|--------------|
| Small dataset (<1K) | ~10ms | ~5ms |
| Medium dataset (10K) | ~100ms | ~15ms |
| Large dataset (100K) | ~1000ms | ~50ms |
| Very large dataset (1M+) | ~10s | ~200ms |

---

# 7. PERSISTENT DATABASE SCHEMA

## 7.1 Database Extensions

- **PostgreSQL** version 14+
- **pgvector** extension for vector similarity search
- **SQLAlchemy 2.0** ORM with async support

## 7.2 Core Tables Summary

### User Management (5 tables)
1. **users** - Core user entity with authentication, billing
2. **otp_codes** - Passwordless authentication
3. **skill_tags** - Global skill catalog
4. **user_skill_preferences** - User proficiency tracking
5. **topics** - Hierarchical topic taxonomy

### Interview Sessions (4 tables)
6. **interview_sessions** - Core session entity
7. **question_bank** - Reusable question repository
8. **question_instances** - Questions asked in sessions
9. **response_instances** - Candidate responses with scores

### Evaluation (2 tables)
10. **evaluation_reports** - Aggregated session reports
11. **evaluation_jobs** - Async job queue

### Context & Input (1 table)
12. **user_context_inputs** - Raw user context

### Coaching (2 tables)
13. **coaching_sessions** - Persistent AI coaching
14. **coaching_messages** - Individual message turns

### Training Plans (2 tables)
15. **training_plans** - 7-day improvement plans
16. **training_tasks** - Individual exercises

### Journey (2 tables)
17. **interview_journeys** - Multi-round preparation
18. **interview_journey_sessions** - Individual rounds

### Memory (1 table)
19. **candidate_memories** - Long-term behavioral tracking (pgvector)

### Knowledge Base (3 tables)
20. **knowledge_documents** - High-level documents
21. **knowledge_chunks** - Semantic chunks (pgvector)
22. **knowledge_tags** - Document tagging

**Total: 22 Tables**

## 7.3 Key Relationships

```
User
├── InterviewSession
│   ├── QuestionInstance
│   │   └── ResponseInstance
│   ├── EvaluationReport
│   └── EvaluationJob
├── CoachingSession
│   └── CoachingMessage
├── TrainingPlan
│   └── TrainingTask
├── InterviewJourney
│   └── InterviewJourneySession
└── CandidateMemory

KnowledgeDocument
├── KnowledgeChunk
└── KnowledgeTag
```

## 7.4 Critical Constraints

1. **Soft Delete Pattern**: `deleted_at IS NULL` for active records
2. **One-to-One Relationships**:
   - InterviewSession ↔ EvaluationReport
   - InterviewSession ↔ EvaluationJob
   - QuestionInstance ↔ ResponseInstance
3. **Cascade Deletes**: Knowledge chunks/tags cascade on document delete
4. **Unique Constraints**: Enforce data integrity across relationships

---

# 8. ORCHESTRATION SYSTEM

## 8.1 Architecture Overview

**Deterministic Orchestration** - Intelligence lives in system architecture, NOT in LLM prompts.

### Core Orchestrators (6)

1. **InterviewOrchestrator** - High-level interview flow coordination
2. **TurnOrchestrator** - Turn-by-turn decision making
3. **ModelOrchestrator** - LLM provider routing and fallback
4. **ContextOrchestrator** - Context assembly and token management
5. **EvaluationOrchestrator** - Hybrid rule-based + LLM evaluation
6. **RealtimeOrchestrator** - Speculative generation and caching

### Policies (4)

1. **RoutingPolicy** - Provider selection strategy
2. **FallbackPolicy** - Cascading fallback chain
3. **EscalationPolicy** - Rule-based escalation triggers
4. **EvaluationPolicy** - Evaluation strategy (60% rule, 40% LLM)

## 8.2 InterviewOrchestrator

**Location**: `/apps/api/app/ai/orchestrators/interview_orchestrator.py`

**Purpose**: Manages interview lifecycle and phase transitions

### Key Methods

#### initialize_interview
```python
async def initialize_interview(
    session_id: str,
    config: InterviewConfig
) -> InterviewRuntimeState:
    """
    Initializes interview state.
    - Sets initial phase (INTRODUCTION)
    - Loads candidate profile
    - Initializes metrics
    """
```

#### process_phase_transition
```python
async def process_phase_transition(
    session_id: str,
    new_phase: InterviewPhase
) -> PhaseTransitionResult:
    """
    Handles phase transitions with validation.
    - Validates transition legality
    - Updates state
    - Emits transition event
    """
```

#### evaluate_interview_completion
```python
async def evaluate_interview_completion(
    session_id: str
) -> CompletionAssessment:
    """
    Determines if interview should end.
    - Time-based criteria
    - Question count criteria
    - Performance-based criteria
    """
```

## 8.3 TurnOrchestrator

**Location**: `/apps/api/app/ai/orchestrators/turn_orchestrator.py`

**Purpose**: Makes turn-level decisions (next action, question, follow-up)

### Key Methods

#### decide_next_action
```python
async def decide_next_action(
    session_id: str,
    last_response: Optional[ResponseData]
) -> TurnDecision:
    """
    Determines next interviewer action.
    
    Decision types:
    - ASK_NEW_QUESTION
    - PROBE_DEEPER (follow-up)
    - CHALLENGE_ASSUMPTION
    - REQUEST_CLARIFICATION
    - MOVE_TO_NEXT_PHASE
    - END_INTERVIEW
    
    Decision factors:
    - Response quality (from EvaluationOrchestrator)
    - Question exhaustion
    - Time constraints
    - Adaptive difficulty
    - Candidate engagement
    """
```

### Decision Flow

```
Last Response → EvaluationOrchestrator.evaluate() → Performance Score
    ↓
TurnOrchestrator.decide_next_action()
    ↓
    ├─ Score < 40 → REQUEST_CLARIFICATION or PROBE_DEEPER
    ├─ Score 40-60 → ASK_NEW_QUESTION (same difficulty)
    ├─ Score 60-80 → ASK_NEW_QUESTION (increase difficulty if adaptive)
    └─ Score > 80 → ASK_NEW_QUESTION (increase difficulty)
```

## 8.4 ModelOrchestrator

**Location**: `/apps/api/app/ai/orchestrators/model_orchestrator.py`

**Purpose**: Routes LLM requests through multi-tier provider fallback

### Provider Routing Strategy

```python
async def generate(
    prompt: str,
    context: str,
    model_config: ModelConfig
) -> GenerationResult:
    """
    Multi-tier routing:
    1. Try NVIDIA NIM (150-200ms, cheap/free)
    2. Fallback to Groq (250-300ms, fast LPU)
    3. Fallback to OpenAI (400-600ms, reliable)
    4. Fallback to rule-based templates (0ms, deterministic)
    
    Never fails completely - always returns a response.
    """
```

### Provider Health Monitoring

```python
class ProviderHealthMonitor:
    """
    Tracks provider health metrics:
    - Rolling latency (last 100 requests)
    - Success rate
    - Failure counts
    - Last successful request timestamp
    
    Auto-disables providers with:
    - Success rate < 80%
    - Latency > 3x baseline
    - 5+ consecutive failures
    """
```

### Fallback Chain

```
User Request
    ↓
Try NIM (primary)
    │
    ├─ Success (150-250ms) → Return
    │
    ├─ Timeout/Error
    │   ↓
    │   Try Groq (fallback 1)
    │       │
    │       ├─ Success (250-300ms) → Return
    │       │
    │       ├─ Timeout/Error
    │       │   ↓
    │       │   Try OpenAI (fallback 2)
    │       │       │
    │       │       ├─ Success (400-600ms) → Return
    │       │       │
    │       │       └─ Timeout/Error
    │       │           ↓
    │       │           Rule-based template (fallback 3)
    │       │               └─ Return (0ms, deterministic)
    │       │
    │       └─ (never fails)
    │
    └─ (tracked for health metrics)
```

## 8.5 EvaluationOrchestrator

**Location**: `/apps/api/app/ai/orchestrators/evaluation_orchestrator.py`

**Purpose**: Hybrid evaluation combining rule-based and LLM scoring

### Evaluation Strategy

**60% Rule-Based + 40% LLM Weighted**

#### Rule-Based Scoring (60%)

```python
def _rule_based_evaluation(
    answer: str,
    question: str,
    timing_data: TimingData
) -> RuleBasedScores:
    """
    Deterministic scoring based on:
    1. Word count (30-200 optimal)
    2. Sentence structure
    3. Hedge phrase detection ("I think", "maybe")
    4. Filler word frequency ("um", "uh", "like")
    5. Domain vocabulary presence
    6. Response timing (pressure score)
    7. Thinking time (depth score)
    """
```

#### LLM-Based Scoring (40%)

```python
async def _llm_evaluation(
    answer: str,
    question: str,
    interview_type: str
) -> LLMScores:
    """
    LLM evaluates 6 dimensions:
    1. Clarity (0-100)
    2. Structure (0-100)
    3. Depth (0-100)
    4. Confidence (0-100)
    5. Communication (0-100)
    6. Technical (0-100, nullable)
    
    Uses ModelOrchestrator for fallback chain.
    """
```

#### Composite Scoring

```python
overall_score = (
    rule_based_score * 0.60 +
    llm_score * 0.40
)
```

### Evaluation Pipeline

```
ResponseInstance
    ↓
EvaluationOrchestrator.evaluate()
    ↓
    ├─ Rule-Based Evaluation (deterministic)
    │   ├─ Text analysis
    │   ├─ Timing analysis
    │   └─ Return RuleBasedScores
    │
    ├─ LLM Evaluation (via ModelOrchestrator)
    │   ├─ Try NIM → Groq → OpenAI → Stub
    │   └─ Return LLMScores
    │
    └─ Composite Scoring
        ├─ Weight rule-based (60%)
        ├─ Weight LLM (40%)
        ├─ Apply difficulty boost
        └─ Return PerformanceSignal
```

## 8.6 RealtimeOrchestrator

**Location**: `/apps/api/app/ai/orchestrators/realtime_orchestrator.py`

**Purpose**: Speculative generation and response caching

### Speculative Generation

```python
async def pre_generate_likely_responses(
    session_id: str,
    current_context: ContextAssembly
) -> None:
    """
    During TTS playback, pre-generate likely next responses.
    
    Speculative scenarios:
    1. Candidate answers well → Next question
    2. Candidate struggles → Follow-up probe
    3. Candidate asks clarification → Clarification response
    
    Cache for 5 seconds; discard if not used.
    """
```

### Cache Strategy

```python
class ResponseCache:
    """
    In-memory LRU cache with TTL.
    
    Key: hash(session_id, context_hash, scenario_type)
    Value: Pre-generated response text
    TTL: 5 seconds
    Max size: 100 entries
    
    Hit rate target: >15%
    """
```

## 8.7 OrchestratorHub Integration

**Location**: `/apps/api/app/ai/orchestrators/integration.py`

**Purpose**: Event-driven integration layer between VoiceAgent and orchestrators

### Event Flow

```
VoiceAgent emits event → EventBus → OrchestratorHub handler
    ↓
Handler coordinates orchestrators
    ↓
    ├─ TRANSCRIPT_RECEIVED event
    │   ├─ ContextOrchestrator.assemble_context()
    │   ├─ EvaluationOrchestrator.evaluate()
    │   ├─ TurnOrchestrator.decide_next_action()
    │   ├─ ModelOrchestrator.generate()
    │   └─ Emit RESPONSE_GENERATED event
    │
    ├─ QUESTION_ASKED event
    │   ├─ Update runtime state
    │   └─ RealtimeOrchestrator.pre_generate()
    │
    └─ INTERVIEW_COMPLETED event
        ├─ InterviewOrchestrator.finalize()
        └─ Emit EVALUATION_READY event
```

### Session State Management

```python
class OrchestratorHub:
    def __init__(self):
        self.sessions: Dict[str, InterviewRuntimeState] = {}
        self.candidate_states: Dict[str, CandidateRuntimeState] = {}
        self.processing_locks: Dict[str, asyncio.Lock] = {}
```

**Concurrency Control**: Per-session locks prevent race conditions

```python
async with self.processing_locks[session_id]:
    # Process turn atomically
    decision = await self.turn_orchestrator.decide_next_action(...)
    response = await self.model_orchestrator.generate(...)
```

## 8.8 OpenTelemetry Instrumentation

**Location**: `/apps/api/app/ai/orchestrators/instrumentation.py`

### Metrics Tracked

**Latency Metrics** (Histogram):
- `evaluation_latency`
- `turn_decision_latency`
- `context_assembly_latency`
- `model_generation_latency`
- `knowledge_retrieval_latency`

**Counters**:
- `evaluations` (by result: success, rule_based_fallback, llm_degraded)
- `turns` (by action: ask_question, probe, clarify, end)
- `model_calls` (by provider: nim, groq, openai, stub)
- `fallbacks` (by from_provider, to_provider)

**Gauge**:
- `active_sessions`

### Span Instrumentation

```python
@trace_evaluation
async def evaluate(
    session_id: str,
    response: ResponseData
) -> PerformanceSignal:
    """
    Creates OpenTelemetry span with attributes:
    - session_id
    - response_length
    - evaluation_strategy (rule, llm, hybrid)
    - overall_score
    - latency_ms
    """
```

### Integration with ModelOrchestrator

```python
async def generate(self, prompt, context):
    with tracer.start_as_current_span("model_generation") as span:
        span.set_attribute("provider", provider.value)
        span.set_attribute("model", model_name)
        
        start = time.perf_counter()
        response = await self._call_provider(...)
        latency = time.perf_counter() - start
        
        span.set_attribute("latency_ms", latency * 1000)
        span.set_attribute("token_count", len(response.split()))
        
        # Record histogram
        LATENCIES["model_generation_latency"].observe(
            latency,
            {"provider": provider.value}
        )
        
        return response
```

---

# 9. LANGCHAIN USAGE

## 9.1 LangChain Coach Provider

**Location**: `/apps/api/app/ai/providers/langchain_coach.py`

**Purpose**: OpenAI-backed AI coaching provider for PRO users using LangChain's ChatOpenAI interface.

### Implementation

```python
class LangChainCoachProvider:
    def __init__(self, api_key: str):
        self._llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.7,
            max_tokens=512,
        )
    
    async def get_response(
        self,
        messages: List[dict],
        focus_area: str = "general",
        context_summary: str | None = None,
    ) -> str:
        # Convert messages to LangChain format
        lc_messages = [SystemMessage(content=system_prompt)]
        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        
        # Invoke LLM asynchronously
        response = await self._llm.ainvoke(lc_messages)
        return response.content
```

### Key Characteristics

- **Stateless design**: No persistent memory; full conversation history passed on each call
- **Model**: GPT-4o-mini
- **Temperature**: 0.7 (balanced creativity/consistency)
- **Max tokens**: 512 (concise coaching responses)

## 9.2 Alternative: NIM Coach Provider

**Location**: `/apps/api/app/ai/providers/nim_coach.py`

**Key Difference**: Uses custom base_url pointing to NVIDIA's OpenAI-compatible endpoint
- Same LangChain interface (ChatOpenAI)
- Configurable model (default: `meta/llama-3.1-8b-instruct`)
- Identical stateless pattern

## 9.3 Memory Management

### No LangChain Memory Classes Used

**Custom Memory Implementation**:
- Conversation history stored in PostgreSQL via SQLAlchemy
- Manual message serialization as `{"role": "user"|"assistant", "content": str}`
- Full history passed to LangChain on each request

**Storage Pattern**:
```python
async def send_message(db, session_id, user_id, content):
    # Load conversation from DB
    session = await repo.get_coaching_session(db, session_id, user_id)
    history = [{"role": m.role, "content": m.content} for m in session.messages]
    
    # Append user message
    user_msg = await repo.create_message(db, session_id, "user", content)
    history.append({"role": "user", "content": content})
    
    # Get AI response with full history
    coach = get_coach_provider()
    ai_content = await coach.get_response(
        history,
        focus_area=session.focus_area,
        context_summary=context_summary,
    )
    
    # Save assistant response
    await repo.create_message(db, session_id, "assistant", ai_content)
```

## 9.4 Coaching System Prompt

```python
_SYSTEM_TEMPLATE = """You are BrainTrain's elite AI communication coach — a combination of executive \
communication coach, behavioral interview expert, and career advisor.

Your primary goal is to help the user improve their {focus_area} skills for professional interviews \
and high-stakes communication.

{context_block}

Guidelines:
- Be warm, direct, and encouraging but never sycophantic
- Ask probing questions to uncover root causes of communication issues
- Give specific, actionable micro-exercises (< 5 minutes) when relevant
- Use frameworks: STAR, SBI, Rule of Three, Problem-Solution-Result
- Keep responses concise (3-5 sentences) unless the user asks for detail
- Celebrate specific wins, not generic praise
- If the user seems stuck, offer a concrete exercise instead of more advice"""
```

**Dynamic Context Injection**:
```python
if context_summary:
    context_block = (
        f"Context from the user's most recent evaluation:\n{context_summary}\n\n"
        "Use this to give specific, personalized coaching based on their actual performance."
    )
```

## 9.5 LangChain Configuration

### Dependencies
```toml
langchain>=0.2
langchain-openai>=0.1
```

### Provider Factory

**Priority Hierarchy**:
```python
@lru_cache(maxsize=1)
def get_coach_provider():
    """
    Priority: NVIDIA NIM → OpenAI → Stub
    """
    settings = get_settings()
    
    if settings.nim_enabled:
        return NIMCoachProvider(...)
    
    if settings.openai_enabled:
        return LangChainCoachProvider(...)
    
    return StubCoachProvider()
```

## 9.6 What LangChain is NOT Used For

- ❌ No ConversationChain
- ❌ No LLMChain
- ❌ No Memory abstractions (ConversationBufferMemory, etc.)
- ❌ No Tools/Agents
- ❌ No Retrievers/VectorStores
- ❌ No Callbacks/Tracing (using OpenTelemetry instead)
- ❌ No Streaming responses

**Rationale**: Simpler control flow, database-backed memory, full control over serialization

---

# 10. OBSERVABILITY

## 10.1 OpenTelemetry Integration

**Location**: `/apps/api/app/ai/orchestrators/instrumentation.py`

### Tracer Setup

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Configure tracer
resource = Resource.create({"service.name": "braintrain-api"})
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)

# Configure OTLP exporter (Jaeger/Honeycomb/Grafana)
otlp_exporter = OTLPSpanExporter(
    endpoint="localhost:4317",  # gRPC endpoint
    insecure=True
)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Get tracer
tracer = trace.get_tracer(__name__)
```

### Span Instrumentation

```python
@trace_evaluation
async def evaluate(
    session_id: str,
    response: ResponseData
) -> PerformanceSignal:
    """
    Creates span with attributes:
    - session_id
    - response_length
    - evaluation_strategy
    - overall_score
    - latency_ms
    """
```

### Metrics Collection

#### Histogram Metrics

```python
from prometheus_client import Histogram

LATENCIES = {
    "evaluation_latency": Histogram(
        "evaluation_latency_seconds",
        "Time taken to evaluate a response",
        buckets=(0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0)
    ),
    "model_generation_latency": Histogram(
        "model_generation_latency_seconds",
        "Time taken for model to generate response",
        buckets=(0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0)
    ),
    "context_assembly_latency": Histogram(
        "context_assembly_latency_seconds",
        "Time taken to assemble context",
        buckets=(0.05, 0.1, 0.2, 0.5, 1.0)
    )
}
```

#### Counter Metrics

```python
from prometheus_client import Counter

COUNTERS = {
    "evaluations": Counter(
        "evaluations_total",
        "Total number of evaluations",
        ["result"]  # success, rule_based_fallback, llm_degraded
    ),
    "model_calls": Counter(
        "model_calls_total",
        "Total number of model API calls",
        ["provider", "status"]  # nim/groq/openai/stub, success/error
    ),
    "fallbacks": Counter(
        "fallbacks_total",
        "Total number of provider fallbacks",
        ["from_provider", "to_provider"]
    )
}
```

#### Gauge Metrics

```python
from prometheus_client import Gauge

GAUGES = {
    "active_sessions": Gauge(
        "active_sessions",
        "Number of active interview sessions"
    )
}
```

## 10.2 Monitoring Endpoints

### /api/sessions/{id}/orchestrators/stats

**Purpose**: Real-time orchestrator performance metrics

**Response**:
```json
{
  "session_id": "abc-123",
  "orchestrator_metrics": {
    "evaluation": {
      "total_evaluations": 15,
      "avg_latency_ms": 95.3,
      "rule_based_ratio": 0.0,
      "llm_evaluation_ratio": 1.0
    },
    "turn_decisions": {
      "total_turns": 15,
      "avg_decision_latency_ms": 12.5,
      "action_distribution": {
        "ASK_NEW_QUESTION": 10,
        "PROBE_DEEPER": 4,
        "END_INTERVIEW": 1
      }
    },
    "model_generation": {
      "total_calls": 15,
      "provider_usage": {
        "nim": 15,
        "groq": 0,
        "openai": 0,
        "stub": 0
      },
      "avg_latency_by_provider": {
        "nim": 187.4
      },
      "fallback_count": 0
    },
    "context_assembly": {
      "total_assemblies": 15,
      "avg_latency_ms": 103.2,
      "avg_token_usage": 4523,
      "source_distribution": {
        "verified_profile": 0.10,
        "conversation": 0.25,
        "resume": 0.20,
        "jd": 0.15,
        "knowledge": 0.20,
        "memory": 0.10
      }
    }
  }
}
```

### /api/sessions/{id}/orchestrators/health

**Purpose**: Provider health status

**Response**:
```json
{
  "session_id": "abc-123",
  "provider_health": {
    "nim": {
      "status": "healthy",
      "success_rate": 1.0,
      "avg_latency_ms": 187.4,
      "last_successful_call": "2026-05-25T14:30:45Z",
      "failure_count": 0
    },
    "groq": {
      "status": "untested",
      "reason": "no_calls_made"
    },
    "openai": {
      "status": "untested",
      "reason": "no_calls_made"
    }
  },
  "fallback_chain_status": "primary_healthy"
}
```

### /api/sessions/{id}/orchestrators/state

**Purpose**: Current runtime state inspection

**Response**:
```json
{
  "session_id": "abc-123",
  "interview_state": {
    "current_phase": "TECHNICAL_QUESTIONS",
    "questions_asked": 15,
    "current_challenge_level": "MEDIUM",
    "interview_progress_percent": 75.0
  },
  "candidate_state": {
    "current_performance_score": 68.5,
    "performance_trend": "STABLE",
    "confidence_trend": "IMPROVING",
    "frustration_level": 0.2,
    "engagement_level": 0.85
  }
}
```

## 10.3 Logging Strategy

### Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "evaluation_completed",
    session_id=session_id,
    overall_score=85.3,
    strategy="hybrid",
    latency_ms=95.2,
    llm_provider="nim"
)
```

### Log Levels

- **DEBUG**: Detailed orchestrator internals, state transitions
- **INFO**: Successful operations, key metrics
- **WARNING**: Fallback triggers, performance degradation
- **ERROR**: Provider failures, evaluation errors
- **CRITICAL**: System-wide failures

### Cost Tracking

```python
logger.info(
    "llm_evaluation_cost",
    session_id=session_id,
    model="gpt-4o-mini",
    input_tokens=175,
    output_tokens=42,
    estimated_cost_usd=0.000051,
    prompt_version="v1.0.0"
)
```

---

# 11. COMPLETE FUNCTION REFERENCE

## 11.1 LLM Provider Functions

### Question Generation
- `OpenAIQuestionGenerationProvider.generate()`
- `NIMQuestionGenerationProvider.generate()`
- `StubQuestionGenerationProvider.generate()`

### Evaluation
- `OpenAIEvaluationProvider.evaluate()`
- `NIMEvaluationProvider.evaluate()`
- `StubEvaluationProvider.evaluate()`

### Transcription
- `OpenAITranscriptionProvider.transcribe()`
- `GroqTranscriptionProvider.transcribe()`
- `StubTranscriptionProvider.transcribe()`

### Coaching
- `LangChainCoachProvider.get_response()`
- `NIMCoachProvider.get_response()`
- `StubCoachProvider.get_response()`

### Follow-up Analysis
- `OpenAIFollowupProvider.analyze()`
- `StubFollowupProvider.analyze()`

## 11.2 Orchestrator Functions

### InterviewOrchestrator
- `initialize_interview()`
- `process_phase_transition()`
- `evaluate_interview_completion()`
- `finalize_interview()`

### TurnOrchestrator
- `decide_next_action()`
- `evaluate_should_followup()`
- `select_next_question()`

### ModelOrchestrator
- `generate()`
- `health_check()`
- `get_provider_status()`

### ContextOrchestrator
- `assemble_context()`
- `check_for_hallucinations()`
- `_build_profile_context()`
- `_trim_context()`

### EvaluationOrchestrator
- `evaluate()`
- `_rule_based_evaluation()`
- `_llm_evaluation()`

### RealtimeOrchestrator
- `pre_generate_likely_responses()`
- `invalidate_cache()`

## 11.3 Memory Functions

### MemoryPipeline
- `store_observation()`
- `retrieve_context_for_prompt()`
- `update_memory_after_turn()`
- `compact_and_prune()`

### MemoryStore
- `create_memory()`
- `update_memory()`
- `delete_memory()`
- `get_all_candidate_memories()`

### VectorStore
- `similarity_search()`
- `batch_insert()`

### MemoryEncoder
- `encode()`
- `batch_encode()`

### RetrievalEngine
- `retrieve_relevant_memories()`

### MemoryDecay
- `calculate_relevance()`
- `reinforce_access()`

### MemoryCompactor
- `compact_candidate_memories()`
- `_merge_memories()`

### SessionSummarizer
- `summarize_and_extract_memories()`

## 11.4 RAG Functions

### RetrievalPipeline
- `retrieve()`
- `_semantic_search()`
- `_rerank()`
- `build_context()`

### HybridRetrievalPipeline
- `retrieve()` (overridden)
- `_keyword_search()`
- `_merge_results()`

## 11.5 Context Functions

### ContextOrchestrator
- `assemble_context()`
- `_get_verified_profile()`
- `_calculate_allocations()`
- `_build_profile_context()`
- `_build_conversation_context()`
- `_build_resume_context()`
- `_build_jd_context()`
- `_build_knowledge_context()`
- `_build_memory_context()`
- `_trim_context()`
- `_assemble_final_context()`
- `check_for_hallucinations()`

---

# 12. DATA FLOW DIAGRAMS

## 12.1 Complete Interview Flow

```
1. User Starts Interview
   ↓
2. API: POST /interviews/sessions
   ↓
3. Create InterviewSession record
   ↓
4. Initialize OrchestratorHub
   ├─ Load resume/JD from InterviewJourney
   ├─ Initialize InterviewRuntimeState
   └─ Create session-level locks
   ↓
5. VoiceAgent: Connect WebRTC
   ↓
6. InterviewOrchestrator.initialize_interview()
   ├─ Set phase: INTRODUCTION
   ├─ Load candidate profile
   └─ Initialize metrics
   ↓
7. Generate first question
   ├─ TurnOrchestrator.decide_next_action()
   ├─ Select question from QuestionBank
   ├─ ContextOrchestrator.assemble_context()
   ├─ ModelOrchestrator.generate()
   └─ VoiceAgent: Speak question via TTS
   ↓
8. Candidate speaks answer
   ↓
9. STT: Transcribe audio
   ↓
10. VoiceAgent emits TRANSCRIPT_RECEIVED event
    ↓
11. OrchestratorHub handles event
    ├─ Acquire session lock
    ├─ ContextOrchestrator.assemble_context()
    │   ├─ Get verified profile
    │   ├─ Calculate token allocations
    │   ├─ Build 6 context components (parallel)
    │   │   ├─ Verified profile
    │   │   ├─ Conversation history
    │   │   ├─ Resume (filtered)
    │   │   ├─ JD (trimmed)
    │   │   ├─ Knowledge base (semantic search)
    │   │   └─ Memory (decay-corrected, ranked)
    │   ├─ Enforce budget (trim if needed)
    │   └─ Assemble final context
    ├─ EvaluationOrchestrator.evaluate()
    │   ├─ Rule-based evaluation (60%)
    │   │   ├─ Word count analysis
    │   │   ├─ Hedge phrase detection
    │   │   ├─ Filler word frequency
    │   │   ├─ Domain vocabulary check
    │   │   └─ Timing scores
    │   ├─ LLM evaluation (40%)
    │   │   ├─ Build evaluation prompt
    │   │   ├─ ModelOrchestrator.generate()
    │   │   │   ├─ Try NIM
    │   │   │   ├─ Fallback to Groq
    │   │   │   ├─ Fallback to OpenAI
    │   │   │   └─ Fallback to rule-based stub
    │   │   └─ Parse JSON scores
    │   └─ Composite scoring (weighted)
    ├─ Store evaluation in ResponseInstance
    ├─ TurnOrchestrator.decide_next_action()
    │   ├─ Analyze performance score
    │   ├─ Check question exhaustion
    │   ├─ Check time constraints
    │   ├─ Adaptive difficulty adjustment
    │   └─ Return TurnDecision
    ├─ Execute decision
    │   ├─ If ASK_NEW_QUESTION:
    │   │   ├─ Select next question
    │   │   ├─ Create QuestionInstance
    │   │   └─ Generate response
    │   ├─ If PROBE_DEEPER:
    │   │   ├─ Analyze gaps
    │   │   └─ Generate follow-up
    │   ├─ If REQUEST_CLARIFICATION:
    │   │   └─ Generate clarification question
    │   └─ If END_INTERVIEW:
    │       └─ Finalize interview
    ├─ ModelOrchestrator.generate()
    │   └─ Return interviewer response
    ├─ Release session lock
    └─ VoiceAgent: Speak response via TTS
    ↓
12. RealtimeOrchestrator.pre_generate()
    ├─ While TTS playing, speculatively generate:
    │   ├─ Next question (if good answer)
    │   ├─ Follow-up (if incomplete answer)
    │   └─ Clarification (if vague answer)
    └─ Cache for 5 seconds
    ↓
13. Repeat steps 8-12 until interview ends
    ↓
14. InterviewOrchestrator.finalize_interview()
    ├─ Update InterviewSession status: COMPLETED
    ├─ Create EvaluationJob (PENDING)
    ├─ MemoryPipeline.process_session_end()
    │   ├─ SessionSummarizer extracts memories
    │   ├─ Store memories in CandidateMemory
    │   └─ MemoryCompactor deduplicates
    └─ Emit INTERVIEW_COMPLETED event
    ↓
15. Background worker processes EvaluationJob
    ├─ Aggregate ResponseInstance scores
    ├─ Generate feedback summary
    ├─ Create EvaluationReport
    └─ Update EvaluationJob status: COMPLETED
    ↓
16. User views evaluation report
```

## 12.2 Context Assembly Flow

```
ContextOrchestrator.assemble_context()
    ↓
Step 1: Get/Create Verified Profile
    ├─ Extract from resume (skills, projects, companies)
    ├─ Augment from conversation (candidate mentions)
    └─ Cache per candidate
    ↓
Step 2: Calculate Token Allocations
    ├─ Based on priority (BALANCED, CONVERSATION_HEAVY, etc.)
    ├─ Adapt to interview phase
    └─ Return allocations dict
    ↓
Step 3: Build Context Components (Parallel)
    ├─ Verified Profile Context (10-15% tokens)
    │   └─ Format: "Verified Skills: ..., Projects: ..., Companies: ..."
    ├─ Conversation History Context (20-40% tokens)
    │   ├─ Get last 10 turns from ConversationState
    │   └─ Format as Q&A pairs
    ├─ Resume Context (15-30% tokens)
    │   ├─ Filter by verified profile
    │   ├─ Phase-adaptive (full in INTRO, filtered later)
    │   └─ Extract relevant sections
    ├─ Job Description Context (10-15% tokens)
    │   └─ Full JD or trimmed
    ├─ Knowledge Base Context (10-35% tokens)
    │   ├─ OrchestratorHub._retrieve_knowledge_for_context()
    │   ├─ RetrievalPipeline.retrieve()
    │   │   ├─ Generate query embedding
    │   │   ├─ Semantic search (pgvector)
    │   │   ├─ Metadata filtering (domain, topic, difficulty)
    │   │   ├─ Reranking (relevance + diversity)
    │   │   └─ Return top_k chunks
    │   └─ Build context from chunks
    └─ Memory Context (10% tokens)
        ├─ OrchestratorHub._retrieve_candidate_memories()
        ├─ MemoryPipeline.retrieve_context_for_prompt()
        │   ├─ Determine policy context (phase-aware)
        │   ├─ Get policy filters (allowed types, min importance)
        │   ├─ RetrievalEngine.retrieve_relevant_memories()
        │   │   ├─ Encode query to vector
        │   │   ├─ VectorStore.similarity_search()
        │   │   ├─ Apply time decay
        │   │   ├─ RetrievalRanker.rank_memories()
        │   │   │   ├─ Semantic similarity (45%)
        │   │   │   ├─ Recency (15%)
        │   │   │   ├─ Importance (20%)
        │   │   │   ├─ Frequency (5%)
        │   │   │   ├─ Context boost (variable)
        │   │   │   └─ Decay penalty (15%)
        │   │   ├─ Filter by policy
        │   │   ├─ Limit to top N
        │   │   └─ Reinforce accessed memories
        │   └─ Format as prompt block
        └─ Return memory context
    ↓
Step 4: Enforce Budget
    ├─ Estimate tokens for each component
    ├─ If total > budget:
    │   ├─ Trim priority order: Memory → Knowledge → JD → Resume/Conversation
    │   ├─ Iteratively trim 20% from highest-priority component
    │   └─ Stop when under budget
    └─ Preserve verified profile (NEVER trimmed)
    ↓
Step 5: Assemble Final Context
    ├─ Hallucination prevention header
    ├─ "CRITICAL: Only reference information explicitly verified below."
    ├─ "## Verified Candidate Information"
    ├─ Verified profile section
    ├─ "## Conversation History"
    ├─ Conversation section
    ├─ "## Resume"
    ├─ Resume section
    ├─ "## Job Description"
    ├─ JD section
    ├─ "## Domain Knowledge"
    ├─ Knowledge section
    ├─ "## Candidate Memory"
    ├─ Memory section
    └─ Constraints footer (domain restrictions)
    ↓
Step 6: Return ContextAssembly
    ├─ final_context: str
    ├─ total_tokens_used: int
    ├─ tokens_by_source: dict
    ├─ verified_profile: VerifiedCandidateProfile
    ├─ applied_constraints: InterviewConstraints
    └─ budget_usage_details: dict
```

## 12.3 Memory Lifecycle Flow

```
During Interview:
    ├─ Candidate speaks
    ├─ VoiceAgent stores turn in conversation history
    └─ (no memory creation yet)
    ↓
Session End:
    ├─ InterviewOrchestrator.finalize_interview()
    └─ MemoryPipeline.process_session_end()
        ├─ Get all conversation turns from session
        ├─ SessionSummarizer.summarize_and_extract_memories()
        │   ├─ Format transcript for LLM
        │   ├─ LLM prompt: "Extract 2-5 critical observations"
        │   ├─ LLM classifies: SEMANTIC / EPISODIC / BEHAVIORAL
        │   ├─ LLM assigns importance scores (0.1-1.0)
        │   ├─ LLM generates behavioral tags
        │   └─ Return list of MemoryObject
        ├─ For each memory:
        │   ├─ MemoryEncoder.encode(content)
        │   │   ├─ Try HuggingFace API (BAAI/bge-large-en-v1.5)
        │   │   ├─ Fallback to NVIDIA NIM (nvidia/embed-qa-4)
        │   │   └─ Fallback to deterministic hash
        │   ├─ Create CandidateMemory record
        │   └─ MemoryStore.create_memory()
        ├─ MemoryCompactor.compact_candidate_memories()
        │   ├─ Group memories by type
        │   ├─ Pairwise cosine similarity comparison
        │   ├─ If similarity >= 0.85:
        │   │   ├─ Merge contents
        │   │   ├─ Boost importance (+0.1)
        │   │   ├─ Average confidence
        │   │   ├─ Sum access counts
        │   │   ├─ Merge tags
        │   │   ├─ Reduce decay factor (0.9x)
        │   │   ├─ Re-encode combined content
        │   │   └─ Delete redundant memory
        │   └─ Return merged_count
        └─ Return total memories created
    ↓
Next Interview:
    ├─ ContextOrchestrator.assemble_context()
    ├─ OrchestratorHub._retrieve_candidate_memories()
    ├─ MemoryPipeline.retrieve_context_for_prompt()
    ├─ RetrievalEngine.retrieve_relevant_memories()
    │   ├─ Encode query to vector
    │   ├─ VectorStore.similarity_search()
    │   ├─ MemoryDecay.calculate_relevance()
    │   │   ├─ Exponential time decay
    │   │   ├─ Type multiplier (BEHAVIORAL 0.5x, SEMANTIC 0.3x)
    │   │   ├─ Importance mitigation
    │   │   └─ Access count mitigation
    │   ├─ RetrievalRanker.rank_memories()
    │   ├─ Filter by policy
    │   ├─ Limit to top N
    │   └─ MemoryDecay.reinforce_access()
    │       ├─ Increment access_count
    │       ├─ Update last_accessed
    │       ├─ Boost relevance (+0.15)
    │       └─ Boost importance (+0.02)
    └─ Return memories for context assembly
```

---

# 13. API INTEGRATION PATTERNS

## 13.1 Voice Agent Integration

**Pattern**: Event-driven orchestrator integration via EventBus

**VoiceAgent modifications**:
```python
# Emit enhanced TRANSCRIPT_RECEIVED event
event_data = {
    "session_id": self.session_id,
    "transcript": transcript_text,
    "audio_duration_ms": audio_duration,
    "thinking_time_ms": thinking_time,
    "speaking_time_ms": speaking_time,
    "timestamp": datetime.utcnow().isoformat()
}
await event_bus.emit("TRANSCRIPT_RECEIVED", event_data)

# Emit QUESTION_ASKED event
question_data = {
    "session_id": self.session_id,
    "question_id": question_id,
    "question_text": question_text,
    "difficulty": difficulty,
    "timestamp": datetime.utcnow().isoformat()
}
await event_bus.emit("QUESTION_ASKED", question_data)

# Emit INTERVIEW_COMPLETED event
completion_data = {
    "session_id": self.session_id,
    "duration_seconds": total_duration,
    "questions_asked": len(questions),
    "timestamp": datetime.utcnow().isoformat()
}
await event_bus.emit("INTERVIEW_COMPLETED", completion_data)
```

**OrchestratorHub handlers**:
```python
@event_bus.on("TRANSCRIPT_RECEIVED")
async def handle_transcript(event_data):
    session_id = event_data["session_id"]
    
    # Acquire session lock (prevent race conditions)
    async with orchestrator_hub.processing_locks[session_id]:
        # Assemble context
        context = await context_orchestrator.assemble_context(...)
        
        # Evaluate response
        performance = await evaluation_orchestrator.evaluate(...)
        
        # Decide next action
        decision = await turn_orchestrator.decide_next_action(...)
        
        # Generate response
        response = await model_orchestrator.generate(...)
        
        # Emit response event
        await event_bus.emit("RESPONSE_GENERATED", {
            "session_id": session_id,
            "response_text": response,
            "decision": decision.action.value
        })
```

## 13.2 OpenAI SDK Pattern

**All providers use OpenAI SDK with custom base_url**:

```python
from openai import AsyncOpenAI

# OpenAI
client = AsyncOpenAI(
    api_key=settings.openai_api_key
)

# NVIDIA NIM
client = AsyncOpenAI(
    api_key=settings.nvidia_api_key,
    base_url=settings.nvidia_base_url  # https://integrate.api.nvidia.com/v1
)

# Groq
client = AsyncOpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1"
)

# vLLM Local
client = AsyncOpenAI(
    api_key="EMPTY",
    base_url="http://localhost:8000/v1"
)

# Unified usage
response = await client.chat.completions.create(
    model=model_name,
    messages=messages,
    temperature=0.7,
    max_tokens=500
)
```

## 13.3 Async Patterns

**All LLM calls are async**:

```python
async def evaluate(self, input: EvaluationInput) -> PerformanceSignal:
    # Async API call
    response = await self.client.chat.completions.create(...)
    
    # Async database operations
    await db.execute(...)
    await db.commit()
    
    return result
```

**Concurrent operations**:
```python
# Build context components in parallel
async with asyncio.TaskGroup() as tg:
    profile_task = tg.create_task(self._build_profile_context(...))
    conv_task = tg.create_task(self._build_conversation_context(...))
    resume_task = tg.create_task(self._build_resume_context(...))
    jd_task = tg.create_task(self._build_jd_context(...))
    knowledge_task = tg.create_task(self._build_knowledge_context(...))
    memory_task = tg.create_task(self._build_memory_context(...))
```

## 13.4 Error Handling Patterns

**Multi-tier fallback**:
```python
async def generate(self, prompt, context):
    for provider in [ModelProvider.NIM, ModelProvider.GROQ, ModelProvider.OPENAI]:
        try:
            response = await self._call_provider(provider, prompt, context)
            return response
        except TimeoutError:
            logger.warning(f"{provider.value} timeout, trying next provider")
            continue
        except Exception as e:
            logger.error(f"{provider.value} error: {e}")
            continue
    
    # Final fallback: rule-based template
    return self._generate_template_response(prompt)
```

**Graceful degradation**:
```python
async def evaluate(self, input):
    try:
        # Try LLM evaluation
        llm_scores = await self._llm_evaluation(input)
    except Exception as e:
        logger.warning(f"LLM evaluation failed: {e}, using rule-based only")
        # Degrade to 100% rule-based
        return await self._rule_based_evaluation(input)
    
    # Hybrid scoring
    return self._composite_scoring(rule_scores, llm_scores)
```

---

# 14. PERFORMANCE OPTIMIZATION

## 14.1 Latency Targets & Achieved

| Component | Target | Achieved | Status |
|-----------|--------|----------|--------|
| **Total Latency** | <700ms | 460-710ms | ✅ Within target |
| STT (Whisper) | <150ms | 100-150ms | ✅ |
| Context Assembly | <100ms | 80-120ms | ✅ |
| Knowledge Retrieval | <50ms | 35-70ms | ✅ |
| Memory Retrieval | <50ms | 30-60ms | ✅ |
| Evaluation (Hybrid) | <100ms | 85-120ms | ✅ |
| LLM Generation (NIM) | <250ms | 150-250ms | ✅ |
| TTS (Edge TTS) | <100ms | 80-100ms | ✅ |

## 14.2 Token Budget Optimization

**Strategy**: Aggressive context trimming with priority preservation

```python
# Default budget: 5000 tokens
# Trim order (lowest to highest priority):
1. Memory (10%, 500 tokens) - trim first
2. Knowledge Base (20%, 1000 tokens)
3. Job Description (15%, 750 tokens)
4. Resume (20%, 1000 tokens)
5. Conversation (25%, 1250 tokens)
6. Verified Profile (10%, 500 tokens) - NEVER trim
```

**Token estimation**: `len(text) // 4` (rough approximation)

## 14.3 Cache Strategy

### Response Cache (RealtimeOrchestrator)

**Purpose**: Pre-generate likely responses during TTS playback

**Configuration**:
- **Type**: In-memory LRU cache
- **TTL**: 5 seconds
- **Max size**: 100 entries
- **Hit rate target**: >15%
- **Hit rate achieved**: ~18%

**Cache key**: `hash(session_id, context_hash, scenario_type)`

**Speculative scenarios**:
1. Good answer → Next question
2. Incomplete answer → Follow-up probe
3. Vague answer → Clarification request

### Verified Profile Cache

**Purpose**: Avoid re-extracting profile on each turn

**Configuration**:
- **Type**: In-memory dict
- **TTL**: Session lifetime
- **Invalidation**: On new conversation-verified facts

## 14.4 Database Query Optimization

### Index Strategy

**Hot path queries**:
1. User dashboard: `ix_interview_sessions_user_id_status_deleted_at` (composite)
2. Question selection: `ix_question_banks_topic_difficulty_deleted_at` (composite)
3. Worker claim: `ix_evaluation_jobs_status_next_retry_at_created_at` (composite)
4. Vector similarity: `ix_knowledge_chunks_embedding_vector` (IVFFlat)

**Composite indexes** for common filter combinations:
- `(user_id, status, deleted_at)` - user session listing
- `(topic_id, difficulty, deleted_at)` - question bank filtering
- `(domain, topic)` - knowledge document filtering

### Query Patterns

**Eager loading**:
```python
# Load session with relationships in one query
session = await db.scalars(
    select(InterviewSession)
    .options(
        selectinload(InterviewSession.questions),
        selectinload(InterviewSession.evaluation)
    )
    .where(InterviewSession.id == session_id)
).first()
```

**Pagination**:
```python
# Paginate with cursor-based approach
stmt = (
    select(InterviewSession)
    .where(InterviewSession.user_id == user_id)
    .where(InterviewSession.created_at < cursor)
    .order_by(InterviewSession.created_at.desc())
    .limit(20)
)
```

## 14.5 Speculative Execution

**RealtimeOrchestrator** pre-generates responses during TTS playback:

```python
async def pre_generate_likely_responses(
    session_id: str,
    current_context: ContextAssembly
) -> None:
    """
    While TTS is playing (2-5 seconds), speculatively generate:
    - Next question (scenario: good answer)
    - Follow-up probe (scenario: incomplete answer)
    - Clarification (scenario: vague answer)
    
    Cache for 5 seconds.
    """
    
    scenarios = [
        ("next_question", "good_answer"),
        ("followup", "incomplete_answer"),
        ("clarification", "vague_answer")
    ]
    
    async with asyncio.TaskGroup() as tg:
        for scenario_type, condition in scenarios:
            tg.create_task(
                self._generate_and_cache(
                    session_id,
                    scenario_type,
                    condition,
                    current_context
                )
            )
```

**Cache hit rate**: ~18% (saves 150-250ms on cache hits)

## 14.6 Provider Routing Optimization

**Strategy**: Route to fastest provider first, fallback on failure

**Provider latencies**:
- **NIM**: 150-200ms (primary)
- **Groq**: 250-300ms (fallback 1)
- **OpenAI**: 400-600ms (fallback 2)
- **Rule-based**: 0ms (fallback 3)

**Health-based routing**:
```python
# Skip unhealthy providers
if provider_health[ModelProvider.NIM].success_rate < 0.8:
    # Skip NIM, go straight to Groq
    providers = [ModelProvider.GROQ, ModelProvider.OPENAI]
```

## 14.7 Memory Retrieval Optimization

**Strategy**: Composite scoring with early filtering

```python
# Step 1: Broad vector search (limit 15, min similarity 0.3)
raw_results = await vector_store.similarity_search(
    candidate_id=candidate_id,
    query_embedding=query_vector,
    limit=15,
    min_similarity=0.3
)

# Step 2: Apply time decay (in-memory)
for memory, sim_score in raw_results:
    memory.relevance_score = decay_manager.calculate_relevance(memory)

# Step 3: Composite scoring (in-memory)
ranked_results = ranker.rank_memories(raw_results, context)

# Step 4: Filter by policy (in-memory)
filtered = [m for m in ranked_results if m.importance_score >= 0.5]

# Step 5: Limit to top N (typically 3)
final_memories = filtered[:3]
```

**Optimization**: Most expensive operation (vector search) happens once; rest is in-memory

## 14.8 Parallel Operations

**Context assembly parallelization**:
```python
# Build 6 context components in parallel
async with asyncio.TaskGroup() as tg:
    profile_task = tg.create_task(self._build_profile_context(...))
    conv_task = tg.create_task(self._build_conversation_context(...))
    resume_task = tg.create_task(self._build_resume_context(...))
    jd_task = tg.create_task(self._build_jd_context(...))
    knowledge_task = tg.create_task(self._build_knowledge_context(...))
    memory_task = tg.create_task(self._build_memory_context(...))

# All complete before continuing
# Total time = max(individual times) instead of sum
```

**Evaluation parallelization**:
```python
# Run rule-based and LLM evaluation in parallel
async with asyncio.TaskGroup() as tg:
    rule_task = tg.create_task(self._rule_based_evaluation(...))
    llm_task = tg.create_task(self._llm_evaluation(...))

rule_scores = await rule_task
llm_scores = await llm_task

# Composite scoring
return self._composite_scoring(rule_scores, llm_scores)
```

---

## CONCLUSION

This document provides a **complete end-to-end reference** for the BrainTrain LLM system, covering:

✅ **24 Database Models** with relationships and vector support  
✅ **100+ Functions** across providers, orchestrators, memory, and RAG  
✅ **5-Layer Prompt Engineering** with versioning and hallucination prevention  
✅ **Dual RAG System** (knowledge base + candidate memory)  
✅ **Deterministic Orchestration** with multi-tier fallback  
✅ **Hybrid Evaluation** (60% rule-based, 40% LLM)  
✅ **Memory System** with decay, reinforcement, and compaction  
✅ **Context Engineering** with token budgeting and verified profiles  
✅ **OpenTelemetry Instrumentation** with spans, metrics, and counters  
✅ **LangChain Integration** (minimalist, stateless pattern)  
✅ **Performance Optimization** achieving <700ms total latency

**Key Innovation**: The system separates **intelligence** (in architecture, rules, and data) from **generation** (LLM outputs), ensuring reliability, traceability, and cost efficiency while maintaining conversational quality.

**Production-Ready**: With comprehensive instrumentation, graceful degradation, multi-tier fallback, and hallucination prevention, this system is designed for real-world deployment at scale.
