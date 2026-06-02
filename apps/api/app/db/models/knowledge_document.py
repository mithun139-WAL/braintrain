"""
Knowledge Document model for storing interview knowledge sources.

This model stores high-level documents (articles, guides, documentation)
that will be chunked and embedded for retrieval-augmented interviewing.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.knowledge_chunk import KnowledgeChunk


class KnowledgeDocument(Base):
    """
    High-level knowledge documents for interview intelligence.
    
    Supports ingestion from multiple sources (markdown, PDF, YAML)
    and categorization by domain, topic, company, and difficulty.
    """
    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Document metadata
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source: Mapped[str] = mapped_column(String(512), nullable=False)  # URL or file path
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)  # markdown, pdf, yaml, json, txt
    
    # Categorization
    domain: Mapped[str] = mapped_column(String(64), nullable=False)  # frontend, backend, system_design, behavioral
    topic: Mapped[str] = mapped_column(String(128), nullable=False)  # react, aws, distributed_systems, leadership
    difficulty: Mapped[str] = mapped_column(String(16), nullable=False)  # EASY, MEDIUM, HARD
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Raw document content
    
    # Metadata (company, tags, interview_type, etc.)
    meta_data: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, server_default='{}', nullable=False)
    
    # Statistics
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    chunks: Mapped[List["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk", back_populates="document", lazy="raise", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_knowledge_documents_domain", "domain"),
        Index("ix_knowledge_documents_topic", "topic"),
        Index("ix_knowledge_documents_domain_topic", "domain", "topic"),
        Index("ix_knowledge_documents_difficulty", "difficulty"),
    )

    def __repr__(self) -> str:
        return f"<KnowledgeDocument id={self.id} title='{self.title[:30]}' domain={self.domain} topic={self.topic}>"
