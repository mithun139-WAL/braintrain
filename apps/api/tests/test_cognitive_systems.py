import sys
from unittest.mock import MagicMock
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid

# ══════════════════════════════════════════════════════════════════════════════
# SQLAlchemy Module Stubbing (MUST RUN BEFORE ANY OTHER IMPORTS)
# ══════════════════════════════════════════════════════════════════════════════

TestBase = declarative_base()

class LearningMemoryNode(TestBase):
    __tablename__ = "learning_memory_nodes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), nullable=False)
    concept_name = Column(String(255), nullable=False)
    concept_type = Column(String(64), default="concept")
    familiarity_score = Column(Float, default=50.0)
    confidence_score = Column(Float, default=50.0)
    recall_latency = Column(Float, default=1.0)
    retention_strength = Column(Float, default=50.0)
    pressure_recall_stability = Column(Float, default=50.0)
    retry_success_rate = Column(Float, default=1.0)
    exposure_count = Column(Integer, default=0)
    mastery_level = Column(Float, default=50.0)
    is_fragile = Column(Boolean, default=False)
    is_weak_recall = Column(Boolean, default=False)
    is_strong_recall = Column(Boolean, default=False)
    last_exposed_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    next_review_at = Column(DateTime)

    def __init__(self, **kwargs):
        defaults = {
            "familiarity_score": 50.0,
            "confidence_score": 50.0,
            "recall_latency": 1.0,
            "retention_strength": 50.0,
            "pressure_recall_stability": 50.0,
            "retry_success_rate": 1.0,
            "exposure_count": 0,
            "mastery_level": 50.0,
            "is_fragile": False,
            "is_weak_recall": False,
            "is_strong_recall": False,
            "concept_type": "concept"
        }
        for k, v in defaults.items():
            setattr(self, k, v)
        for k, v in kwargs.items():
            setattr(self, k, v)

class LearningMemoryEdge(TestBase):
    __tablename__ = "learning_memory_edges"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), nullable=False)
    source_node_id = Column(UUID(as_uuid=True), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), nullable=False)
    relationship_type = Column(String(64), default="conceptual")
    strength = Column(Float, default=0.5)
    created_at = Column(DateTime)

    def __init__(self, **kwargs):
        defaults = {
            "relationship_type": "conceptual",
            "strength": 0.5
        }
        for k, v in defaults.items():
            setattr(self, k, v)
        for k, v in kwargs.items():
            setattr(self, k, v)

# Inject stub into sys.modules to prevent SQLAlchemy mapper configuration conflicts
mock_memory_mod = MagicMock()
mock_memory_mod.LearningMemoryNode = LearningMemoryNode
mock_memory_mod.LearningMemoryEdge = LearningMemoryEdge
sys.modules["app.db.models.learning_memory"] = mock_memory_mod


import pytest
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.ai.intelligence.memory.reinforcement_engine import MemoryReinforcementEngine
from app.ai.intelligence.communication.communication_engine import CommunicationIntelligenceEngine
from app.ai.intelligence.strategic.strategic_engine import StrategicThinkingEngine
from app.ai.orchestrators.contracts.interview_contracts import InterviewPhase


# ══════════════════════════════════════════════════════════════════════════════
# Database Mocks
# ══════════════════════════════════════════════════════════════════════════════

class MockResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return self._items

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None


class MockAsyncSession:
    def __init__(self, nodes=None, edges=None):
        self.nodes = nodes or []
        self.edges = edges or []
        self.committed = False
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def execute(self, stmt):
        stmt_str = str(stmt).lower()
        if "learning_memory_nodes" in stmt_str:
            binds = stmt.compile().params
            concept_name = binds.get("concept_name_1") or binds.get("concept_name")
            if concept_name:
                filtered = [n for n in self.nodes if n.concept_name == concept_name]
                return MockResult(filtered)
            return MockResult(self.nodes)
        elif "learning_memory_edges" in stmt_str:
            return MockResult(self.edges)
        return MockResult([])


# ══════════════════════════════════════════════════════════════════════════════
# Memory Reinforcement Engine Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestMemoryReinforcementEngine:
    
    def test_calculate_retention_score(self):
        engine = MemoryReinforcementEngine()
        
        # Scenario 1: Fresh exposure (0 days ago), should have ~100% retention
        node1 = LearningMemoryNode(
            concept_name="caching",
            last_exposed_at=datetime.utcnow(),
            mastery_level=80.0,
            retry_success_rate=1.0,
            exposure_count=1
        )
        r1 = engine.calculate_retention_score(node1)
        assert r1 == 100.0
        
        # Scenario 2: Decay after 5 days with low stability
        # Stability = base_stability(50/10=5) * retry_factor(0.5) * exposure_bonus(1.4) = 3.5 days
        # R = 100 * e^(-5 / 3.5) = 100 * e^(-1.428) = ~23.9%
        node2 = LearningMemoryNode(
            concept_name="sharding",
            last_exposed_at=datetime.utcnow() - timedelta(days=5),
            mastery_level=50.0,
            familiarity_score=50.0,
            confidence_score=50.0,
            pressure_recall_stability=50.0,
            retry_success_rate=0.5,
            exposure_count=1
        )
        r2 = engine.calculate_retention_score(node2)
        assert 20.0 <= r2 <= 28.0

        # Scenario 3: High stability, should decay much slower
        # Stability = base_stability(80/10=8) * retry_factor(1.0) * exposure_bonus(1 + 0.4*5 = 3.0) = 24.0 days
        # R = 100 * e^(-5 / 24) = 100 * e^(-0.208) = ~81.2%
        node3 = LearningMemoryNode(
            concept_name="cap_theorem",
            last_exposed_at=datetime.utcnow() - timedelta(days=5),
            mastery_level=80.0,
            familiarity_score=80.0,
            confidence_score=80.0,
            pressure_recall_stability=80.0,
            retry_success_rate=1.0,
            exposure_count=5
        )
        r3 = engine.calculate_retention_score(node3)
        assert 78.0 <= r3 <= 84.0

    @pytest.mark.asyncio
    async def test_analyze_memory_strength(self):
        engine = MemoryReinforcementEngine()
        candidate_id = uuid.uuid4()
        
        node = LearningMemoryNode(
            candidate_id=candidate_id,
            concept_name="indexing",
            last_exposed_at=datetime.utcnow() - timedelta(days=10),
            familiarity_score=80.0,
            confidence_score=30.0,
            pressure_recall_stability=20.0,  # low stability under pressure
            retry_success_rate=0.5,
            exposure_count=1
        )
        
        db = MockAsyncSession(nodes=[node])
        updated_nodes = await engine.analyze_memory_strength(candidate_id, db)
        
        assert len(updated_nodes) == 1
        updated_node = updated_nodes[0]
        
        # Verify decay has occurred
        assert updated_node.retention_strength < 100.0
        # Should be classified as fragile since familiarity > 50 and pressure stability < 50
        assert updated_node.is_fragile is True
        # Verify database commit was triggered
        assert db.committed is True

    @pytest.mark.asyncio
    async def test_detect_memory_decay(self):
        engine = MemoryReinforcementEngine()
        candidate_id = uuid.uuid4()
        
        # Expired node (retention should fall below 70)
        node_decayed = LearningMemoryNode(
            candidate_id=candidate_id,
            concept_name="indexing",
            last_exposed_at=datetime.utcnow() - timedelta(days=20),
            mastery_level=30.0,
            retry_success_rate=0.2,
            exposure_count=1
        )
        # Fresh node (retention should be near 100)
        node_fresh = LearningMemoryNode(
            candidate_id=candidate_id,
            concept_name="caching",
            last_exposed_at=datetime.utcnow(),
            mastery_level=90.0,
            retry_success_rate=1.0,
            exposure_count=3
        )
        
        db = MockAsyncSession(nodes=[node_decayed, node_fresh])
        decaying = await engine.detect_memory_decay(candidate_id, db)
        
        assert len(decaying) == 1
        assert decaying[0]["concept_name"] == "indexing"

    @pytest.mark.asyncio
    async def test_detect_recall_fragility(self):
        engine = MemoryReinforcementEngine()
        candidate_id = uuid.uuid4()
        
        node_fragile = LearningMemoryNode(
            candidate_id=candidate_id,
            concept_name="raft",
            familiarity_score=80.0,
            pressure_recall_stability=30.0,  # fragile: high familiarity, low stability
            last_exposed_at=datetime.utcnow()
        )
        
        db = MockAsyncSession(nodes=[node_fragile])
        fragile_concepts = await engine.detect_recall_fragility(candidate_id, db)
        
        assert len(fragile_concepts) == 1
        assert fragile_concepts[0]["concept_name"] == "raft"

    @pytest.mark.asyncio
    async def test_schedule_reinforcement(self):
        engine = MemoryReinforcementEngine()
        candidate_id = uuid.uuid4()
        
        node = LearningMemoryNode(
            candidate_id=candidate_id,
            concept_name="paxos",
            exposure_count=0
        )
        
        db = MockAsyncSession(nodes=[node])
        scheduled = await engine.schedule_reinforcement(candidate_id, "paxos", 7, db)
        
        assert scheduled is not None
        assert scheduled.exposure_count == 1
        assert scheduled.next_review_at is not None
        # Check next review date is roughly 7 days in the future
        diff = scheduled.next_review_at - datetime.utcnow()
        assert 6.9 <= diff.total_seconds() / 86400.0 <= 7.1

    @pytest.mark.asyncio
    async def test_generate_recall_drills(self):
        engine = MemoryReinforcementEngine()
        candidate_id = uuid.uuid4()
        
        node_weak = LearningMemoryNode(
            candidate_id=candidate_id,
            concept_name="two_phase_commit",
            last_exposed_at=datetime.utcnow() - timedelta(days=15),
            mastery_level=30.0,
            retry_success_rate=0.2,
            exposure_count=1
        )
        
        db = MockAsyncSession(nodes=[node_weak])
        drills = await engine.generate_recall_drills(candidate_id, db)
        
        assert len(drills) == 1
        assert drills[0]["concept_name"] == "two_phase_commit"
        assert drills[0]["drill_type"] == "CONCEPT_REINFORCEMENT"

    @pytest.mark.asyncio
    async def test_generate_memory_recovery_exercises(self):
        engine = MemoryReinforcementEngine()
        candidate_id = uuid.uuid4()
        
        node_a = LearningMemoryNode(id=uuid.uuid4(), candidate_id=candidate_id, concept_name="raft", last_exposed_at=datetime.utcnow() - timedelta(days=10), mastery_level=30.0)
        node_b = LearningMemoryNode(id=uuid.uuid4(), candidate_id=candidate_id, concept_name="consensus", last_exposed_at=datetime.utcnow())
        
        edge = LearningMemoryEdge(
            candidate_id=candidate_id,
            source_node_id=node_a.id,
            target_node_id=node_b.id,
            relationship_type="prerequisite"
        )
        
        db = MockAsyncSession(nodes=[node_a, node_b], edges=[edge])
        recovery = await engine.generate_memory_recovery_exercises(candidate_id, db)
        
        assert len(recovery) == 1
        assert recovery[0]["concept_name"] == "raft"
        assert "consensus" in recovery[0]["anchors"]


# ══════════════════════════════════════════════════════════════════════════════
# Communication Intelligence Engine Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestCommunicationIntelligenceEngine:

    def test_analyze_response_structure_star(self):
        engine = CommunicationIntelligenceEngine()
        star_text = "In my last team context, we had a scenario where the backend was slow. The goal was to reduce latency. I built a cache layer and implemented Redis. As a result, we lead to 50% faster query impact metric."
        result = engine.analyze_response_structure(star_text, InterviewPhase.BEHAVIORAL)
        
        assert result["structure_type"] == "STAR"
        assert result["structure_score"] >= 50.0
        assert "situation" in result["components_detected"]
        assert "action" in result["components_detected"]

    def test_analyze_response_structure_prep(self):
        engine = CommunicationIntelligenceEngine()
        prep_text = "My main idea is that sharding works best. The reason is because it distributes load. For example, such as splitting user table. Therefore we conclude that it scales database."
        result = engine.analyze_response_structure(prep_text, InterviewPhase.TECHNICAL_ROUND_1)
        
        assert result["structure_type"] == "PREP"
        assert result["structure_score"] >= 50.0

    def test_detect_rambling(self):
        engine = CommunicationIntelligenceEngine()
        
        concise_text = "We chose PostgreSQL because it supports transactional consistency and relational integrity out-of-the-box."
        res_concise = engine.detect_rambling(concise_text)
        assert res_concise["is_rambling"] is False
        
        rambling_text = "We decided to just use a database. Actually, like, we were thinking of a database. Honestly, the database, like, it was honestly just, you know, we decided to build it. Basically, it was a database database database. And we just built the database and it was basically, like, you know, very database oriented." * 10
        res_ramble = engine.detect_rambling(rambling_text)
        assert res_ramble["is_rambling"] is True
        assert res_ramble["rambling_score"] > 60.0

    def test_detect_fragmentation(self):
        engine = CommunicationIntelligenceEngine()
        
        fragmented_text = "Well... we built the... backend... and then---we deployed it. It was slow. Then it worked. But then..."
        result = engine.detect_fragmentation(fragmented_text)
        
        assert result["fragmentation_score"] >= 40.0
        assert "evidence" in result

    def test_detect_uncertainty_language(self):
        engine = CommunicationIntelligenceEngine()
        
        uncertain_text = "Um, I think maybe we probably built it in Python, er, but I suppose I am not sure."
        result = engine.detect_uncertainty_language(uncertain_text)
        
        assert result["uncertainty_score"] > 20.0
        assert result["filler_count"] >= 2
        assert result["hedge_count"] >= 3

    def test_detect_executive_presence(self):
        engine = CommunicationIntelligenceEngine()
        
        assertive_text = "There are three tradeoffs we weighed. Firstly, consistency. Secondly, latency. We decided to prioritize latency because business impact is core."
        result = engine.detect_executive_presence(assertive_text)
        
        assert result["is_executive_presence_strong"] is True
        assert result["executive_presence_score"] >= 70.0

    def test_analyze_narrative_flow(self):
        engine = CommunicationIntelligenceEngine()
        
        flow_text = "First, we analyzed the query logs. Next, we identified the slow indices. Consequently, we added a composite index."
        result = engine.analyze_narrative_flow(flow_text)
        
        assert result["transition_count"] >= 3
        assert result["narrative_flow_score"] >= 50.0


# ══════════════════════════════════════════════════════════════════════════════
# Strategic Thinking Engine Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestStrategicThinkingEngine:

    def test_analyze_reasoning_path(self):
        engine = StrategicThinkingEngine()
        
        correct_text = "First, let's clarify the scale and constraints of the user base. Decompose this into a cache layer and database layer. However, the tradeoff is latency vs consistency."
        res1 = engine.analyze_reasoning_path(correct_text)
        assert res1["is_order_correct"] is True
        assert res1["reasoning_path_score"] >= 80.0
        
        incorrect_text = "We will break down the microservices architecture layers database layer. Also, we will clarify the constraints and scale."
        res2 = engine.analyze_reasoning_path(incorrect_text)
        assert res2["is_order_correct"] is False
        assert res2["reasoning_path_score"] < res1["reasoning_path_score"]

    def test_detect_missing_clarification(self):
        engine = StrategicThinkingEngine()
        question = "Design a URL shortener at scale."
        
        ans_missing = "I will write a python script with a redis backend database."
        res1 = engine.detect_missing_clarification(question, ans_missing)
        assert res1["missing_clarification"] is True
        
        ans_clarified = "Before starting, I want to clarify the scale, QPS target, and storage constraints."
        res2 = engine.detect_missing_clarification(question, ans_clarified)
        assert res2["missing_clarification"] is False

    def test_detect_tradeoff_thinking(self):
        engine = StrategicThinkingEngine()
        
        text = "This simplifies deployment, but cap theorem states consistency vs availability is the primary tradeoff."
        result = engine.detect_tradeoff_thinking(text)
        
        assert result["has_tradeoff_thinking"] is True
        assert "consistency vs" in result["tradeoff_matches"]

    def test_analyze_problem_decomposition(self):
        engine = StrategicThinkingEngine()
        
        text = "We will decompose this system into microservices, a modular database layer, and a cache layer."
        result = engine.analyze_problem_decomposition(text)
        
        assert result["decomposition_score"] >= 50.0
        assert len(result["decomposition_matches"]) >= 3

    def test_analyze_decision_quality(self):
        engine = StrategicThinkingEngine()
        
        justified_text = "The core constraint is availability, which is our most important priority. We made a tradeoff of latency vs consistency to support it."
        result = engine.analyze_decision_quality(justified_text)
        
        assert result["is_decision_justified"] is True
        assert result["decision_quality_score"] >= 80.0

    def test_detect_assumption_failures(self):
        engine = StrategicThinkingEngine()
        
        bad_text = "We will obviously always just use DynamoDB for this database, it must be the standard choice."
        assert engine.detect_assumption_failures(bad_text) is True
        
        good_text = "Depending on our scalability requirements and availability target, we might choose DynamoDB."
        assert engine.detect_assumption_failures(good_text) is False

    def test_analyze_priority_ordering(self):
        engine = StrategicThinkingEngine()
        
        # Priority mentioned first
        p1 = engine.analyze_priority_ordering("The critical path baseline target is scale, then database schema design.")
        assert p1 == 100.0
        
        # Detail mentioned first (using "first" keyword which is priority)
        p2 = engine.analyze_priority_ordering("Let's define the database indexing columns and API, then list first priorities.")
        assert p2 == 70.0

    def test_get_thinking_pattern_profile(self):
        engine = StrategicThinkingEngine()
        
        # Systems profile (has tradeoff and decomposition)
        sys_text = "Let's decompose this into database layer and cache layer. The tradeoff is consistency vs availability latency."
        assert engine.get_thinking_pattern_profile(sys_text) == "systems"
        
        # Reactive profile (jumps straight to decomposition/implementation, missing clarification)
        reactive_text = "We will build a database layer microservices architecture."
        assert engine.get_thinking_pattern_profile(reactive_text) == "reactive"
        
        # Framework memorizer (high tech boilerplate, no tradeoffs)
        framework_text = "We will deploy NextJS, Redis, and Postgres on Kubernetes, Docker, and AWS."
        assert engine.get_thinking_pattern_profile(framework_text) == "framework_memorizer"
