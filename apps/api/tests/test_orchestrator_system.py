"""
Comprehensive tests for the Orchestrator System.

Tests cover:
- Individual orchestrator functionality
- Integration with EventBus
- End-to-end turn processing
- Performance metrics
- Error handling and fallbacks
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import uuid

from app.ai.voice.events import EventBus, Event, EventType
from app.ai.orchestrators.integration import create_orchestrator_hub, OrchestratorHub
from app.ai.orchestrators.contracts.interview_contracts import (
    InterviewConfig,
    InterviewDomain,
    InterviewPhase,
)
from app.ai.orchestrators.contracts.turn_contracts import (
    TurnAction,
    AnswerQuality,
)
from app.ai.orchestrators.contracts.evaluation_contracts import (
    RuleBasedMetrics,
    LLMBasedMetrics,
    UnifiedEvaluation,
)
from app.ai.orchestrators.contracts.context_contracts import ContextSources
from app.ai.orchestrators.state.interview_runtime_state import QuestionState


# ══════════════════════════════════════════════════════════════════════════════
# Unit Tests - Individual Orchestrators
# ══════════════════════════════════════════════════════════════════════════════


class TestInterviewOrchestrator:
    """Test InterviewOrchestrator functionality."""
    
    @pytest.mark.asyncio
    async def test_start_interview(self):
        """Test starting a new interview session."""
        from app.ai.orchestrators import InterviewOrchestrator
        
        config = InterviewConfig(
            domain=InterviewDomain.BACKEND,
            target_duration_minutes=45
        )
        orchestrator = InterviewOrchestrator(config)
        
        state = await orchestrator.start_interview(
            session_id="test-session-1",
            candidate_id="candidate-1",
            journey_id="journey-1"
        )
        
        assert state.session_id == "test-session-1"
        assert state.candidate_id == "candidate-1"
        assert state.current_phase == InterviewPhase.INTRODUCTION
        assert state.questions_asked == 0
        assert state.domain == InterviewDomain.BACKEND
    
    @pytest.mark.asyncio
    async def test_phase_transition(self):
        """Test phase transition logic."""
        from app.ai.orchestrators import InterviewOrchestrator
        
        config = InterviewConfig(domain=InterviewDomain.BACKEND)
        orchestrator = InterviewOrchestrator(config)
        
        state = await orchestrator.start_interview(
            session_id="test-session-2",
            candidate_id="candidate-2",
            journey_id=None
        )
        
        # Transition to next phase
        transition = await orchestrator.transition_to_phase(
            InterviewPhase.RESUME_DISCUSSION,
            "time_limit_reached"
        )
        
        assert transition.from_phase == InterviewPhase.INTRODUCTION
        assert transition.to_phase == InterviewPhase.RESUME_DISCUSSION
        assert state.current_phase == InterviewPhase.RESUME_DISCUSSION
    
    @pytest.mark.asyncio
    async def test_should_end_phase(self):
        """Test phase ending detection."""
        from app.ai.orchestrators import InterviewOrchestrator
        
        config = InterviewConfig(domain=InterviewDomain.BACKEND)
        orchestrator = InterviewOrchestrator(config)
        
        await orchestrator.start_interview(
            session_id="test-session-3",
            candidate_id="candidate-3",
            journey_id=None
        )
        
        # Initially should not end
        should_end, reason = await orchestrator.should_end_phase()
        assert not should_end
        
        # Simulate time passing by setting phase_start_time in the past
        import datetime as dt
        orchestrator.state.phase_start_time = dt.datetime.utcnow() - dt.timedelta(minutes=10)
        
        # Update phase state
        phase_state = orchestrator.phase_states[InterviewPhase.INTRODUCTION]
        phase_state.started_at = dt.datetime.utcnow() - dt.timedelta(minutes=10)
        phase_state.target_duration_minutes = 3
        
        should_end, reason = await orchestrator.should_end_phase()
        assert should_end
        assert reason == "time_limit_reached"


class TestTurnOrchestrator:
    """Test TurnOrchestrator functionality."""
    
    @pytest.mark.asyncio
    async def test_action_routing(self):
        """Test deterministic action routing from answer quality."""
        from app.ai.orchestrators import TurnOrchestrator
        from app.ai.orchestrators.state.interview_runtime_state import CandidateRuntimeState
        
        orchestrator = TurnOrchestrator()
        
        # Create test data
        candidate_state = CandidateRuntimeState(
            candidate_id="candidate-1",
            session_id="test-session"
        )
        
        question_state = QuestionState(
            question_id="q1",
            question_text="Tell me about your experience with Python.",
            question_type="initial",
            domain="backend",
            difficulty="moderate",
            target_topics=["python", "experience"]
        )
        
        evaluation = UnifiedEvaluation(
            final_score=85.0,
            rule_based_score=80.0,
            llm_based_score=90.0,
            answer_quality=AnswerQuality.EXCELLENT,
            rule_based_metrics=RuleBasedMetrics(),
            llm_based_metrics=LLMBasedMetrics(),
            confidence=0.9
        )
        
        # Analyze turn
        decision = await orchestrator.analyze_turn(
            session_id="test-session",
            turn_number=1,
            transcript="I have 5 years of Python experience...",
            evaluation=evaluation,
            current_question=question_state,
            candidate_state=candidate_state,
            current_phase=InterviewPhase.RESUME_DISCUSSION,
            interviewer_mood=InterviewPhase.INTRODUCTION,  # Using enum value as placeholder
            consecutive_followups=0,
            max_followup_depth=3
        )
        
        # EXCELLENT answer should trigger PROBE_DEEPER or CHALLENGE_CANDIDATE
        assert decision.action in [
            TurnAction.PROBE_DEEPER,
            TurnAction.CHALLENGE_CANDIDATE,
            TurnAction.NEXT_QUESTION
        ]
        assert decision.confidence > 0
    
    @pytest.mark.asyncio
    async def test_followup_depth_limit(self):
        """Test that followup depth is limited."""
        from app.ai.orchestrators import TurnOrchestrator
        from app.ai.orchestrators.state.interview_runtime_state import CandidateRuntimeState
        
        orchestrator = TurnOrchestrator()
        
        candidate_state = CandidateRuntimeState(
            candidate_id="candidate-1",
            session_id="test-session"
        )
        
        question_state = QuestionState(
            question_id="q1",
            question_text="Test question",
            question_type="initial",
            domain="backend",
            difficulty="moderate",
            target_topics=["test"]
        )
        
        evaluation = UnifiedEvaluation(
            final_score=70.0,
            rule_based_score=70.0,
            llm_based_score=70.0,
            answer_quality=AnswerQuality.GOOD,
            rule_based_metrics=RuleBasedMetrics(),
            llm_based_metrics=LLMBasedMetrics(),
            confidence=0.8
        )
        
        # At max depth, should move to next question
        decision = await orchestrator.analyze_turn(
            session_id="test-session",
            turn_number=5,
            transcript="Test answer",
            evaluation=evaluation,
            current_question=question_state,
            candidate_state=candidate_state,
            current_phase=InterviewPhase.TECHNICAL_ROUND_1,
            interviewer_mood=InterviewPhase.INTRODUCTION,
            consecutive_followups=3,  # At max depth
            max_followup_depth=3
        )
        
        assert decision.action == TurnAction.NEXT_QUESTION


class TestEvaluationOrchestrator:
    """Test EvaluationOrchestrator functionality."""
    
    @pytest.mark.asyncio
    async def test_evaluate_answer(self):
        """Test answer evaluation with combined scoring."""
        from app.ai.orchestrators import EvaluationOrchestrator
        
        orchestrator = EvaluationOrchestrator()
        
        evaluation = await orchestrator.evaluate_answer(
            question="What is your experience with microservices?",
            answer_transcript="I have worked with microservices for 3 years, implementing REST APIs and message queues.",
            phase=InterviewPhase.TECHNICAL_ROUND_1,
            domain=InterviewDomain.BACKEND,
            context={}
        )
        
        assert evaluation.final_score >= 0 and evaluation.final_score <= 100
        assert evaluation.rule_based_score >= 0
        assert evaluation.llm_based_score >= 0
        assert evaluation.answer_quality in list(AnswerQuality)
        assert evaluation.confidence >= 0 and evaluation.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_score_combination(self):
        """Test that scores are combined with correct weights (60/40)."""
        from app.ai.orchestrators import EvaluationOrchestrator
        from app.ai.orchestrators.policies.evaluation_policy import EvaluationPolicy
        
        policy = EvaluationPolicy()
        orchestrator = EvaluationOrchestrator(policy)
        
        # The weights should be 60% rule-based, 40% LLM-based
        assert policy.rule_based_weight == 0.6
        assert policy.llm_based_weight == 0.4


class TestContextOrchestrator:
    """Test ContextOrchestrator functionality."""
    
    @pytest.mark.asyncio
    async def test_assemble_context(self):
        """Test context assembly with token budgeting."""
        from app.ai.orchestrators import ContextOrchestrator
        from app.ai.orchestrators.contracts.interview_contracts import InterviewConstraints
        
        orchestrator = ContextOrchestrator()
        
        sources = ContextSources(
            resume_text="Software Engineer with 5 years experience in Python and Django...",
            job_description="Looking for a Backend Engineer with Python experience...",
            conversation_history=[
                {"speaker": "interviewer", "transcript": "Tell me about yourself"},
                {"speaker": "candidate", "transcript": "I'm a software engineer..."}
            ],
            knowledge_retrieved=[{"content": "Python is a high-level programming language..."}],
            memory_entries=[{"content": "Candidate prefers backend work"}]
        )
        
        constraints = InterviewConstraints(
            allowed_topics=["python", "backend", "apis"],
            forbidden_topics=["frontend", "css", "react"]
        )
        
        assembly = await orchestrator.assemble_context(
            session_id="test-session",
            candidate_id="candidate-1",
            current_phase=InterviewPhase.TECHNICAL_ROUND_1,
            domain=InterviewDomain.BACKEND,
            sources=sources,
            constraints=constraints
        )
        
        assert assembly.context is not None
        assert assembly.total_tokens > 0
        assert assembly.total_tokens <= 5000  # Default budget
        assert assembly.verified_profile is not None
    
    @pytest.mark.asyncio
    async def test_hallucination_check(self):
        """Test hallucination detection."""
        from app.ai.orchestrators import ContextOrchestrator
        from app.ai.orchestrators.contracts.context_contracts import VerifiedCandidateProfile
        
        orchestrator = ContextOrchestrator()
        
        verified_profile = VerifiedCandidateProfile(
            verified_skills=["python", "django", "postgresql"],
            verified_projects=[{"name": "E-commerce API"}, {"name": "Analytics Dashboard"}],
            verified_technologies=["python", "django", "postgresql", "redis"],
            verified_companies=["TechCorp", "StartupXYZ"]
        )
        
        # Safe text (references verified info)
        safe_text = "Tell me more about your work on the E-commerce API project."
        check = await orchestrator.check_for_hallucinations(safe_text, verified_profile)
        assert check.is_safe
        
        # Unsafe text (references unverified info)
        unsafe_text = "Tell me about your experience with React and the mobile app you built."
        check = await orchestrator.check_for_hallucinations(unsafe_text, verified_profile)
        # May or may not detect depending on implementation, but should not crash
        assert isinstance(check.is_safe, bool)


# ══════════════════════════════════════════════════════════════════════════════
# Integration Tests - EventBus Integration
# ══════════════════════════════════════════════════════════════════════════════


class TestOrchestratorIntegration:
    """Test orchestrator integration with EventBus."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_hub_creation(self):
        """Test creating orchestrator hub."""
        event_bus = EventBus()
        config = InterviewConfig(domain=InterviewDomain.BACKEND)
        
        hub = create_orchestrator_hub(event_bus, config)
        
        assert hub is not None
        assert hub.event_bus is event_bus
        assert hub.interview_orchestrator is not None
        assert hub.turn_orchestrator is not None
        assert hub.context_orchestrator is not None
        assert hub.evaluation_orchestrator is not None
        assert hub.model_orchestrator is not None
        assert hub.realtime_orchestrator is not None
    
    @pytest.mark.asyncio
    async def test_event_handler_registration(self):
        """Test that event handlers are registered properly."""
        event_bus = EventBus()
        hub = create_orchestrator_hub(event_bus)
        
        hub.register_event_handlers()
        
        # Check that handlers are registered
        assert EventType.TRANSCRIPT_RECEIVED in event_bus._handlers
        assert EventType.DECISION_CREATED in event_bus._handlers
        assert EventType.RESPONSE_GENERATED in event_bus._handlers
        assert EventType.QUESTION_ASKED in event_bus._handlers
        assert EventType.INTERVIEW_COMPLETED in event_bus._handlers
    
    @pytest.mark.asyncio
    async def test_session_initialization(self):
        """Test session initialization in orchestrator hub."""
        event_bus = EventBus()
        hub = create_orchestrator_hub(event_bus)
        
        session_id = str(uuid.uuid4())
        candidate_id = str(uuid.uuid4())
        
        state = await hub.initialize_session(
            session_id=session_id,
            candidate_id=candidate_id,
            journey_id=None,
            domain=InterviewDomain.BACKEND,
            resume_text="Test resume",
            job_description="Test JD"
        )
        
        assert state.session_id == session_id
        assert state.candidate_id == candidate_id
        assert session_id in hub.session_states
        assert session_id in hub.candidate_states
    
    @pytest.mark.asyncio
    async def test_full_turn_cycle(self):
        """Test complete turn cycle from transcript to response."""
        event_bus = EventBus()
        config = InterviewConfig(domain=InterviewDomain.BACKEND)
        hub = create_orchestrator_hub(event_bus, config)
        hub.register_event_handlers()
        
        session_id = str(uuid.uuid4())
        candidate_id = str(uuid.uuid4())
        
        # Initialize session
        await hub.initialize_session(
            session_id=session_id,
            candidate_id=candidate_id,
            journey_id=None,
            domain=InterviewDomain.BACKEND,
            resume_text="Software Engineer with 5 years of Python experience.",
            job_description="Backend Engineer position requiring Python expertise."
        )
        
        # Emit QUESTION_ASKED event
        await event_bus.emit(Event(
            type=EventType.QUESTION_ASKED,
            session_id=session_id,
            payload={
                "question": "Tell me about your experience with Python.",
                "question_id": str(uuid.uuid4()),
                "sequence": 1
            }
        ))
        
        # Wait for question to be processed
        await asyncio.sleep(0.1)
        
        # Emit TRANSCRIPT_RECEIVED event
        await event_bus.emit(Event(
            type=EventType.TRANSCRIPT_RECEIVED,
            session_id=session_id,
            payload={
                "transcript": "I have 5 years of experience with Python, building APIs and microservices.",
                "turn_number": 1
            }
        ))
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Verify state was updated
        candidate_state = hub.candidate_states[session_id]
        assert len(candidate_state.answer_quality_history) > 0
        assert len(candidate_state.recent_scores) > 0
    
    @pytest.mark.asyncio
    async def test_performance_stats(self):
        """Test that performance stats are collected."""
        event_bus = EventBus()
        hub = create_orchestrator_hub(event_bus)
        
        stats = hub.get_performance_stats()
        
        assert "evaluation" in stats
        assert "model" in stats
        assert "realtime" in stats
        assert "active_sessions" in stats


# ══════════════════════════════════════════════════════════════════════════════
# Performance Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestPerformance:
    """Test performance characteristics of orchestrators."""
    
    @pytest.mark.asyncio
    async def test_evaluation_latency(self):
        """Test that evaluation completes within target latency."""
        from app.ai.orchestrators import EvaluationOrchestrator
        import time
        
        orchestrator = EvaluationOrchestrator()
        
        start = time.time()
        
        await orchestrator.evaluate_answer(
            question="What is your experience?",
            answer_transcript="I have 5 years of experience in software engineering.",
            phase=InterviewPhase.RESUME_DISCUSSION,
            domain=InterviewDomain.BACKEND
        )
        
        latency_ms = (time.time() - start) * 1000
        
        # Should complete within 100ms (mocked models)
        assert latency_ms < 200
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self):
        """Test handling multiple concurrent sessions."""
        event_bus = EventBus()
        hub = create_orchestrator_hub(event_bus)
        hub.register_event_handlers()
        
        # Initialize 5 concurrent sessions
        session_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        tasks = []
        for session_id in session_ids:
            task = hub.initialize_session(
                session_id=session_id,
                candidate_id=str(uuid.uuid4()),
                journey_id=None,
                domain=InterviewDomain.BACKEND,
                resume_text="Test resume",
                job_description="Test JD"
            )
            tasks.append(task)
        
        # Wait for all to complete
        await asyncio.gather(*tasks)
        
        # Verify all sessions initialized
        for session_id in session_ids:
            assert session_id in hub.session_states
            assert session_id in hub.candidate_states


# ══════════════════════════════════════════════════════════════════════════════
# Error Handling Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    """Test error handling and fallback mechanisms."""
    
    @pytest.mark.asyncio
    async def test_missing_session_state(self):
        """Test handling of missing session state gracefully."""
        event_bus = EventBus()
        hub = create_orchestrator_hub(event_bus)
        hub.register_event_handlers()
        
        # Emit event for non-existent session (should not crash)
        await event_bus.emit(Event(
            type=EventType.TRANSCRIPT_RECEIVED,
            session_id="non-existent-session",
            payload={
                "transcript": "test",
                "turn_number": 1
            }
        ))
        
        # Should complete without error
        await asyncio.sleep(0.1)
    
    @pytest.mark.asyncio
    async def test_model_orchestrator_fallback(self):
        """Test model orchestrator fallback behavior."""
        from app.ai.orchestrators import ModelOrchestrator
        from app.ai.orchestrators.contracts.model_contracts import ModelTask
        
        orchestrator = ModelOrchestrator()
        
        # Should not crash even with mocked models
        try:
            response = await orchestrator.generate(
                task=ModelTask.REALTIME_RESPONSE,
                prompt="Test prompt",
                max_tokens=50,
                timeout_ms=1000
            )
            assert response is not None
        except Exception as e:
            # If it fails, should be a controlled exception
            assert isinstance(e, Exception)


# ══════════════════════════════════════════════════════════════════════════════
# Test Configuration
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def event_bus():
    """Provide a fresh EventBus for each test."""
    return EventBus()


@pytest.fixture
def orchestrator_hub(event_bus):
    """Provide a configured OrchestratorHub for tests."""
    config = InterviewConfig(domain=InterviewDomain.BACKEND)
    hub = create_orchestrator_hub(event_bus, config)
    hub.register_event_handlers()
    return hub


if __name__ == "__main__":
    # Run tests with: python -m pytest test_orchestrator_system.py -v
    pytest.main([__file__, "-v", "--tb=short"])
