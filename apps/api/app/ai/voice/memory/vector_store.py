import uuid
import logging
from typing import List, Tuple, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.candidate_memory import CandidateMemory
from app.db.session import SessionLocal

logger = logging.getLogger("vector_store")

class VectorStore:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    async def save_embedding(
        self,
        memory_id: uuid.UUID,
        embedding: List[float],
        db: Optional[AsyncSession] = None
    ) -> bool:
        """
        Saves or updates the vector embedding for an existing memory ID.
        """
        async def _run(session: AsyncSession) -> bool:
            stmt = select(CandidateMemory).where(CandidateMemory.id == memory_id)
            result = await session.execute(stmt)
            memory = result.scalar_one_or_none()
            if memory:
                memory.embedding = embedding
                await session.commit()
                return True
            return False

        if db:
            return await _run(db)
        else:
            async with self.session_factory() as session:
                return await _run(session)

    async def similarity_search(
        self,
        candidate_id: uuid.UUID,
        query_embedding: List[float],
        limit: int = 5,
        min_similarity: float = 0.0,
        db: Optional[AsyncSession] = None
    ) -> List[Tuple[CandidateMemory, float]]:
        """
        Executes a vector cosine similarity search in PostgreSQL via pgvector.
        Returns a list of tuples containing (CandidateMemory, similarity_score).
        """
        if not query_embedding:
            return []

        async def _run(session: AsyncSession) -> List[Tuple[CandidateMemory, float]]:
            # Cosine distance in pgvector: similarity = 1 - cosine_distance
            cosine_dist = CandidateMemory.embedding.cosine_distance(query_embedding)
            similarity = (1.0 - cosine_dist).label("similarity")

            stmt = (
                select(CandidateMemory, similarity)
                .where(CandidateMemory.candidate_id == candidate_id)
                .where(CandidateMemory.embedding.isnot(None))
                .order_by(cosine_dist.asc())
                .limit(limit)
            )

            result = await session.execute(stmt)
            rows = result.all()
            
            # Filter results by minimum similarity threshold
            filtered = []
            for memory, sim_score in rows:
                score = float(sim_score) if sim_score is not None else 0.0
                if score >= min_similarity:
                    filtered.append((memory, score))
            return filtered

        if db:
            return await _run(db)
        else:
            async with self.session_factory() as session:
                return await _run(session)
