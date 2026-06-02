import uuid
import logging
from typing import List, Optional
from app.ai.voice.memory.memory_types import MemoryObject, MemoryType
from app.ai.voice.memory.memory_store import MemoryStore
from app.ai.voice.memory.memory_encoder import MemoryEncoder

logger = logging.getLogger("episodic_memory")

class EpisodicMemory:
    def __init__(self, memory_store: MemoryStore, encoder: MemoryEncoder):
        self.memory_store = memory_store
        self.encoder = encoder

    async def record_moment(
        self,
        candidate_id: uuid.UUID,
        session_id: uuid.UUID,
        description: str,
        importance_score: float = 0.5,
        confidence_score: float = 1.0,
        tags: Optional[List[str]] = None
    ) -> MemoryObject:
        """
        Records a notable episode or milestone from an interview session.
        """
        embedding = await self.encoder.encode(description)
        behavioral_tags = tags or ["notable_moment"]
        
        mem = MemoryObject(
            memory_id=uuid.uuid4(),
            candidate_id=candidate_id,
            memory_type=MemoryType.EPISODIC,
            content=description,
            embedding=embedding,
            confidence_score=confidence_score,
            importance_score=importance_score,
            source_session_id=session_id,
            behavioral_tags=behavioral_tags
        )
        return await self.memory_store.create_memory(mem)
