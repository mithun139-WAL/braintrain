import uuid
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.candidate_memory import CandidateMemory
from app.ai.voice.memory.memory_types import MemoryObject, MemoryType
from app.db.session import SessionLocal

logger = logging.getLogger("memory_store")

class MemoryStore:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def _to_dataclass(self, db_mem: CandidateMemory) -> MemoryObject:
        return MemoryObject(
            memory_id=db_mem.id,
            candidate_id=db_mem.candidate_id,
            memory_type=MemoryType(db_mem.memory_type),
            content=db_mem.content,
            embedding=db_mem.embedding,
            confidence_score=db_mem.confidence_score,
            relevance_score=db_mem.relevance_score,
            importance_score=db_mem.importance_score,
            decay_factor=db_mem.decay_factor,
            access_count=db_mem.access_count,
            source_session_id=db_mem.source_session_id,
            behavioral_tags=db_mem.behavioral_tags or [],
            created_at=db_mem.created_at,
            last_accessed=db_mem.last_accessed,
        )

    async def create_memory(self, memory: MemoryObject, db: Optional[AsyncSession] = None) -> MemoryObject:
        """
        Persists a new memory into the database.
        """
        async def _run(session: AsyncSession) -> MemoryObject:
            db_mem = CandidateMemory(
                id=memory.memory_id,
                candidate_id=memory.candidate_id,
                source_session_id=memory.source_session_id,
                memory_type=memory.memory_type.value,
                content=memory.content,
                embedding=memory.embedding,
                confidence_score=memory.confidence_score,
                relevance_score=memory.relevance_score,
                importance_score=memory.importance_score,
                decay_factor=memory.decay_factor,
                access_count=memory.access_count,
                behavioral_tags=memory.behavioral_tags,
                created_at=memory.created_at,
                last_accessed=memory.last_accessed,
            )
            session.add(db_mem)
            await session.commit()
            return self._to_dataclass(db_mem)

        if db:
            return await _run(db)
        else:
            async with self.session_factory() as session:
                return await _run(session)

    async def get_memory(self, memory_id: uuid.UUID, db: Optional[AsyncSession] = None) -> Optional[MemoryObject]:
        """
        Retrieves a single memory by ID.
        """
        async def _run(session: AsyncSession) -> Optional[MemoryObject]:
            stmt = select(CandidateMemory).where(CandidateMemory.id == memory_id)
            result = await session.execute(stmt)
            db_mem = result.scalar_one_or_none()
            return self._to_dataclass(db_mem) if db_mem else None

        if db:
            return await _run(db)
        else:
            async with self.session_factory() as session:
                return await _run(session)

    async def update_memory(self, memory: MemoryObject, db: Optional[AsyncSession] = None) -> bool:
        """
        Updates an existing memory.
        """
        async def _run(session: AsyncSession) -> bool:
            stmt = select(CandidateMemory).where(CandidateMemory.id == memory.memory_id)
            result = await session.execute(stmt)
            db_mem = result.scalar_one_or_none()
            if not db_mem:
                return False

            db_mem.content = memory.content
            db_mem.embedding = memory.embedding
            db_mem.confidence_score = memory.confidence_score
            db_mem.relevance_score = memory.relevance_score
            db_mem.importance_score = memory.importance_score
            db_mem.decay_factor = memory.decay_factor
            db_mem.access_count = memory.access_count
            db_mem.behavioral_tags = memory.behavioral_tags
            db_mem.last_accessed = memory.last_accessed
            
            await session.commit()
            return True

        if db:
            return await _run(db)
        else:
            async with self.session_factory() as session:
                return await _run(session)

    async def increment_access(self, memory_id: uuid.UUID, db: Optional[AsyncSession] = None) -> bool:
        """
        Increments the access count and updates the last accessed timestamp.
        """
        async def _run(session: AsyncSession) -> bool:
            stmt = select(CandidateMemory).where(CandidateMemory.id == memory_id)
            result = await session.execute(stmt)
            db_mem = result.scalar_one_or_none()
            if not db_mem:
                return False

            db_mem.access_count += 1
            db_mem.last_accessed = datetime.utcnow()
            await session.commit()
            return True

        if db:
            return await _run(db)
        else:
            async with self.session_factory() as session:
                return await _run(session)

    async def delete_memory(self, memory_id: uuid.UUID, db: Optional[AsyncSession] = None) -> bool:
        """
        Deletes a memory by ID.
        """
        async def _run(session: AsyncSession) -> bool:
            stmt = delete(CandidateMemory).where(CandidateMemory.id == memory_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

        if db:
            return await _run(db)
        else:
            async with self.session_factory() as session:
                return await _run(session)

    async def get_all_candidate_memories(
        self,
        candidate_id: uuid.UUID,
        db: Optional[AsyncSession] = None
    ) -> List[MemoryObject]:
        """
        Fetches all memories associated with a candidate ID.
        """
        async def _run(session: AsyncSession) -> List[MemoryObject]:
            stmt = select(CandidateMemory).where(CandidateMemory.candidate_id == candidate_id)
            result = await session.execute(stmt)
            return [self._to_dataclass(row) for row in result.scalars()]

        if db:
            return await _run(db)
        else:
            async with self.session_factory() as session:
                return await _run(session)
