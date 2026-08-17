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
    reference_facts: Optional[str] = None


@dataclass
class GeneratedQuestion:
    question_text: str
    expected_answer_traits: list[str]
    estimated_difficulty: str
    reference_facts: Optional[str] = None


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
    reference_facts: Optional[str] = None
    # RAG-retrieved knowledge base context for this question.
    # Injected by the evaluation service at runtime; None when the KB returns no
    # relevant chunks (e.g. behavioral sessions, empty KB).
    # Used by LLM providers to cross-check technical claims against authoritative
    # reference material and enumerate factual contradictions.


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
    clarity_evidence: str
    structure_score: float
    structure_evidence: str
    depth_score: float
    depth_evidence: str
    confidence_score: float
    confidence_evidence: str
    communication_score: float
    communication_evidence: str
    # hesitation_score intentionally removed from post-session evaluation (v1.1.0).
    # The underlying concern (punishing thinking-out-loud) is better handled by
    # pressure_score (response timing) and thinking_depth_score (deliberateness).
    # Text-based filler detection on voice transcripts produces false positives on
    # natural speech disfluencies. The DB column is preserved for historical data
    # but is no longer written or surfaced in the API response.
    # Real-time voice hesitation detection (HesitationDetector) is unaffected.
    technical_score: Optional[float]   # None for BEHAVIORAL
    technical_evidence: Optional[str]
    evaluation_explanation: str
    technical_accuracy_issues: list[str] = field(default_factory=list)
    # Contradictions enumerated by LLM against reference_facts.
    # Empty list = no contradictions found (confirmed clear, not skipped).
    technical_accuracy_evidence: Optional[str] = None
    # Summary string: "Reference facts confirm answer" or "Reference facts
    # contradict: <detail>". None when no reference_facts were available.
    # Server-computed (not LLM):
    pressure_score: Optional[float] = None
    thinking_depth_score: Optional[float] = None
    overall_score: Optional[float] = None
    is_followup: bool = False
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


# ── Real-time Follow-up Analysis ───────────────────────────────────────────────

@dataclass
class FollowupExchange:
    followup_question: str
    followup_answer: str


@dataclass
class FollowupInput:
    question_text: str
    answer_text: str
    interview_type: str       # "TECHNICAL" | "BEHAVIORAL"
    difficulty: str           # "EASY" | "MEDIUM" | "HARD"
    prior_exchanges: list[FollowupExchange]  # previous follow-up rounds in this Q&A


@dataclass
class FollowupSignal:
    needs_followup: bool
    followup_question: Optional[str]   # None when needs_followup is False
    acknowledgement: str               # brief feedback shown inline in chat
    gap_identified: Optional[str]      # what was missing (None when complete)


@runtime_checkable
class FollowupProvider(Protocol):
    async def analyze(self, input: FollowupInput) -> FollowupSignal:
        ...
