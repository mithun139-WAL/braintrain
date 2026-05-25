import uuid
import logging
from typing import List, Optional
from app.ai.voice.memory.memory_types import MemoryObject, MemoryType
from app.ai.voice.memory.memory_store import MemoryStore
from app.ai.voice.memory.memory_encoder import MemoryEncoder

logger = logging.getLogger("behavioral_memory")

class BehavioralMemory:
    def __init__(self, memory_store: MemoryStore, encoder: MemoryEncoder):
        self.memory_store = memory_store
        self.encoder = encoder

    async def record_behavior_pattern(
        self,
        candidate_id: uuid.UUID,
        session_id: uuid.UUID,
        pattern_description: str,
        confidence_score: float = 0.8,
        importance_score: float = 0.6,
        tags: Optional[List[str]] = None
    ) -> MemoryObject:
        """
        Saves a rolling candidate behavioral trend, e.g., 'Candidate shows high hesitation under stress'.
        """
        embedding = await self.encoder.encode(pattern_description)
        behavioral_tags = tags or ["behavioral_trend"]

        mem = MemoryObject(
            memory_id=uuid.uuid4(),
            candidate_id=candidate_id,
            memory_type=MemoryType.BEHAVIORAL,
            content=pattern_description,
            embedding=embedding,
            confidence_score=confidence_score,
            importance_score=importance_score,
            source_session_id=session_id,
            behavioral_tags=behavioral_tags
        )
        return await self.memory_store.create_memory(mem)
