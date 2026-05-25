"""
Retrieval Pipeline for knowledge-augmented interviewing.

This pipeline retrieves relevant knowledge chunks from the knowledge base
to ground interview questions and prevent hallucinations.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from pgvector.sqlalchemy import Vector

from app.db.models.knowledge_chunk import KnowledgeChunk
from app.db.models.knowledge_document import KnowledgeDocument

logger = logging.getLogger(__name__)


@dataclass
class RetrievalQuery:
    """Query specification for knowledge retrieval."""
    query_text: str
    domain: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    company: Optional[str] = None
    interview_type: Optional[str] = None
    top_k: int = 10
    similarity_threshold: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_text": self.query_text,
            "domain": self.domain,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "company": self.company,
            "interview_type": self.interview_type,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
        }


@dataclass
class RetrievedChunk:
    """A retrieved knowledge chunk with metadata."""
    chunk_id: str
    text: str
    similarity_score: float
    document_title: str
    domain: str
    topic: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "similarity_score": self.similarity_score,
            "document_title": self.document_title,
            "domain": self.domain,
            "topic": self.topic,
            "metadata": self.metadata,
        }


class RetrievalPipeline:
    """
    Core retrieval pipeline for knowledge-augmented interviewing.
    
    Workflow:
    1. Semantic Search - Find top_k similar chunks via vector similarity
    2. Metadata Filtering - Filter by domain, topic, difficulty, etc.
    3. Reranking - Re-rank results by relevance and authority
    4. Context Building - Construct context for prompt assembly
    """
    
    def __init__(self, embedding_generator: Optional[Any] = None):
        """
        Initialize retrieval pipeline.
        
        Args:
            embedding_generator: Function to generate embeddings from text
        """
        self.embedding_generator = embedding_generator
        self._retrieval_count = 0
    
    async def retrieve(
        self,
        db: AsyncSession,
        query: RetrievalQuery
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant knowledge chunks.
        
        Args:
            db: Database session
            query: Retrieval query specification
            
        Returns:
            List of retrieved chunks sorted by relevance
        """
        self._retrieval_count += 1
        
        # Generate embedding for query
        query_embedding = await self._generate_query_embedding(query.query_text)
        
        # Semantic search
        chunks = await self._semantic_search(
            db=db,
            query_embedding=query_embedding,
            query=query
        )
        
        logger.info(
            f"Retrieved {len(chunks)} chunks for query: '{query.query_text[:50]}...'",
            extra={"domain": query.domain, "topic": query.topic}
        )
        
        return chunks
    
    async def _generate_query_embedding(self, query_text: str) -> List[float]:
        """Generate embedding vector for query text."""
        if self.embedding_generator is None:
            # Return dummy embedding for testing
            logger.warning("No embedding generator configured, using dummy embedding")
            return [0.0] * 1536
        
        try:
            embedding = await self.embedding_generator(query_text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise
    
    async def _semantic_search(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        query: RetrievalQuery
    ) -> List[RetrievedChunk]:
        """
        Perform semantic search using pgvector.
        
        Args:
            db: Database session
            query_embedding: Query embedding vector
            query: Retrieval query with filters
            
        Returns:
            List of retrieved chunks
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
    
    async def _rerank(
        self,
        chunks: List[RetrievedChunk],
        query: RetrievalQuery
    ) -> List[RetrievedChunk]:
        """
        Rerank retrieved chunks by relevance and authority.
        
        Simple reranking strategy:
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
            
            # Boost authoritative sources (could be enhanced with source authority db)
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
    
    def build_context(
        self,
        chunks: List[RetrievedChunk],
        max_tokens: int = 2000
    ) -> str:
        """
        Build context string from retrieved chunks for prompt assembly.
        
        Args:
            chunks: Retrieved chunks
            max_tokens: Maximum tokens for context (rough estimate: 1 token ≈ 4 chars)
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return ""
        
        context_parts = ["Retrieved Knowledge:\n"]
        current_length = 0
        max_chars = max_tokens * 4
        
        for i, chunk in enumerate(chunks, 1):
            chunk_text = chunk.text.strip()
            chunk_header = f"\n[Source {i}: {chunk.document_title} | {chunk.domain}/{chunk.topic}]\n"
            chunk_content = f"{chunk_text}\n"
            
            chunk_total = chunk_header + chunk_content
            if current_length + len(chunk_total) > max_chars:
                break
            
            context_parts.append(chunk_total)
            current_length += len(chunk_total)
        
        return "".join(context_parts)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get retrieval pipeline metrics."""
        return {
            "retrieval_count": self._retrieval_count,
        }


class HybridRetrievalPipeline(RetrievalPipeline):
    """
    Hybrid retrieval combining semantic and keyword search.
    
    Extends base RetrievalPipeline with keyword matching.
    """
    
    async def retrieve(
        self,
        db: AsyncSession,
        query: RetrievalQuery
    ) -> List[RetrievedChunk]:
        """Retrieve using hybrid semantic + keyword search."""
        # Get semantic results
        semantic_chunks = await super().retrieve(db, query)
        
        # Get keyword results
        keyword_chunks = await self._keyword_search(db, query)
        
        # Merge and deduplicate
        merged = self._merge_results(semantic_chunks, keyword_chunks)
        
        return merged[:query.top_k]
    
    async def _keyword_search(
        self,
        db: AsyncSession,
        query: RetrievalQuery
    ) -> List[RetrievedChunk]:
        """
        Perform keyword-based search using PostgreSQL full-text search.
        
        Args:
            db: Database session
            query: Retrieval query
            
        Returns:
            List of retrieved chunks
        """
        # Extract keywords from query
        keywords = query.query_text.lower().split()
        
        # Build LIKE query for keyword matching
        stmt = (
            select(KnowledgeChunk, KnowledgeDocument)
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        )
        
        # Add keyword filters
        keyword_filters = [
            KnowledgeChunk.chunk_text.ilike(f"%{keyword}%")
            for keyword in keywords[:5]  # Limit to first 5 keywords
        ]
        
        if keyword_filters:
            stmt = stmt.where(or_(*keyword_filters))
        
        # Apply domain/topic filters
        if query.domain:
            stmt = stmt.where(KnowledgeDocument.domain == query.domain)
        if query.topic:
            stmt = stmt.where(KnowledgeDocument.topic == query.topic)
        
        stmt = stmt.limit(query.top_k)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        # Convert to RetrievedChunk objects
        chunks = []
        for chunk, document in rows:
            # Simple keyword match scoring
            match_score = sum(
                1 for keyword in keywords 
                if keyword in chunk.chunk_text.lower()
            ) / len(keywords)
            
            chunks.append(RetrievedChunk(
                chunk_id=str(chunk.id),
                text=chunk.chunk_text,
                similarity_score=match_score,
                document_title=document.title,
                domain=document.domain,
                topic=document.topic,
                metadata=chunk.meta_data
            ))
        
        return chunks
    
    def _merge_results(
        self,
        semantic: List[RetrievedChunk],
        keyword: List[RetrievedChunk]
    ) -> List[RetrievedChunk]:
        """Merge semantic and keyword results, removing duplicates."""
        seen_ids = set()
        merged = []
        
        # Add semantic results first (higher priority)
        for chunk in semantic:
            if chunk.chunk_id not in seen_ids:
                merged.append(chunk)
                seen_ids.add(chunk.chunk_id)
        
        # Add keyword results
        for chunk in keyword:
            if chunk.chunk_id not in seen_ids:
                # Boost score slightly for keyword match
                chunk.similarity_score = min(1.0, chunk.similarity_score + 0.05)
                merged.append(chunk)
                seen_ids.add(chunk.chunk_id)
        
        # Sort by score
        merged.sort(key=lambda c: c.similarity_score, reverse=True)
        
        return merged
