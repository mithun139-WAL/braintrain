"""
AI provider protocols — typed interfaces for all AI integrations.

Every concrete provider (OpenAI, Stub) must implement these protocols.
The factory (app.ai.factory) returns the correct implementation based on
whether OPENAI_API_KEY is configured.

Protocols are used instead of ABCs so that no base class import is needed
in each provider file, keeping the dependency graph clean.
"""
import uuid
from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable


# ── Question Generation ────────────────────────────────────────────────────────

@dataclass
class QuestionGenerationInput:
    topic_name: str
    topic_id: uuid.UUID
    difficulty: str           # "EASY" | "MEDIUM" | "HARD"
    interview_type: str       # "TECHNICAL" | "BEHAVIORAL" | ...
    existing_questions: list[str]  # already-asked questions in this session


@dataclass
class GeneratedQuestion:
    question_text: str
    expected_answer_traits: list[str]
    estimated_difficulty: str


@runtime_checkable
class QuestionGenerationProvider(Protocol):
    async def generate(self, input: QuestionGenerationInput) -> GeneratedQuestion:
        ...


# ── Answer Evaluation ──────────────────────────────────────────────────────────

@dataclass
class EvaluationInput:
    question_text: str
    answer_text: str          # transcribed text if audio present, else typed text
    topic_name: str
    interview_type: str       # "TECHNICAL" | "BEHAVIORAL"
    difficulty: str           # "EASY" | "MEDIUM" | "HARD"
    response_time_ms: int
    thinking_time_ms: int


@dataclass
class EvaluationCostMeta:
    """Attached to PerformanceSignal by OpenAI providers; absent for stubs."""
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    model_used: str
    prompt_version: str
    degraded: bool = False


@dataclass
class PerformanceSignal:
    clarity_score: float
    structure_score: float
    depth_score: float
    confidence_score: float
    communication_score: float
    hesitation_score: float
    technical_score: Optional[float]   # None for BEHAVIORAL
    evaluation_explanation: str
    # Server-computed (not LLM):
    pressure_score: Optional[float] = None
    thinking_depth_score: Optional[float] = None
    overall_score: Optional[float] = None
    # Cost metadata (None for stub providers)
    cost_meta: Optional[EvaluationCostMeta] = field(default=None)


@runtime_checkable
class AnswerEvaluationProvider(Protocol):
    async def evaluate(self, input: EvaluationInput) -> PerformanceSignal:
        ...


# ── Audio Transcription ────────────────────────────────────────────────────────

@dataclass
class TranscriptionResult:
    text: str
    duration_seconds: Optional[float]
    model_used: str
    is_stub: bool
    estimated_cost_usd: Optional[float]


@runtime_checkable
class AudioTranscriptionProvider(Protocol):
    async def transcribe(self, audio_url: str) -> TranscriptionResult:
        ...
