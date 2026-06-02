"""
Orchestrator Integration with EventBus.

This module connects the deterministic orchestrators to the existing EventBus,
enabling event-driven interview flow while maintaining architectural separation.

Event Flow:
1. TRANSCRIPT_RECEIVED → Trigger evaluation + context assembly (parallel)
2. Evaluation complete → Trigger turn decision
3. Turn decision → Trigger response generation
4. Response generated → Trigger TTS + speculative next generation
5. Phase transitions managed by InterviewOrchestrator
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.voice.events.bus import EventBus
from app.ai.voice.events.event import Event
from app.ai.voice.events.event_types import EventType

from app.ai.orchestrators import (
    InterviewOrchestrator,
    TurnOrchestrator,
    ContextOrchestrator,
    EvaluationOrchestrator,
    ModelOrchestrator,
    RealtimeOrchestrator,
    RoutingPolicy,
    FallbackPolicy,
    EscalationPolicy,
    EvaluationPolicy,
)

from app.ai.orchestrators.contracts.interview_contracts import (
    InterviewConfig,
    InterviewPhase,
    InterviewDomain,
)
from app.ai.orchestrators.contracts.context_contracts import ContextSources, ContextPriority
from app.ai.orchestrators.contracts.model_contracts import ModelTask
from app.ai.orchestrators.state.interview_runtime_state import (
    InterviewRuntimeState,
    CandidateRuntimeState,
    QuestionState,
)

# Import retrieval systems
from app.ai.intelligence.retrieval.retrieval_pipeline import (
    RetrievalPipeline,
    RetrievalQuery,
    RetrievedChunk
)
from app.ai.voice.memory.memory_pipeline import MemoryPipeline
from app.ai.voice.state.interview_state import InterviewState

logger = logging.getLogger(__name__)


class OrchestratorHub:
    """
    Central hub for orchestrator management and event handling.
    
    Responsibilities:
    - Initialize all orchestrators
    - Subscribe to EventBus
    - Route events to appropriate orchestrators
    - Maintain session-specific state
    - Coordinate between orchestrators
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        config: Optional[InterviewConfig] = None,
        db_session_factory: Optional[Any] = None
    ):
        self.event_bus = event_bus
        self.config = config or InterviewConfig(domain=InterviewDomain.MIXED)
        self.db_session_factory = db_session_factory
        
        # Initialize policies
        self.routing_policy = RoutingPolicy.get_default_policy()
        self.fallback_policy = FallbackPolicy()
        self.escalation_policy = EscalationPolicy()
        self.evaluation_policy = EvaluationPolicy()
        
        # Initialize retrieval systems
        self.memory_pipeline = MemoryPipeline()
        self.retrieval_pipeline = RetrievalPipeline(
            embedding_generator=self.memory_pipeline.encoder.encode
        )
        
        # Initialize core orchestrators
        self.interview_orchestrator = InterviewOrchestrator(self.config)
        self.turn_orchestrator = TurnOrchestrator(self.escalation_policy)
        self.context_orchestrator = ContextOrchestrator()
        
        # Initialize cognitive intelligence engines
        from app.ai.intelligence.memory.reinforcement_engine import MemoryReinforcementEngine
        from app.ai.intelligence.communication.communication_engine import CommunicationIntelligenceEngine
        from app.ai.intelligence.strategic.strategic_engine import StrategicThinkingEngine
        
        self.memory_reinforcement_engine = MemoryReinforcementEngine()
        self.communication_intelligence_engine = CommunicationIntelligenceEngine()
        self.strategic_thinking_engine = StrategicThinkingEngine()
        
        # Initialize ModelOrchestrator first (needed by EvaluationOrchestrator)
        self.model_orchestrator = ModelOrchestrator(
            self.routing_policy,
            self.fallback_policy
        )
        
        # Initialize EvaluationOrchestrator with ModelOrchestrator
        self.evaluation_orchestrator = EvaluationOrchestrator(
            self.evaluation_policy,
            enable_cache=True,
            model_orchestrator=self.model_orchestrator
        )
        
        self.realtime_orchestrator = RealtimeOrchestrator()

        # Session state tracking
        self.session_states: Dict[str, InterviewRuntimeState] = {}
        self.candidate_states: Dict[str, CandidateRuntimeState] = {}
        self.current_questions: Dict[str, QuestionState] = {}

        # Per-session SessionOrchestrator instances (session-layer control plane)
        from app.ai.orchestrators.session import SessionOrchestrator
        self._session_orchestrators: Dict[str, SessionOrchestrator] = {}

        # Processing locks (prevent concurrent processing of same session)
        self.processing_locks: Dict[str, asyncio.Lock] = {}

        logger.info("OrchestratorHub initialized with cognitive coaching engines")
    
    def register_event_handlers(self) -> None:
        """
        Register all event handlers with the EventBus.
        
        This wires up the orchestrators to respond to events.
        """
        
        # Transcript received → Start evaluation pipeline
        self.event_bus.subscribe(
            EventType.TRANSCRIPT_RECEIVED,
            self.handle_transcript_received
        )
        
        # Decision created → Generate response
        self.event_bus.subscribe(
            EventType.DECISION_CREATED,
            self.handle_decision_created
        )
        
        # Response generated → Check for hallucinations
        self.event_bus.subscribe(
            EventType.RESPONSE_GENERATED,
            self.handle_response_generated
        )
        
        # Interview events
        self.event_bus.subscribe(
            EventType.QUESTION_ASKED,
            self.handle_question_asked
        )
        
        self.event_bus.subscribe(
            EventType.INTERVIEW_COMPLETED,
            self.handle_interview_completed
        )
        
        # Behavioral signals for escalation
        self.event_bus.subscribe(
            EventType.HESITATION_DETECTED,
            self.handle_hesitation_detected
        )
        
        self.event_bus.subscribe(
            EventType.TOPIC_DRIFT_DETECTED,
            self.handle_topic_drift_detected
        )
        
        logger.info("Event handlers registered with EventBus")
    
    async def handle_transcript_received(self, event: Event) -> None:
        """
        Handle TRANSCRIPT_RECEIVED event.
        
        Process:
        1. Run evaluation (rule-based + LLM in parallel)
        2. Assemble context (in parallel with evaluation)
        3. Make turn decision
        4. Emit DECISION_CREATED event
        """
        
        session_id = event.session_id
        payload = event.payload
        
        # Get lock for this session
        if session_id not in self.processing_locks:
            self.processing_locks[session_id] = asyncio.Lock()
        
        async with self.processing_locks[session_id]:
            try:
                transcript = payload.get("transcript", "")
                turn_number = payload.get("turn_number", 0)
                
                logger.info(
                    f"Processing transcript: session={session_id} turn={turn_number} "
                    f"len={len(transcript)}"
                )
                
                # Get session state
                interview_state = self.session_states.get(session_id)
                candidate_state = self.candidate_states.get(session_id)
                current_question = self.current_questions.get(session_id)
                
                if not interview_state or not candidate_state or not current_question:
                    logger.warning(f"Missing state for session {session_id}, skipping")
                    return
                
                # Run evaluation and context assembly in PARALLEL
                eval_task = self.evaluation_orchestrator.evaluate_answer(
                    question=current_question.question_text,
                    answer_transcript=transcript,
                    phase=interview_state.current_phase,
                    domain=interview_state.domain,
                    context={
                        "session_id": session_id,
                        "turn_number": turn_number
                    }
                )
                
                context_task = self._assemble_context_for_session(
                    session_id,
                    interview_state,
                    transcript,
                    db=None  # TODO: Pass actual db session from VoiceAgent
                )
                
                # Wait for both
                evaluation, context_assembly = await asyncio.gather(
                    eval_task,
                    context_task
                )
                
                # Update candidate state with evaluation
                candidate_state.answer_quality_history.append(evaluation.answer_quality)
                candidate_state.recent_scores.append(evaluation.final_score)
                
                # Keep only recent history
                if len(candidate_state.recent_scores) > 10:
                    candidate_state.recent_scores = candidate_state.recent_scores[-10:]
                
                # Recalculate performance metrics
                candidate_state.current_performance_score = sum(candidate_state.recent_scores) / len(candidate_state.recent_scores)
                
                # Determine performance trend
                if len(candidate_state.recent_scores) >= 3:
                    recent_avg = sum(candidate_state.recent_scores[-3:]) / 3
                    older_avg = sum(candidate_state.recent_scores[-6:-3]) / 3 if len(candidate_state.recent_scores) >= 6 else recent_avg
                    
                    if recent_avg > older_avg + 5:
                        candidate_state.performance_trend = "improving"
                    elif recent_avg < older_avg - 5:
                        candidate_state.performance_trend = "declining"
                    else:
                        candidate_state.performance_trend = "stable"
                
                # ── Session-layer evaluation (runs BEFORE turn decision) ──────────
                from app.ai.orchestrators.session import SessionOrchestrator

                # Lazily create a SessionOrchestrator per session
                if session_id not in self._session_orchestrators:
                    domain_str = interview_state.domain.value if hasattr(interview_state.domain, "value") else str(interview_state.domain)
                    self._session_orchestrators[session_id] = SessionOrchestrator(
                        session_id=session_id,
                        domain=domain_str,
                    )

                session_orch = self._session_orchestrators[session_id]
                session_directive = session_orch.evaluate(
                    transcript=transcript,
                    answer_quality=evaluation.answer_quality.value if hasattr(evaluation.answer_quality, "value") else str(evaluation.answer_quality),
                    performance_score=candidate_state.current_performance_score,
                    frustration_level=getattr(candidate_state, "frustration_level", 0.0),
                    is_topic_fixation_active=False,  # set below after turn decision
                    question_was_ambiguous=False,
                )

                # Propagate pressure-engine mood into interview state
                interview_state.interviewer_mood = session_directive.interviewer_mood

                # Make turn decision
                decision = await self.turn_orchestrator.analyze_turn(
                    session_id=session_id,
                    turn_number=turn_number,
                    transcript=transcript,
                    evaluation=evaluation,
                    current_question=current_question,
                    candidate_state=candidate_state,
                    current_phase=interview_state.current_phase,
                    interviewer_mood=interview_state.interviewer_mood,
                    consecutive_followups=interview_state.consecutive_followups,
                    max_followup_depth=self.config.max_followup_depth
                )

                # Attach session directive to the decision for generation + analytics
                decision.session_directive = session_directive.model_dump()
                
                # Update consecutive followup tracking
                should_reset = await self.turn_orchestrator.should_reset_followup_chain(
                    decision.action,
                    interview_state.consecutive_followups
                )
                
                if should_reset:
                    interview_state.consecutive_followups = 0
                else:
                    from app.ai.orchestrators.contracts.turn_contracts import TurnAction
                    if decision.action in [TurnAction.FOLLOW_UP, TurnAction.PROBE_DEEPER, TurnAction.CLARIFY]:
                        interview_state.consecutive_followups += 1
                        interview_state.followups_asked += 1
                
                # Check if should end phase
                self.interview_orchestrator.state = interview_state
                should_end, end_reason = await self.interview_orchestrator.should_end_phase()
                
                if should_end:
                    logger.info(f"Phase ending: {interview_state.current_phase.value} reason={end_reason}")
                    
                    # Compute next phase
                    next_phase = await self.interview_orchestrator.compute_next_phase(end_reason)
                    
                    # Transition
                    if next_phase != interview_state.current_phase:
                        await self.interview_orchestrator.transition_to_phase(
                            next_phase,
                            end_reason
                        )
                        
                        # Emit phase change event
                        await self.event_bus.emit(Event(
                            type=EventType.TOPIC_CHANGED,
                            session_id=session_id,
                            payload={
                                "from_phase": interview_state.current_phase.value,
                                "to_phase": next_phase.value,
                                "reason": end_reason
                            }
                        ))
                
                # --- COGNITIVE PIPELINE AND MIND STATE PERSISTENCE ---
                import uuid
                from app.db.models.learning_memory import LearningMemoryNode
                from app.db.models.candidate_mind_state import CandidateMindState
                
                candidate_uuid = uuid.UUID(interview_state.candidate_id)
                
                # Fetch DB Session
                db_session = None
                if self.db_session_factory:
                    db_session = self.db_session_factory()
                else:
                    from app.db.session import SessionLocal
                    db_session = SessionLocal()
                
                meta_feedback = []
                thinking_profile = "structured"
                
                async with db_session as db:
                    # Run Communication & Strategic Heuristics
                    comm_analysis = self.communication_intelligence_engine.analyze_response_structure(transcript, interview_state.current_phase)
                    rambling_analysis = self.communication_intelligence_engine.detect_rambling(transcript)
                    uncertainty_analysis = self.communication_intelligence_engine.detect_uncertainty_language(transcript)
                    exec_presence = self.communication_intelligence_engine.detect_executive_presence(transcript)
                    
                    strat_path = self.strategic_thinking_engine.analyze_reasoning_path(transcript)
                    tradeoffs = self.strategic_thinking_engine.detect_tradeoff_thinking(transcript)
                    thinking_profile = self.strategic_thinking_engine.get_thinking_pattern_profile(transcript)
                    
                    # Match Concepts in Transcript for Spaced Repetition Graph
                    KNOWN_CONCEPTS = {
                        "event loop": ("technology", "JS Concurrency"),
                        "cap theorem": ("concept", "Distributed Systems"),
                        "react reconciliation": ("framework", "Frontend Rendering"),
                        "redis": ("technology", "Caching"),
                        "concurrency": ("concept", "Multithreading"),
                        "consistency": ("concept", "Distributed Systems"),
                        "star story": ("communication_pattern", "STAR Method"),
                        "prep structure": ("communication_pattern", "PREP Structure"),
                        "tradeoff analysis": ("system_design_pattern", "Tradeoff Analysis"),
                        "bottleneck identification": ("system_design_pattern", "Bottlenecks"),
                        "requirements clarification": ("system_design_pattern", "Clarification"),
                    }
                    
                    text_lower = transcript.lower()
                    matched_concepts = []
                    for kw, (ctype, _) in KNOWN_CONCEPTS.items():
                        if kw in text_lower or (current_question.question_text and kw in current_question.question_text.lower()):
                            matched_concepts.append((kw, ctype))
                            
                    if hasattr(current_question, "target_topics") and current_question.target_topics:
                        for topic in current_question.target_topics:
                            matched_concepts.append((topic.lower(), "concept"))
                            
                    # Remove duplicates
                    matched_concepts = list(set(matched_concepts))
                    
                    # Update Node states in graph
                    for concept_name, concept_type in matched_concepts:
                        stmt = select(LearningMemoryNode).where(
                            LearningMemoryNode.candidate_id == candidate_uuid,
                            LearningMemoryNode.concept_name == concept_name
                        )
                        node_res = await db.execute(stmt)
                        node = node_res.scalar_one_or_none()
                        
                        latency_sec = (datetime.utcnow() - event.timestamp).total_seconds()
                        if latency_sec < 0.1:
                            latency_sec = 1.5
                            
                        success = 1.0 if evaluation.final_score >= 60.0 else 0.0
                        
                        if not node:
                            node = LearningMemoryNode(
                                candidate_id=candidate_uuid,
                                concept_name=concept_name,
                                concept_type=concept_type,
                                familiarity_score=evaluation.final_score,
                                confidence_score=evaluation.confidence * 100.0,
                                recall_latency=round(latency_sec, 2),
                                retention_strength=80.0,
                                pressure_recall_stability=80.0 if interview_state.current_challenge_level.value == "high" else 50.0,
                                retry_success_rate=success,
                                exposure_count=1,
                                mastery_level=evaluation.final_score,
                                last_exposed_at=datetime.utcnow()
                            )
                            db.add(node)
                        else:
                            node.exposure_count += 1
                            node.last_exposed_at = datetime.utcnow()
                            node.familiarity_score = round(node.familiarity_score * 0.7 + evaluation.final_score * 0.3, 1)
                            node.confidence_score = round(node.confidence_score * 0.7 + evaluation.confidence * 30.0 + 35.0, 1)
                            node.recall_latency = round(node.recall_latency * 0.6 + latency_sec * 0.4, 2)
                            node.retry_success_rate = round(node.retry_success_rate * 0.8 + success * 0.2, 2)
                            if interview_state.current_challenge_level.value == "high":
                                node.pressure_recall_stability = round(node.pressure_recall_stability * 0.7 + evaluation.final_score * 0.3, 1)
                            else:
                                node.pressure_recall_stability = round(node.pressure_recall_stability * 0.9 + evaluation.final_score * 0.1, 1)
                    
                    # Update Node Decays / Strength Compilations
                    await self.memory_reinforcement_engine.analyze_memory_strength(candidate_uuid, db)
                    
                    # Update CandidateMindState
                    mind_stmt = select(CandidateMindState).where(CandidateMindState.candidate_id == candidate_uuid)
                    mind_res = await db.execute(mind_stmt)
                    mind_state = mind_res.scalar_one_or_none()
                    
                    if not mind_state:
                        mind_state = CandidateMindState(
                            candidate_id=candidate_uuid,
                            confidence_level=evaluation.confidence * 100.0,
                            stress_tolerance=50.0,
                            communication_clarity=evaluation.clarity_score,
                            response_structure=comm_analysis["structure_score"],
                            filler_word_control=100.0 - uncertainty_analysis["uncertainty_score"],
                            speaking_consistency=100.0 - rambling_analysis["rambling_score"],
                            executive_presence=exec_presence["executive_presence_score"],
                            memory_recall_strength=50.0,
                            strategic_thinking=strat_path["reasoning_path_score"],
                            cognitive_load_tolerance=50.0,
                            session_count=1,
                            total_turns_analyzed=1
                        )
                        db.add(mind_state)
                    else:
                        mind_state.total_turns_analyzed += 1
                        mind_state.communication_clarity = round(mind_state.communication_clarity * 0.8 + evaluation.clarity_score * 0.2, 1)
                        mind_state.response_structure = round(mind_state.response_structure * 0.8 + comm_analysis["structure_score"] * 0.2, 1)
                        mind_state.filler_word_control = round(mind_state.filler_word_control * 0.8 + (100.0 - uncertainty_analysis["uncertainty_score"]) * 0.2, 1)
                        mind_state.speaking_consistency = round(mind_state.speaking_consistency * 0.8 + (100.0 - rambling_analysis["rambling_score"]) * 0.2, 1)
                        mind_state.executive_presence = round(mind_state.executive_presence * 0.8 + exec_presence["executive_presence_score"] * 0.2, 1)
                        mind_state.strategic_thinking = round(mind_state.strategic_thinking * 0.8 + strat_path["reasoning_path_score"] * 0.2, 1)
                        
                        all_nodes_stmt = select(LearningMemoryNode).where(LearningMemoryNode.candidate_id == candidate_uuid)
                        all_nodes_res = await db.execute(all_nodes_stmt)
                        all_nodes = all_nodes_res.scalars().all()
                        if all_nodes:
                            avg_mastery = sum(n.mastery_level for n in all_nodes) / len(all_nodes)
                            mind_state.memory_recall_strength = round(mind_state.memory_recall_strength * 0.7 + avg_mastery * 0.3, 1)
                    
                    await db.commit()
                    
                    # 4. Formulate Meta-Cognitive Feedback suggestions
                    if thinking_profile == "reactive":
                        meta_feedback.append("Meta-Cognitive Signal: You jumped to implementation before defining constraints.")
                    elif thinking_profile == "systems":
                        meta_feedback.append("Meta-Cognitive Signal: Excellent systems-level thinking. Decomposed issues and compared tradeoffs.")
                    elif thinking_profile == "framework_memorizer":
                        meta_feedback.append("Meta-Cognitive Signal: High boilerplate word usage. Ground explanations in custom tradeoff constraints.")
                    else:
                        meta_feedback.append("Meta-Cognitive Signal: Structured thinking flow. Open with clarifying constraints first.")
                        
                    if rambling_analysis["is_rambling"]:
                        meta_feedback.append("Communication Steering: Pacing is drifting. Re-assert structure and wrap up details.")
                
                # Update event payload
                decision_payload = decision.dict()
                decision_payload["metadata"] = decision_payload.get("metadata", {})
                decision_payload["metadata"]["meta_cognitive_feedback"] = meta_feedback
                decision_payload["metadata"]["thinking_profile"] = thinking_profile
                
                # Emit decision created event
                await self.event_bus.emit(Event(
                    type=EventType.DECISION_CREATED,
                    session_id=session_id,
                    payload={
                        "decision": decision_payload,
                        "evaluation": evaluation.dict(),
                        "context_assembly": context_assembly.dict() if hasattr(context_assembly, 'dict') else {},
                        "turn_number": turn_number
                    },
                    metadata={
                        "processing_time_ms": (datetime.utcnow() - event.timestamp).total_seconds() * 1000
                    }
                ))
                
                logger.info(
                    f"Turn decision: session={session_id} action={decision.action.value} "
                    f"quality={evaluation.answer_quality.value} score={evaluation.final_score:.1f}"
                )
            
            except Exception as e:
                logger.exception(f"Error processing transcript for session {session_id}: {e}")
    
    async def handle_decision_created(self, event: Event) -> None:
        """
        Handle DECISION_CREATED event.
        
        Process:
        1. Get decision from event
        2. Generate response using ModelOrchestrator
        3. Apply hallucination check
        4. Emit RESPONSE_GENERATED event
        """
        
        session_id = event.session_id
        payload = event.payload
        
        try:
            decision_data = payload.get("decision", {})
            context_data = payload.get("context_assembly", {})
            
            # Get session state
            interview_state = self.session_states.get(session_id)
            if not interview_state:
                logger.warning(f"No state for session {session_id}")
                return
            
            # Build prompt based on decision
            from app.ai.orchestrators.contracts.turn_contracts import TurnAction
            action = TurnAction(decision_data.get("action"))
            
            prompt = self._build_generation_prompt(action, decision_data, interview_state)
            
            # Get context string
            context_str = context_data.get("context", "")
            
            # Generate response using ModelOrchestrator
            response = await self.model_orchestrator.generate(
                task=ModelTask.REALTIME_RESPONSE,
                prompt=prompt,
                context=context_str,
                max_tokens=150,
                temperature=0.7,
                timeout_ms=300,
                metadata={
                    "session_id": session_id,
                    "action": action.value,
                    "phase": interview_state.current_phase.value
                }
            )
            
            # Emit response generated event
            await self.event_bus.emit(Event(
                type=EventType.RESPONSE_GENERATED,
                session_id=session_id,
                payload={
                    "text": response.text,
                    "provider": response.provider.value,
                    "model": response.model,
                    "latency_ms": response.latency_ms,
                    "action": action.value
                }
            ))
            
            logger.info(
                f"Response generated: session={session_id} "
                f"latency={response.latency_ms:.0f}ms provider={response.provider.value}"
            )
        
        except Exception as e:
            logger.exception(f"Error generating response for session {session_id}: {e}")
    
    async def handle_response_generated(self, event: Event) -> None:
        """
        Handle RESPONSE_GENERATED event.
        
        Process:
        1. Get generated text
        2. Run hallucination check
        3. If violations detected, regenerate or use fallback
        4. Continue to TTS
        """
        
        session_id = event.session_id
        payload = event.payload
        
        try:
            text = payload.get("text", "")
            
            # Get candidate state for verified profile
            candidate_state = self.candidate_states.get(session_id)
            if not candidate_state:
                return
            
            # Get verified profile from context orchestrator
            verified_profile = self.context_orchestrator.verified_profiles.get(
                candidate_state.candidate_id
            )
            
            if verified_profile:
                # Check for hallucinations
                hallucination_check = await self.context_orchestrator.check_for_hallucinations(
                    text,
                    verified_profile
                )
                
                if not hallucination_check.is_safe:
                    logger.error(
                        f"Hallucination detected in response for session {session_id}: "
                        f"{hallucination_check.violations}"
                    )
                    
                    # TODO: Regenerate or use fallback
                    # For now, just log the violation
        
        except Exception as e:
            logger.exception(f"Error checking hallucinations for session {session_id}: {e}")
    
    async def handle_question_asked(self, event: Event) -> None:
        """
        Handle QUESTION_ASKED event.
        
        Update current question state.
        """
        
        session_id = event.session_id
        payload = event.payload
        
        try:
            question_text = payload.get("question", "")
            question_id = payload.get("question_id", "")
            
            # Update current question
            if session_id in self.session_states:
                interview_state = self.session_states[session_id]
                interview_state.questions_asked += 1
                
                # Create question state
                question_state = QuestionState(
                    question_id=question_id,
                    question_text=question_text,
                    question_type=payload.get("question_type", "initial"),
                    domain=interview_state.domain.value if hasattr(interview_state.domain, "value") else str(interview_state.domain),
                    difficulty=interview_state.current_challenge_level.value if hasattr(interview_state.current_challenge_level, "value") else str(interview_state.current_challenge_level),
                    target_topics=payload.get("target_topics", [])
                )
                
                self.current_questions[session_id] = question_state
                
                logger.info(f"Question asked: session={session_id} id={question_id}")
        
        except Exception as e:
            logger.exception(f"Error handling question asked for session {session_id}: {e}")
    
    async def handle_interview_completed(self, event: Event) -> None:
        """
        Handle INTERVIEW_COMPLETED event.
        
        Cleanup session state.
        """
        
        session_id = event.session_id
        
        try:
            # Get performance stats before cleanup
            if session_id in self.session_states:
                interview_state = self.session_states[session_id]
                
                logger.info(
                    f"Interview completed: session={session_id} "
                    f"questions={interview_state.questions_asked} "
                    f"followups={interview_state.followups_asked} "
                    f"progress={interview_state.interview_progress_percent:.1f}%"
                )
            
            # Cleanup
            self.session_states.pop(session_id, None)
            self.candidate_states.pop(session_id, None)
            self.current_questions.pop(session_id, None)
            self.processing_locks.pop(session_id, None)
        
        except Exception as e:
            logger.exception(f"Error handling interview completion for session {session_id}: {e}")
    
    async def handle_hesitation_detected(self, event: Event) -> None:
        """Handle HESITATION_DETECTED event - may trigger escalation."""
        
        session_id = event.session_id
        
        try:
            candidate_state = self.candidate_states.get(session_id)
            if candidate_state:
                candidate_state.frustration_level = min(1.0, candidate_state.frustration_level + 0.1)
                
                logger.debug(f"Hesitation detected: session={session_id} frustration={candidate_state.frustration_level:.2f}")
        
        except Exception as e:
            logger.exception(f"Error handling hesitation for session {session_id}: {e}")
    
    async def handle_topic_drift_detected(self, event: Event) -> None:
        """Handle TOPIC_DRIFT_DETECTED event - may trigger escalation."""
        
        session_id = event.session_id
        
        try:
            # Track topic drift - could trigger OFF_TOPIC escalation
            logger.warning(f"Topic drift detected: session={session_id}")
        
        except Exception as e:
            logger.exception(f"Error handling topic drift for session {session_id}: {e}")
    
    async def initialize_session(
        self,
        session_id: str,
        candidate_id: str,
        journey_id: Optional[str],
        domain: InterviewDomain,
        resume_text: Optional[str] = None,
        job_description: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> InterviewRuntimeState:
        """
        Initialize orchestrator state for a new session.
        
        This should be called when a new interview session starts.
        
        If journey_id is provided and db session is available,
        resume_text and job_description will be loaded from the database.
        Otherwise, they must be provided as parameters.
        """
        
        try:
            # Load resume and JD from database if journey_id provided
            if journey_id and db and (not resume_text or not job_description):
                resume_text, job_description = await self._load_journey_data(
                    db=db,
                    journey_id=journey_id,
                    candidate_id=candidate_id
                )
            
            # Use empty strings as fallback
            resume_text = resume_text or ""
            job_description = job_description or ""
            
            # Start interview with InterviewOrchestrator
            interview_state = await self.interview_orchestrator.start_interview(
                session_id=session_id,
                candidate_id=candidate_id,
                journey_id=journey_id
            )
            
            # Create candidate state
            candidate_state = CandidateRuntimeState(
                candidate_id=candidate_id,
                session_id=session_id
            )
            
            # Store states
            self.session_states[session_id] = interview_state
            self.candidate_states[session_id] = candidate_state
            
            # Store resume and JD for later context assembly
            interview_state.metadata["resume_text"] = resume_text
            interview_state.metadata["job_description"] = job_description
            
            # Initialize verified profile
            from app.ai.orchestrators.contracts.context_contracts import ContextSources
            
            sources = ContextSources(
                resume_text=resume_text,
                job_description=job_description,
                conversation_history=[],
                knowledge_retrieved=[],
                memory_entries=[]
            )
            
            verified_profile = await self.context_orchestrator._get_verified_profile(
                candidate_id,
                sources
            )
            
            logger.info(
                f"Session initialized: session={session_id} candidate={candidate_id} "
                f"domain={domain.value} phase={interview_state.current_phase.value}"
            )
            
            return interview_state
        
        except Exception as e:
            logger.exception(f"Error initializing session {session_id}: {e}")
            raise
    
    async def _load_journey_data(
        self,
        db: AsyncSession,
        journey_id: str,
        candidate_id: str
    ) -> tuple[str, str]:
        """
        Load resume and job description from InterviewJourney.
        
        Returns:
            Tuple of (resume_text, job_description)
        """
        try:
            from sqlalchemy import select
            from app.db.models.interview_journey import InterviewJourney
            import uuid
            
            # Convert string IDs to UUID
            journey_uuid = uuid.UUID(journey_id)
            candidate_uuid = uuid.UUID(candidate_id)
            
            # Query journey
            result = await db.execute(
                select(InterviewJourney).where(
                    InterviewJourney.id == journey_uuid,
                    InterviewJourney.user_id == candidate_uuid
                )
            )
            
            journey = result.scalar_one_or_none()
            
            if not journey:
                logger.warning(
                    f"Journey not found: journey_id={journey_id} candidate_id={candidate_id}"
                )
                return "", ""
            
            resume_text = journey.resume_text or ""
            job_description = journey.job_description or ""
            
            logger.info(
                f"Loaded journey data: journey_id={journey_id} "
                f"resume_length={len(resume_text)} jd_length={len(job_description)}"
            )
            
            return resume_text, job_description
        
        except Exception as e:
            logger.error(
                f"Error loading journey data: journey_id={journey_id} error={e}",
                exc_info=True
            )
            return "", ""
    
    async def _assemble_context_for_session(
        self,
        session_id: str,
        interview_state: InterviewRuntimeState,
        latest_transcript: str,
        db: Optional[AsyncSession] = None
    ) -> Any:
        """Assemble context for current session state."""
        
        try:
            # Get conversation history (would come from ConversationMemory in real system)
            conversation_history = []
            
            # Get resume and JD from stored metadata
            resume_text = interview_state.metadata.get("resume_text", "")
            job_description = interview_state.metadata.get("job_description", "")
            
            # Retrieve knowledge chunks from knowledge base
            knowledge_chunks = await self._retrieve_knowledge_for_context(
                db=db,
                query_text=latest_transcript,
                domain=interview_state.domain,
                current_phase=interview_state.current_phase,
                session_id=session_id
            )
            
            # Retrieve candidate memories
            memory_entries = await self._retrieve_candidate_memories(
                db=db,
                candidate_id=interview_state.candidate_id,
                query_text=latest_transcript,
                interview_state=interview_state,
                session_id=session_id
            )
            
            # Build sources
            sources = ContextSources(
                resume_text=resume_text,
                job_description=job_description,
                conversation_history=conversation_history,
                knowledge_retrieved=knowledge_chunks,
                memory_entries=memory_entries
            )
            
            # Get constraints
            constraints = await self.interview_orchestrator.get_interview_constraints()
            
            # Assemble context
            assembly = await self.context_orchestrator.assemble_context(
                session_id=session_id,
                candidate_id=interview_state.candidate_id,
                current_phase=interview_state.current_phase,
                domain=interview_state.domain,
                sources=sources,
                constraints=constraints,
                priority=ContextPriority.BALANCED
            )
            
            return assembly
        
        except Exception as e:
            logger.exception(f"Error assembling context for session {session_id}: {e}")
            # Return minimal context
            return {"context": "", "total_tokens": 0}
    
    async def _retrieve_knowledge_for_context(
        self,
        db: Optional[AsyncSession],
        query_text: str,
        domain: InterviewDomain,
        current_phase: InterviewPhase,
        session_id: str
    ) -> List[str]:
        """
        Retrieve knowledge chunks from the knowledge base.
        
        Uses RetrievalPipeline for semantic search with metadata filtering.
        """
        if not db:
            logger.warning(f"No database session available for knowledge retrieval (session: {session_id})")
            return []
        
        if not query_text or len(query_text.strip()) < 5:
            logger.debug(f"Query text too short for retrieval (session: {session_id})")
            return []
        
        try:
            # Build retrieval query
            query = RetrievalQuery(
                query_text=query_text,
                domain=domain.value if domain else None,
                topic=None,  # Could be derived from question context
                top_k=10,
                similarity_threshold=0.7
            )
            
            # Retrieve chunks
            chunks: List[RetrievedChunk] = await self.retrieval_pipeline.retrieve(
                db=db,
                query=query
            )
            
            # Extract text from chunks
            knowledge_texts = [chunk.text for chunk in chunks]
            
            logger.info(
                f"Retrieved {len(knowledge_texts)} knowledge chunks for session {session_id}",
                extra={
                    "domain": domain.value if domain else None,
                    "phase": current_phase.value,
                    "query_length": len(query_text)
                }
            )
            
            return knowledge_texts
        
        except Exception as e:
            logger.error(
                f"Error retrieving knowledge for session {session_id}: {e}",
                exc_info=True
            )
            return []
    
    async def _retrieve_candidate_memories(
        self,
        db: Optional[AsyncSession],
        candidate_id: str,
        query_text: str,
        interview_state: InterviewRuntimeState,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve candidate-specific memories.
        
        Uses MemoryPipeline for decay-corrected, phase-aware memory retrieval.
        """
        if not db:
            logger.warning(f"No database session available for memory retrieval (session: {session_id})")
            return []
        
        if not query_text or len(query_text.strip()) < 5:
            logger.debug(f"Query text too short for memory retrieval (session: {session_id})")
            return []
        
        try:
            # Convert to UUID
            import uuid
            candidate_uuid = uuid.UUID(candidate_id)
            
            # Create InterviewState for memory pipeline
            # (MemoryPipeline expects InterviewState, not InterviewRuntimeState)
            state = InterviewState(
                phase=interview_state.current_phase.value,
                stress_level="moderate",  # Default, could be computed
                domain=interview_state.domain.value if interview_state.domain else "general"
            )
            
            # Retrieve context
            memory_context = await self.memory_pipeline.retrieve_context_for_prompt(
                candidate_id=candidate_uuid,
                query_text=query_text,
                state=state,
                db=db
            )
            
            # Parse memory context into structured entries
            memory_entries = []
            if memory_context:
                # Memory context is formatted as:
                # "Candidate Historical Behavior Context (...):\n- Memory 1\n- Memory 2..."
                lines = memory_context.split('\n')
                for line in lines[1:]:  # Skip header line
                    if line.strip().startswith('-'):
                        memory_entries.append({
                            "content": line.strip()[1:].strip(),
                            "type": "candidate_memory"
                        })
            
            logger.info(
                f"Retrieved {len(memory_entries)} candidate memories for session {session_id}",
                extra={
                    "candidate_id": candidate_id,
                    "phase": interview_state.current_phase.value,
                }
            )
            
            return memory_entries
        
        except Exception as e:
            logger.error(
                f"Error retrieving memories for session {session_id}: {e}",
                exc_info=True
            )
            return []
    
    def _build_generation_prompt(
        self,
        action: Any,
        decision_data: Dict[str, Any],
        interview_state: InterviewRuntimeState
    ) -> str:
        """Build prompt for response generation based on decision."""

        from app.ai.orchestrators.contracts.turn_contracts import TurnAction
        from app.ai.orchestrators.session.session_coverage_planner import SteerAction

        phase_ctx = f"Phase: {interview_state.current_phase.value}"
        mood_ctx = f"Mood: {interview_state.interviewer_mood.value}"

        # ── Session-layer directive takes priority ──────────────────────────────
        session_dir = decision_data.get("session_directive") or {}
        steer = session_dir.get("steer_action", SteerAction.CONTINUE)

        if steer == SteerAction.PIVOT_TO:
            bridge = session_dir.get("bridge_phrase", "")
            target = (session_dir.get("target_area") or "a different area").replace("_", " ")
            instruction = (
                f"{bridge}\n\n"
                f"Ask the candidate a focused question about {target}.\n"
                f"{phase_ctx}\n{mood_ctx}\n\n"
                "Respond as the interviewer in 1-2 sentences. "
                "Lead with the bridge phrase, then ask the question naturally."
            )
            return instruction

        if steer == SteerAction.ZOOM_OUT:
            bridge = session_dir.get("bridge_phrase", "")
            instruction = (
                f"{bridge}\n\n"
                "Invite the candidate to step back and reflect on the broader architectural "
                "picture: tradeoffs made, alternatives considered, or constraints that shaped decisions.\n"
                f"{phase_ctx}\n{mood_ctx}\n\n"
                "Respond as the interviewer in 1-2 sentences."
            )
            return instruction

        if steer == SteerAction.INTRODUCE_CONSTRAINT:
            scenario = session_dir.get("constraint_scenario", "")
            instruction = (
                f"Introduce this scenario to the candidate: \"{scenario}\"\n\n"
                "Frame it as a real-world constraint that just came up. "
                "Ask how they would adapt their current design.\n"
                f"{phase_ctx}\n{mood_ctx}\n\n"
                "Keep it concise — one scenario, one question."
            )
            return instruction

        if steer == SteerAction.PRESSURE_PROBE:
            probe = session_dir.get("adversarial_probe") or ""
            pressure_instr = session_dir.get("pressure_instruction", "")
            instruction = (
                f"{pressure_instr}\n\n"
                + (f"Use this probe: \"{probe}\"\n\n" if probe else "")
                + f"{phase_ctx}\n{mood_ctx}\n\n"
                "Respond as the interviewer in 1-2 sentences. Be direct and specific."
            )
            return instruction

        # ── Recovery support (from pressure engine) ───────────────────────────
        pressure_instr = session_dir.get("pressure_instruction", "")
        is_collapsed = session_dir.get("is_collapsed", False)
        is_stumble = session_dir.get("is_in_stumble", False)
        if is_collapsed or is_stumble:
            instruction = (
                f"{pressure_instr}\n\n"
                f"{phase_ctx}\n{mood_ctx}\n\n"
                "Respond as the interviewer in 1-2 sentences. "
                "Be warm and scaffolding — help the candidate regain their footing."
            )
            return instruction

        # ── BREADTH_REDIRECT (turn-layer keyword fixation guard) ──────────────
        if action == TurnAction.BREADTH_REDIRECT:
            metadata = decision_data.get("metadata") or {}
            redirect_prompt = metadata.get("breadth_redirect_prompt")
            if redirect_prompt:
                return (
                    f"Say to the candidate, verbatim: \"{redirect_prompt}\"\n\n"
                    "Then naturally bridge to a different architectural topic or trade-off.\n\n"
                    f"{phase_ctx}\n{mood_ctx}"
                )
            return (
                "Ask the candidate to step back and describe the broader architectural "
                "decisions they considered beyond the current topic. "
                "Respond as the interviewer in 1-2 sentences."
            )

        # ── Standard turn-layer actions ───────────────────────────────────────
        action_prompts = {
            TurnAction.FOLLOW_UP:          "Ask a follow-up question to explore this topic further.",
            TurnAction.PROBE_DEEPER:       "Probe deeper into the candidate's understanding.",
            TurnAction.CLARIFY:            "Ask the candidate to clarify their response.",
            TurnAction.CHALLENGE_CANDIDATE:"Challenge the candidate's answer or assumptions.",
            TurnAction.GIVE_HINT:          "Provide a helpful hint to guide the candidate.",
            TurnAction.SIMPLIFY_QUESTION:  "Rephrase the question in simpler terms.",
            TurnAction.NEXT_QUESTION:      "Ask the next question in the interview.",
        }

        # Inject pressure instruction if present
        base = action_prompts.get(action, "Continue the interview naturally.")
        if pressure_instr:
            base = f"{pressure_instr}\n\n{base}"

        return f"{base}\n\n{phase_ctx}\n{mood_ctx}\n\nRespond as the interviewer in 1-2 sentences."

    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from all orchestrators."""
        
        return {
            "evaluation": self.evaluation_orchestrator.get_performance_stats(),
            "model": self.model_orchestrator.get_provider_stats(),
            "realtime": self.realtime_orchestrator.get_performance_stats(),
            "active_sessions": len(self.session_states)
        }


# ── Factory Functions ───────────────────────────────────────────────────────


def create_orchestrator_hub(
    event_bus: EventBus,
    config: Optional[InterviewConfig] = None,
    db_session_factory: Optional[Any] = None
) -> OrchestratorHub:
    """
    Factory function to create and initialize OrchestratorHub.
    
    Args:
        event_bus: EventBus instance for event-driven communication
        config: Interview configuration (optional)
        db_session_factory: Factory function to create database sessions (optional)
    
    Usage:
        hub = create_orchestrator_hub(event_bus, db_session_factory=get_db)
        hub.register_event_handlers()
    """
    
    hub = OrchestratorHub(event_bus, config, db_session_factory)
    return hub


def attach_orchestrators_to_agent(
    agent: Any,
    orchestrator_hub: OrchestratorHub
) -> None:
    """
    Attach orchestrators to existing VoiceAgent.
    
    This allows gradual migration from monolithic agent to orchestrated system.
    """
    
    # Attach hub to agent
    agent.orchestrator_hub = orchestrator_hub
    
    logger.info(f"Orchestrators attached to agent for room {agent.room_name}")
