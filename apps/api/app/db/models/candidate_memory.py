import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Float, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.interview_session import InterviewSession


class CandidateMemory(Base):
    __tablename__ = "candidate_memories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    source_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=True
    )

    memory_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    
    # 1536-dimension vector for embedding similarity matching
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)

    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    decay_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    access_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    behavioral_tags: Mapped[List[str]] = mapped_column(JSONB, default=list, server_default='[]', nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_accessed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    candidate: Mapped["User"] = relationship("User", lazy="raise")
    session: Mapped[Optional["InterviewSession"]] = relationship("InterviewSession", lazy="raise")

    __table_args__ = (
        Index("ix_candidate_memories_candidate_id", "candidate_id"),
        Index("ix_candidate_memories_candidate_type", "candidate_id", "memory_type"),
    )

    def __repr__(self) -> str:
        return f"<CandidateMemory id={self.id} type={self.memory_type} importance={self.importance_score}>"
