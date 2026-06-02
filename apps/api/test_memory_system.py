import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List

from app.ai.voice.memory.memory_types import MemoryObject, MemoryType
from app.ai.voice.memory.memory_encoder import MemoryEncoder
from app.ai.voice.memory.memory_decay import MemoryDecay
from app.ai.voice.memory.memory_filters import MemoryFilters
from app.ai.voice.memory.retrieval_ranker import RetrievalRanker
from app.ai.voice.memory.retrieval_policies import RetrievalPolicies
from app.ai.voice.memory.memory_compactor import MemoryCompactor
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.state.conversation_state import ConversationState
from app.ai.voice.state.candidate_state import CandidateState

class MockSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.deleted = []

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def execute(self, stmt):
        class Result:
            def scalars(self):
                return []
            def all(self):
                return []
        return Result()

    async def delete(self, obj):
        self.deleted.append(obj)

async def run_tests():
    print("=== Running Memory & Retrieval Layer Tests ===")

    # Test 1: Encoder
    print("\n[Test 1] Testing MemoryEncoder...")
    encoder = MemoryEncoder()
    emb1 = await encoder.encode("Test embedding string")
    emb2 = await encoder.encode("Test embedding string")
    emb3 = await encoder.encode("Different embedding string")
    
    assert len(emb1) == 1536, f"Expected 1536 dimension, got {len(emb1)}"
    assert emb1 == emb2, "Expected deterministic fallback embeddings for identical text"
    assert emb1 != emb3, "Expected different embeddings for different text"
    print("✓ MemoryEncoder passed.")

    # Test 2: Decay Manager
    print("\n[Test 2] Testing MemoryDecay...")
    decay_manager = MemoryDecay(base_decay_rate=0.1) # 10% base rate
    
    candidate_id = uuid.uuid4()
    mem = MemoryObject(
        memory_id=uuid.uuid4(),
        candidate_id=candidate_id,
        memory_type=MemoryType.EPISODIC,
        content="Candidate struggled with cache consistency",
        created_at=datetime.utcnow() - timedelta(days=10), # 10 days ago
        relevance_score=1.0,
        importance_score=0.5,
        access_count=0
    )
    
    # Calculate decayed relevance
    rel_after_10_days = decay_manager.calculate_relevance(mem)
    print(f"Relevance after 10 days (no access): {rel_after_10_days:.4f}")
    assert rel_after_10_days < 1.0, "Expected relevance to decay over 10 days"

    # Reinforce access
    decay_manager.reinforce_access(mem)
    assert mem.access_count == 1, "Expected access count to increment"
    assert mem.relevance_score > rel_after_10_days, "Expected access reinforcement to boost relevance"
    print("✓ MemoryDecay passed.")

    # Test 3: Filters
    print("\n[Test 3] Testing MemoryFilters...")
    mem1 = MemoryObject(
        memory_id=uuid.uuid4(),
        candidate_id=candidate_id,
        memory_type=MemoryType.SEMANTIC,
        content="Strong in React",
        behavioral_tags=["react", "frontend"],
        importance_score=0.7
    )
    mem2 = MemoryObject(
        memory_id=uuid.uuid4(),
        candidate_id=candidate_id,
        memory_type=MemoryType.BEHAVIORAL,
        content="Verbose under stress",
        behavioral_tags=["stress", "verbosity"],
        importance_score=0.4
    )
    mems = [mem1, mem2]
    
    filtered_types = MemoryFilters.filter_by_type(mems, [MemoryType.SEMANTIC])
    assert len(filtered_types) == 1 and filtered_types[0].content == "Strong in React"
    
    filtered_tags = MemoryFilters.filter_by_tags(mems, ["stress"])
    assert len(filtered_tags) == 1 and filtered_tags[0].content == "Verbose under stress"

    filtered_importance = MemoryFilters.filter_by_importance(mems, 0.5)
    assert len(filtered_importance) == 1 and filtered_importance[0].content == "Strong in React"
    print("✓ MemoryFilters passed.")

    # Test 4: Retrieval Ranker
    print("\n[Test 4] Testing RetrievalRanker...")
    ranker = RetrievalRanker()
    
    context_sys_design = {"interview_phase": "SYSTEM_DESIGN", "stress_level": "NORMAL"}
    mem_arch = MemoryObject(
        memory_id=uuid.uuid4(),
        candidate_id=candidate_id,
        memory_type=MemoryType.SEMANTIC,
        content="Understands event-driven architecture design",
        behavioral_tags=["architecture", "design"],
        importance_score=0.6,
        created_at=datetime.utcnow()
    )
    mem_other = MemoryObject(
        memory_id=uuid.uuid4(),
        candidate_id=candidate_id,
        memory_type=MemoryType.EPISODIC,
        content="Struggled with simple array sort question",
        behavioral_tags=["sorting"],
        importance_score=0.5,
        created_at=datetime.utcnow()
    )
    
    # Check ranking during System Design phase
    # Both have same semantic similarity (say 0.8)
    ranked = ranker.rank_memories([(mem_arch, 0.8), (mem_other, 0.8)], context_sys_design)
    assert ranked[0][0].memory_id == mem_arch.memory_id, "Expected architecture memory to rank higher in SYSTEM_DESIGN context"
    print("✓ RetrievalRanker passed.")

    # Test 5: Retrieval Policies
    print("\n[Test 5] Testing RetrievalPolicies...")
    conversation_state = ConversationState(
        messages=[],
        current_question_id=None,
        current_question_text=None,
        current_topic="caching",
        current_speaker=None,
        turn_count=15, # Trigger pressure round policy
        started_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    interview_state = InterviewState(
        session_id=str(uuid.uuid4()),
        conversation=conversation_state,
        candidate=CandidateState(),
        mode="ONE_ON_ONE_AI",
        difficulty="MEDIUM",
        adaptive_enabled=True,
        panel_mode=False,
        completed=False,
    )
    # Add pressure level
    interview_state.pressure_level = "HIGH"
    
    ctx = RetrievalPolicies.get_policy_context(interview_state)
    assert ctx["interview_phase"] == "PRESSURE_ROUND"
    assert ctx["stress_level"] == "HIGH"
    
    filters = RetrievalPolicies.get_query_filters(ctx)
    assert MemoryType.BEHAVIORAL in filters["allowed_types"]
    assert filters["min_importance"] == 0.5
    print("✓ RetrievalPolicies passed.")

    print("\n=== All Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
