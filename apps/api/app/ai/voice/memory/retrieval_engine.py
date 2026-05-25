import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.voice.memory.memory_types import MemoryObject
from app.ai.voice.memory.memory_encoder import MemoryEncoder
from app.ai.voice.memory.vector_store import VectorStore
from app.ai.voice.memory.memory_store import MemoryStore
from app.ai.voice.memory.memory_decay import MemoryDecay
from app.ai.voice.memory.retrieval_ranker import RetrievalRanker
from app.ai.voice.memory.memory_filters import MemoryFilters

logger = logging.getLogger("retrieval_engine")

class RetrievalEngine:
    def __init__(
        self,
        encoder: MemoryEncoder,
        vector_store: VectorStore,
        memory_store: MemoryStore,
        decay_manager: MemoryDecay,
        ranker: RetrievalRanker
    ):
        self.encoder = encoder
        self.vector_store = vector_store
        self.memory_store = memory_store
        self.decay_manager = decay_manager
        self.ranker = ranker

    async def retrieve_relevant_memories(
        self,
        candidate_id: uuid.UUID,
        query_text: str,
        policy_filters: Dict[str, Any],
        context: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> List[MemoryObject]:
        """
        Executes a hybrid retrieval flow:
        1. Encodes query text into a vector embedding.
        2. Query vector store for candidates.
        3. Applies decay corrections to memory relevance scores.
        4. Ranks candidates using the composite scoring formula.
        5. Filters by policy constraints (types, min importance).
        6. Reinforces the top retrieved memories.
        """
        if not query_text or not query_text.strip():
            return []

        # 1. Generate query embedding
        query_vector = await self.encoder.encode(query_text)

        # 2. Similarity search in vector store (broad select, limit to 15)
        raw_results = await self.vector_store.similarity_search(
            candidate_id=candidate_id,
            query_embedding=query_vector,
            limit=15,
            min_similarity=0.3,
            db=db
        )
        if not raw_results:
            return []

        # 3. Apply time-decay to compute contemporary relevance
        decayed_results = []
        for memory, sim_score in raw_results:
            # Side-effect: update relevance field on the object in-memory
            memory.relevance_score = self.decay_manager.calculate_relevance(memory)
            decayed_results.append((memory, sim_score))

        # 4. Rank with composite scores
        ranked_results = self.ranker.rank_memories(decayed_results, context)

        # Extract memory objects
        memories = [m for m, score in ranked_results]

        # 5. Filter by policies
        allowed_types = policy_filters.get("allowed_types")
        if allowed_types:
            memories = MemoryFilters.filter_by_type(memories, allowed_types)

        min_importance = policy_filters.get("min_importance", 0.0)
        memories = MemoryFilters.filter_by_importance(memories, min_importance)

        # Limit final output count
        limit = policy_filters.get("limit", 3)
        final_memories = memories[:limit]

        # 6. Reinforce accessed memories in database asynchronously
        for mem in final_memories:
            self.decay_manager.reinforce_access(mem)
            await self.memory_store.increment_access(mem.memory_id, db=db)

        return final_memories
