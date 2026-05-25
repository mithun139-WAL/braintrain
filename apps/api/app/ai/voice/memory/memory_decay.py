import math
import logging
from datetime import datetime
from app.ai.voice.memory.memory_types import MemoryObject, MemoryType

logger = logging.getLogger("memory_decay")

class MemoryDecay:
    def __init__(self, base_decay_rate: float = 0.05):
        """
        :param base_decay_rate: Base decay multiplier per day.
        """
        self.base_decay_rate = base_decay_rate

    def calculate_relevance(self, memory: MemoryObject, current_time: datetime = None) -> float:
        """
        Computes the decay-adjusted relevance score using exponential time decay.
        Formula: R(t) = base_relevance * e^(-decay_rate * days_since_created)
        
        Decay rate is mitigated by:
        1. Higher importance score
        2. Higher access count (reinforcement)
        3. Memory Type (BEHAVIORAL decays slower than EPISODIC)
        """
        if not current_time:
            current_time = datetime.utcnow()

        days_passed = (current_time - memory.created_at).total_seconds() / 86400.0
        if days_passed < 0:
            days_passed = 0.0

        # Memory category specific multiplier
        # Behavioral memories (patterns) persist longer than one-off episodic memories
        type_multiplier = 1.0
        if memory.memory_type == MemoryType.BEHAVIORAL:
            type_multiplier = 0.5  # half the decay speed
        elif memory.memory_type == MemoryType.SEMANTIC:
            type_multiplier = 0.3  # semantic profile info decays very slowly

        # Mitigate decay rate based on importance and access reinforcement
        importance_factor = 1.0 + memory.importance_score
        access_factor = 1.0 + math.log1p(memory.access_count)
        
        # Effective decay rate
        decay_rate = (self.base_decay_rate * type_multiplier) / (importance_factor * access_factor)
        
        # Calculate exponential decay
        decayed_relevance = memory.relevance_score * math.exp(-decay_rate * days_passed)
        
        # Bound the score between [0.0, 1.0]
        return max(0.0, min(1.0, decayed_relevance))

    def reinforce_access(self, memory: MemoryObject) -> None:
        """
        Reinforces a memory upon retrieval. Bumps relevance back up and increments count.
        """
        memory.access_count += 1
        memory.last_accessed = datetime.utcnow()
        # Bumping relevance score back up with reinforcement boost
        memory.relevance_score = min(1.0, memory.relevance_score + 0.15)
        # Bumping importance slightly on repeated usage
        memory.importance_score = min(1.0, memory.importance_score + 0.02)
        logger.info(
            "memory_decay | reinforced_memory | id: %s | access_count: %d | relevance: %.2f",
            memory.memory_id,
            memory.access_count,
            memory.relevance_score
        )

    def strengthen_repeated_pattern(self, memory: MemoryObject, repeat_multiplier: float = 1.2) -> None:
        """
        Strengthens memory when the same pattern is detected in subsequent sessions.
        Decreases the decay factor and boosts importance.
        """
        memory.decay_factor = max(0.1, memory.decay_factor / repeat_multiplier)
        memory.importance_score = min(1.0, memory.importance_score * repeat_multiplier)
        memory.relevance_score = 1.0  # Reset relevance
        logger.info(
            "memory_decay | pattern_strengthened | id: %s | importance: %.2f | decay_factor: %.2f",
            memory.memory_id,
            memory.importance_score,
            memory.decay_factor
        )
