import math
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from app.ai.voice.memory.memory_types import MemoryObject, MemoryType

logger = logging.getLogger("retrieval_ranker")

class RetrievalRanker:
    def __init__(
        self,
        similarity_weight: float = 0.45,
        importance_weight: float = 0.20,
        recency_weight: float = 0.15,
        frequency_weight: float = 0.05,
        decay_penalty_weight: float = 0.15
    ):
        self.similarity_weight = similarity_weight
        self.importance_weight = importance_weight
        self.recency_weight = recency_weight
        self.frequency_weight = frequency_weight
        self.decay_penalty_weight = decay_penalty_weight

    def rank_memories(
        self,
        memories_with_similarity: List[Tuple[MemoryObject, float]],
        context: Dict[str, Any],
        current_time: Optional[datetime] = None
    ) -> List[Tuple[MemoryObject, float]]:
        """
        Ranks a list of memories based on a composite scoring formula.
        Returns a sorted list of (MemoryObject, composite_score) tuples, descending.
        """
        if not current_time:
            current_time = datetime.utcnow()

        scored_memories = []
        for memory, sim_score in memories_with_similarity:
            # 1. Semantic Similarity
            semantic_score = sim_score * self.similarity_weight

            # 2. Recency Score
            days_since_created = (current_time - memory.created_at).total_seconds() / 86400.0
            recency = math.exp(-0.05 * max(0.0, days_since_created))
            recency_score = recency * self.recency_weight

            # 3. Importance Weight
            importance_score = memory.importance_score * self.importance_weight

            # 4. Access Frequency Boost
            freq_score = math.log1p(memory.access_count) * self.frequency_weight

            # 5. Decay Penalty (reduces score if relevance is low)
            decay_penalty = (1.0 - memory.relevance_score) * self.decay_penalty_weight

            # 6. Context-Interview Stage Alignment Boost
            context_boost = self._calculate_context_boost(memory, context)

            # Composite formula
            composite_score = (
                semantic_score
                + recency_score
                + importance_score
                + freq_score
                + context_boost
                - decay_penalty
            )

            scored_memories.append((memory, composite_score))

        # Sort descending by composite score
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return scored_memories

    def _calculate_context_boost(self, memory: MemoryObject, context: Dict[str, Any]) -> float:
        """
        Applies a boost if the memory tags match the active interview context.
        """
        boost = 0.0
        phase = context.get("interview_phase", "").upper()
        stress = context.get("stress_level", "").upper()
        tags = set(t.lower() for t in memory.behavioral_tags)

        # Boost during system design rounds
        if phase == "SYSTEM_DESIGN":
            if memory.memory_type == MemoryType.SEMANTIC and ("architecture" in tags or "system" in tags):
                boost += 0.20
            # If they previously struggled with a design topic
            if "weakness" in tags and "design" in tags:
                boost += 0.15

        # Boost during behavioral rounds
        elif phase == "BEHAVIORAL":
            if "communication" in tags or "leadership" in tags or "behavioral" in tags:
                boost += 0.20

        # Boost during pressure rounds or if stress is high
        if phase == "PRESSURE_ROUND" or stress == "HIGH":
            # Target previous hesitation patterns/confidence slips
            if memory.memory_type == MemoryType.BEHAVIORAL:
                if "hesitation" in tags or "stress" in tags or "confidence" in tags:
                    boost += 0.25
                else:
                    boost += 0.10

        return boost
