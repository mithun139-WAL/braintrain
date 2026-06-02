import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Float, Boolean, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class LearningMemoryNode(Base):
    """
    Represents a single node in a candidate's cognitive knowledge map (memory graph).
    Tracks familiarity, recall latency, stability, and spaced-repetition metrics.
    """
    __tablename__ = "learning_memory_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    concept_name: Mapped[str] = mapped_column(String(255), nullable=False)
    concept_type: Mapped[str] = mapped_column(String(64), default="concept")  # concept, technology, framework, star_story, behavioral_example

    # Cognitive & performance metrics
    familiarity_score: Mapped[float] = mapped_column(Float, default=50.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=50.0)
    recall_latency: Mapped[float] = mapped_column(Float, default=1.0)  # Average response latency in seconds
    retention_strength: Mapped[float] = mapped_column(Float, default=50.0)
    pressure_recall_stability: Mapped[float] = mapped_column(Float, default=50.0)
    retry_success_rate: Mapped[float] = mapped_column(Float, default=1.0)
    exposure_count: Mapped[int] = mapped_column(Integer, default=0)
    mastery_level: Mapped[float] = mapped_column(Float, default=50.0)

    # State flags
    is_fragile: Mapped[bool] = mapped_column(Boolean, default=False)
    is_weak_recall: Mapped[bool] = mapped_column(Boolean, default=False)
    is_strong_recall: Mapped[bool] = mapped_column(Boolean, default=False)

    # Next review for spaced repetition
    next_review_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_exposed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    candidate: Mapped["User"] = relationship("User", lazy="raise")

    __table_args__ = (
        Index("ix_learning_memory_nodes_candidate_id", "candidate_id"),
        Index("ix_learning_memory_nodes_candidate_concept", "candidate_id", "concept_name", unique=True),
    )

    def __repr__(self) -> str:
        return f"<LearningMemoryNode id={self.id} concept={self.concept_name} mastery={self.mastery_level}>"


class LearningMemoryEdge(Base):
    """
    Represents conceptual relationships, prerequisite dependencies, overlap,
    and reinforcement links between concepts in the candidate's learning graph.
    """
    __tablename__ = "learning_memory_edges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    source_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_memory_nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_memory_nodes.id", ondelete="CASCADE"), nullable=False
    )

    relationship_type: Mapped[str] = mapped_column(
        String(64), default="conceptual"
    )  # conceptual, prerequisite, confusion_overlap, reinforcement
    strength: Mapped[float] = mapped_column(Float, default=0.5)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    source_node: Mapped["LearningMemoryNode"] = relationship(
        "LearningMemoryNode", foreign_keys=[source_node_id], lazy="raise"
    )
    target_node: Mapped["LearningMemoryNode"] = relationship(
        "LearningMemoryNode", foreign_keys=[target_node_id], lazy="raise"
    )

    __table_args__ = (
        Index("ix_learning_memory_edges_candidate_id", "candidate_id"),
        Index("ix_learning_memory_edges_source_target", "source_node_id", "target_node_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<LearningMemoryEdge id={self.id} source={self.source_node_id} target={self.target_node_id} type={self.relationship_type}>"
