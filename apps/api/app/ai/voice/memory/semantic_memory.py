import uuid
import logging
from typing import List, Optional
from datetime import datetime
from app.ai.voice.memory.memory_types import MemoryObject, MemoryType
from app.ai.voice.memory.memory_store import MemoryStore
from app.ai.voice.memory.memory_encoder import MemoryEncoder

logger = logging.getLogger("semantic_memory")

class SemanticMemory:
    def __init__(self, memory_store: MemoryStore, encoder: MemoryEncoder):
        self.memory_store = memory_store
        self.encoder = encoder

    async def add_skill_profile(
        self,
        candidate_id: uuid.UUID,
        skill_name: str,
        proficiency: str,
        source_session_id: Optional[uuid.UUID] = None
    ) -> MemoryObject:
        """
        Records a candidate's skill profile, e.g. "Candidate claims proficiency in Node.js: expert".
        """
        content = f"Candidate has expertise in {skill_name} ({proficiency})."
        embedding = await self.encoder.encode(content)
        
        mem = MemoryObject(
            memory_id=uuid.uuid4(),
            candidate_id=candidate_id,
            memory_type=MemoryType.SEMANTIC,
            content=content,
            embedding=embedding,
            confidence_score=0.9,
            importance_score=0.6,
            source_session_id=source_session_id,
            behavioral_tags=["skill", skill_name.lower()]
        )
        return await self.memory_store.create_memory(mem)

    async def add_architecture_preference(
        self,
        candidate_id: uuid.UUID,
        preference_description: str,
        source_session_id: Optional[uuid.UUID] = None
    ) -> MemoryObject:
        """
        Records candidate architectural preferences, e.g. "Favors microservices over monoliths".
        """
        content = f"Architectural Preference: {preference_description}"
        embedding = await self.encoder.encode(content)

        mem = MemoryObject(
            memory_id=uuid.uuid4(),
            candidate_id=candidate_id,
            memory_type=MemoryType.SEMANTIC,
            content=content,
            embedding=embedding,
            confidence_score=0.8,
            importance_score=0.5,
            source_session_id=source_session_id,
            behavioral_tags=["architecture", "preference"]
        )
        return await self.memory_store.create_memory(mem)
