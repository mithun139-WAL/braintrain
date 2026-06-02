import logging
import uuid
import numpy as np
from typing import List, Optional
from app.ai.voice.memory.memory_types import MemoryObject, MemoryType
from app.ai.voice.memory.memory_store import MemoryStore
from app.ai.voice.memory.vector_store import VectorStore
from app.ai.voice.memory.memory_encoder import MemoryEncoder

logger = logging.getLogger("memory_compactor")

class MemoryCompactor:
    def __init__(
        self,
        memory_store: MemoryStore,
        vector_store: VectorStore,
        encoder: MemoryEncoder,
        similarity_threshold: float = 0.85
    ):
        self.memory_store = memory_store
        self.vector_store = vector_store
        self.encoder = encoder
        self.similarity_threshold = similarity_threshold

    async def compact_candidate_memories(self, candidate_id: uuid.UUID) -> int:
        """
        Runs compaction for all memories of a candidate.
        Compares pairwise within each MemoryType category.
        Merges similar memories, updating the primary and deleting the secondary.
        Returns the number of merged memories.
        """
        memories = await self.memory_store.get_all_candidate_memories(candidate_id)
        if len(memories) < 2:
            return 0

        # Group by memory type
        grouped = {}
        for m in memories:
            grouped.setdefault(m.memory_type, []).append(m)

        merged_count = 0

        for mtype, m_list in grouped.items():
            if len(m_list) < 2:
                continue

            # Pairwise comparison
            visited = set()
            for i in range(len(m_list)):
                m1 = m_list[i]
                if m1.memory_id in visited:
                    continue

                for j in range(i + 1, len(m_list)):
                    m2 = m_list[j]
                    if m2.memory_id in visited:
                        continue

                    # Calculate cosine similarity of embeddings
                    if m1.embedding and m2.embedding:
                        similarity = self._cosine_similarity(m1.embedding, m2.embedding)
                        if similarity >= self.similarity_threshold:
                            logger.info(
                                "Compacting similar memories: %s & %s (similarity: %.2f)",
                                m1.memory_id, m2.id if hasattr(m2, 'id') else m2.memory_id, similarity
                            )
                            # Merge m2 into m1
                            await self._merge_memories(m1, m2)
                            visited.add(m2.memory_id)
                            merged_count += 1

        return merged_count

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        a = np.array(vec1)
        b = np.array(vec2)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    async def _merge_memories(self, m1: MemoryObject, m2: MemoryObject) -> None:
        """
        Merges second memory (m2) into the first (m1).
        Updates m1 in DB and deletes m2.
        """
        # Combine text content deterministically
        if m1.content.lower() in m2.content.lower():
            m1.content = m2.content
        elif m2.content.lower() in m1.content.lower():
            pass  # keep m1
        else:
            m1.content = f"{m1.content}; {m2.content}"

        # Consolidate metadata
        m1.importance_score = min(1.0, max(m1.importance_score, m2.importance_score) + 0.1)
        m1.confidence_score = (m1.confidence_score + m2.confidence_score) / 2.0
        m1.access_count += m2.access_count
        m1.behavioral_tags = list(set(m1.behavioral_tags + m2.behavioral_tags))
        m1.decay_factor = min(m1.decay_factor, m2.decay_factor) * 0.9  # Persist longer

        # Re-encode combined content
        m1.embedding = await self.encoder.encode(m1.content)

        # Update in database
        await self.memory_store.update_memory(m1)
        await self.memory_store.delete_memory(m2.memory_id)
        
        logger.info("Successfully merged memory %s into %s", m2.memory_id, m1.memory_id)
