"""
Knowledge Chunk model for storing semantically chunked document sections.

This model stores individual chunks of knowledge documents with embeddings
for semantic retrieval during interviews.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, Float, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.knowledge_document import KnowledgeDocument


class KnowledgeChunk(Base):
    """
    Semantic chunks of knowledge documents with embeddings.
    
    Supports vector similarity search via pgvector for RAG-based interviewing.
    """
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False
    )
    
    # Chunk content
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)  # Order within document
    
    # Token counting for context budgeting
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # 1536-dimension embedding (OpenAI-compatible, bge-large, jina, or nomic)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)
    
    # Metadata inherited from document + chunk-specific tags
    meta_data: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, server_default='{}', nullable=False)
    
    # Retrieval statistics
    retrieval_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usefulness_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)  # Updated based on feedback
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    document: Mapped["KnowledgeDocument"] = relationship("KnowledgeDocument", back_populates="chunks", lazy="raise")

    __table_args__ = (
        Index("ix_knowledge_chunks_document_id", "document_id"),
        Index("ix_knowledge_chunks_document_index", "document_id", "chunk_index"),
        # Vector similarity search index (IVFFlat for better performance on large datasets)
        Index(
            "ix_knowledge_chunks_embedding_vector",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )

    def __repr__(self) -> str:
        preview = self.chunk_text[:50].replace('\n', ' ')
        return f"<KnowledgeChunk id={self.id} doc={self.document_id} index={self.chunk_index} text='{preview}...'>"
