"""
Knowledge Tag model for filtering and categorizing interview knowledge.

This model provides a many-to-many relationship between documents and tags,
enabling advanced filtering during retrieval (e.g., "show me FAANG system design questions").
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KnowledgeTag(Base):
    """
    Tags for categorizing and filtering knowledge documents.
    
    Examples:
    - domain: frontend, backend, system_design, behavioral
    - difficulty: EASY, MEDIUM, HARD
    - company: google, amazon, netflix, uber, meta, apple, startup
    - interview_type: technical, behavioral, coding, system_design
    - topic: react, aws, distributed_systems, leadership
    """
    __tablename__ = "knowledge_tags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False
    )
    
    # Tag categorization
    tag_type: Mapped[str] = mapped_column(String(64), nullable=False)  # domain, difficulty, company, interview_type, topic
    tag_value: Mapped[str] = mapped_column(String(128), nullable=False)  # react, google, hard, etc.
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_knowledge_tags_document_id", "document_id"),
        Index("ix_knowledge_tags_type", "tag_type"),
        Index("ix_knowledge_tags_type_value", "tag_type", "tag_value"),
        UniqueConstraint("document_id", "tag_type", "tag_value", name="uq_knowledge_tags_document_type_value"),
    )

    def __repr__(self) -> str:
        return f"<KnowledgeTag doc={self.document_id} {self.tag_type}={self.tag_value}>"
