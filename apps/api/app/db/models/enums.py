"""
Python enums matching the Prisma schema enums exactly.

All values are uppercase strings to match what PostgreSQL stores.
Using `str` mixin ensures Pydantic can serialize them as strings directly.

Source of truth: apps/backend/prisma/schema.prisma
"""
import enum


class SessionStatus(str, enum.Enum):
    """InterviewSession lifecycle states — maps to Prisma SessionStatus enum."""
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ANALYZED = "ANALYZED"
    CANCELLED = "CANCELLED"


class EvaluationJobStatus(str, enum.Enum):
    """Async evaluation job states — maps to Prisma EvaluationJobStatus enum."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


class AudioProcessingStatus(str, enum.Enum):
    """
    Whisper transcription state per ResponseInstance.
    Maps to Prisma AudioProcessingStatus enum (Phase 4).

    PENDING  — audioUrl present, transcription not yet attempted
    PROCESSING — transcription in progress
    COMPLETED  — Whisper returned transcript (may be empty if silent)
    FAILED     — Whisper call threw an error
    SKIPPED    — No audioUrl submitted (text-only response)
    """
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class DifficultyLevel(str, enum.Enum):
    """Question/session difficulty — maps to Prisma DifficultyLevel enum."""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class InterviewMode(str, enum.Enum):
    """Session interview format — maps to Prisma InterviewMode enum."""
    ONE_ON_ONE_AI = "ONE_ON_ONE_AI"
    PANEL_AI = "PANEL_AI"
    HYBRID = "HYBRID"


class InterviewType(str, enum.Enum):
    """
    Question/session category — maps to Prisma InterviewType enum.
    Drives the scoring rubric: TECHNICAL uses a different weight formula
    than BEHAVIORAL (see ARCHITECTURE.md §5.6).
    """
    TECHNICAL = "TECHNICAL"
    BEHAVIORAL = "BEHAVIORAL"
    MIXED = "MIXED"
    GROUP_DISCUSSION = "GROUP_DISCUSSION"
    RAPID_FIRE = "RAPID_FIRE"
