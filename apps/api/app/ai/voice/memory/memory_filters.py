import uuid
from typing import List, Optional
from app.ai.voice.memory.memory_types import MemoryObject, MemoryType

class MemoryFilters:
    @staticmethod
    def filter_by_type(memories: List[MemoryObject], memory_types: List[MemoryType]) -> List[MemoryObject]:
        """Filters memories by matching their memory type."""
        return [m for m in memories if m.memory_type in memory_types]

    @staticmethod
    def filter_by_tags(memories: List[MemoryObject], tags: List[str], match_all: bool = False) -> List[MemoryObject]:
        """
        Filters memories by matching tags.
        If match_all is True, all specified tags must be present.
        If match_all is False, at least one tag must be present.
        """
        if not tags:
            return memories

        target_tags = set(tag.lower() for tag in tags)
        filtered = []
        for m in memories:
            mem_tags = set(t.lower() for t in m.behavioral_tags)
            if match_all:
                if target_tags.issubset(mem_tags):
                    filtered.append(m)
            else:
                if not target_tags.isdisjoint(mem_tags):
                    filtered.append(m)
        return filtered

    @staticmethod
    def filter_by_importance(memories: List[MemoryObject], min_importance: float) -> List[MemoryObject]:
        """Filters memories by minimum importance score."""
        return [m for m in memories if m.importance_score >= min_importance]

    @staticmethod
    def filter_by_confidence(memories: List[MemoryObject], min_confidence: float) -> List[MemoryObject]:
        """Filters memories by minimum confidence score."""
        return [m for m in memories if m.confidence_score >= min_confidence]

    @staticmethod
    def filter_by_session(memories: List[MemoryObject], session_id: uuid.UUID) -> List[MemoryObject]:
        """Filters memories matching the source session ID."""
        return [m for m in memories if m.source_session_id == session_id]

    @staticmethod
    def exclude_session(memories: List[MemoryObject], session_id: uuid.UUID) -> List[MemoryObject]:
        """Filters memories that did not originate from the current session."""
        return [m for m in memories if m.source_session_id != session_id]
