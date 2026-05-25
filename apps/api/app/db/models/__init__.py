"""
Models package — imports all ORM models so they register with Base.metadata.

IMPORTANT: Every model file must be imported here. If a model is missing,
Alembic autogenerate will not detect it and will not create the table.

Import order follows FK dependency chain (parent before child):
  1. enums         — no FK deps
  2. user          — root entity
  3. skill_tag     — no FK deps
  4. user_skill_preference  — depends on user + skill_tag
  5. topic         — depends on user (self-referential)
  6. question_bank — depends on user + topic
  7. interview_session     — depends on user + topic
  8. question_instance     — depends on interview_session
  9. response_instance     — depends on question_instance
  10. evaluation_report    — depends on interview_session
  11. evaluation_job       — depends on interview_session
  12. user_context_input   — depends on user
  13. otp_code             — depends on user
  14. coaching_session     — depends on user
  15. coaching_message     — depends on coaching_session
  16. training_plan        — depends on user
  17. training_task        — depends on training_plan
"""

from app.db.models.enums import (  # noqa: F401
    AudioProcessingStatus,
    DifficultyLevel,
    EvaluationJobStatus,
    InterviewMode,
    InterviewType,
    SessionStatus,
)
from app.db.models.user import User  # noqa: F401
from app.db.models.skill_tag import SkillTag  # noqa: F401
from app.db.models.user_skill_preference import UserSkillPreference  # noqa: F401
from app.db.models.topic import Topic  # noqa: F401
from app.db.models.question_bank import QuestionBank  # noqa: F401
from app.db.models.interview_session import InterviewSession  # noqa: F401
from app.db.models.question_instance import QuestionInstance  # noqa: F401
from app.db.models.response_instance import ResponseInstance  # noqa: F401
from app.db.models.evaluation_report import EvaluationReport  # noqa: F401
from app.db.models.evaluation_job import EvaluationJob  # noqa: F401
from app.db.models.user_context_input import UserContextInput  # noqa: F401
from app.db.models.otp_code import OtpCode  # noqa: F401
from app.db.models.coaching_session import CoachingSession  # noqa: F401
from app.db.models.coaching_message import CoachingMessage  # noqa: F401
from app.db.models.training_plan import TrainingPlan  # noqa: F401
from app.db.models.training_task import TrainingTask  # noqa: F401
from app.db.models.interview_journey import InterviewJourney  # noqa: F401
from app.db.models.interview_journey_session import InterviewJourneySession  # noqa: F401
from app.db.models.candidate_memory import CandidateMemory  # noqa: F401
from app.db.models.knowledge_document import KnowledgeDocument  # noqa: F401
from app.db.models.knowledge_chunk import KnowledgeChunk  # noqa: F401
from app.db.models.knowledge_tag import KnowledgeTag  # noqa: F401
from app.db.models.candidate_mind_state import CandidateMindState  # noqa: F401
from app.db.models.mind_state_history import MindStateHistory  # noqa: F401
from app.db.models.turn import Turn  # noqa: F401
from app.db.models.pressure_event import PressureEvent  # noqa: F401
from app.db.models.recovery_record import RecoveryRecord  # noqa: F401
from app.db.models.confidence_event import ConfidenceEvent  # noqa: F401
from app.db.models.training_journey import TrainingJourney  # noqa: F401
from app.db.models.learning_memory import LearningMemoryNode, LearningMemoryEdge  # noqa: F401

__all__ = [
    "AudioProcessingStatus",
    "DifficultyLevel",
    "EvaluationJobStatus",
    "InterviewMode",
    "InterviewType",
    "SessionStatus",
    "User",
    "SkillTag",
    "UserSkillPreference",
    "Topic",
    "QuestionBank",
    "InterviewSession",
    "QuestionInstance",
    "ResponseInstance",
    "EvaluationReport",
    "EvaluationJob",
    "UserContextInput",
    "OtpCode",
    "CoachingSession",
    "CoachingMessage",
    "TrainingPlan",
    "TrainingTask",
    "InterviewJourney",
    "InterviewJourneySession",
    "CandidateMemory",
    "KnowledgeDocument",
    "KnowledgeChunk",
    "KnowledgeTag",
    # Coaching system models
    "CandidateMindState",
    "MindStateHistory",
    "PressureEvent",
    "RecoveryRecord",
    "ConfidenceEvent",
    "TrainingJourney",
    # Learning Memory models
    "LearningMemoryNode",
    "LearningMemoryEdge",
]
