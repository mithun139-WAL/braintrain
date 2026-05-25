"""
Realtime Orchestrator - Manages speculative generation and parallel execution.

This orchestrator is critical for achieving <700ms latency by:
1. Running STT, evaluation, and generation in parallel where possible
2. Speculative pre-generation of likely follow-ups
3. Pipeline optimization
4. Latency budget enforcement
"""
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio

from pydantic import BaseModel, Field

from app.ai.orchestrators.contracts.realtime_contracts import (
    RealtimeLatencyTarget,
    PipelineStage,
    LatencyBreakdown,
    SpeculativeGeneration
)
from app.ai.orchestrators.contracts.model_contracts import ModelTask
from app.ai.orchestrators.contracts.turn_contracts import TurnAction, TurnDecision

logger = logging.getLogger(__name__)


class RealtimeOrchestrator:
    """
    Orchestrator for realtime interview flow with latency optimization.
    
    Key responsibilities:
    - Parallel execution of independent stages
    - Speculative generation for likely paths
    - Latency tracking and budget enforcement
    - Pipeline optimization
    - Adaptive degradation when latency threatened
    """
    
    def __init__(
        self,
        latency_target: Optional[RealtimeLatencyTarget] = None
    ):
        self.latency_target = latency_target or RealtimeLatencyTarget()
        
        # Performance tracking
        self.stage_latencies: Dict[str, List[float]] = {}
        self.total_latencies: List[float] = []
        self.budget_violations: int = 0
        self.total_turns: int = 0
        
        # Speculative cache
        self.speculative_cache: Dict[str, SpeculativeGeneration] = {}
        self.speculative_hits: int = 0
        self.speculative_misses: int = 0
        
        logger.info(
            f"Initialized RealtimeOrchestrator with {self.latency_target.total_target_ms}ms target"
        )
    
    async def process_turn(
        self,
        audio_input: bytes,
        context: Dict[str, Any],
        orchestrators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a complete interview turn with latency optimization.
        
        Pipeline stages:
        1. STT (Speech-to-Text) - 150ms budget
        2. Analysis (Evaluation) - 50ms budget
        3. Decision (Turn logic) - 50ms budget
        4. Context Assembly - 100ms budget
        5. Generation (LLM) - 250ms budget
        6. TTS (Text-to-Speech) - 100ms budget
        
        Total target: 700ms
        
        Optimizations:
        - Run stages in parallel where possible
        - Use speculative generation
        - Adaptive quality degradation
        """
        
        turn_start = datetime.utcnow()
        latency_breakdown = LatencyBreakdown()
        
        # Check speculative cache first
        cached_response = await self._check_speculative_cache(context)
        if cached_response:
            logger.info("Speculative cache HIT - skipping pipeline")
            self.speculative_hits += 1
            
            # Still need TTS
            tts_start = datetime.utcnow()
            audio_output = await orchestrators["tts"].synthesize(cached_response["text"])
            tts_ms = (datetime.utcnow() - tts_start).total_seconds() * 1000
            latency_breakdown.tts_ms = tts_ms
            latency_breakdown.total_ms = tts_ms
            
            return {
                "text": cached_response["text"],
                "audio": audio_output,
                "latency": latency_breakdown,
                "from_cache": True
            }
        
        self.speculative_misses += 1
        
        # Stage 1: STT (Speech-to-Text)
        stt_start = datetime.utcnow()
        transcript = await self._run_stt(
            audio_input,
            orchestrators["stt"],
            self.latency_target.stt_ms
        )
        stt_ms = (datetime.utcnow() - stt_start).total_seconds() * 1000
        latency_breakdown.stt_ms = stt_ms
        
        if stt_ms > self.latency_target.stt_ms:
            logger.warning(f"STT budget exceeded: {stt_ms:.0f}ms > {self.latency_target.stt_ms}ms")
        
        # Stage 2 & 3: Run Analysis and Context Assembly in PARALLEL
        parallel_start = datetime.utcnow()
        
        eval_task = self._run_evaluation(
            transcript,
            context,
            orchestrators["evaluation"],
            self.latency_target.analysis_ms
        )
        
        context_task = self._assemble_context(
            transcript,
            context,
            orchestrators["context"],
            self.latency_target.context_assembly_ms
        )
        
        # Wait for both
        evaluation, assembled_context = await asyncio.gather(eval_task, context_task)
        
        analysis_ms = (datetime.utcnow() - parallel_start).total_seconds() * 1000
        latency_breakdown.analysis_ms = min(analysis_ms, stt_ms + self.latency_target.analysis_ms)
        latency_breakdown.context_assembly_ms = min(analysis_ms, stt_ms + self.latency_target.context_assembly_ms)
        
        # Stage 4: Decision
        decision_start = datetime.utcnow()
        decision = await self._make_decision(
            evaluation,
            context,
            orchestrators["turn"],
            self.latency_target.decision_ms
        )
        decision_ms = (datetime.utcnow() - decision_start).total_seconds() * 1000
        latency_breakdown.decision_ms = decision_ms
        
        # Calculate remaining budget for generation
        elapsed_ms = (datetime.utcnow() - turn_start).total_seconds() * 1000
        remaining_budget = self.latency_target.total_target_ms - elapsed_ms - self.latency_target.tts_ms
        
        if remaining_budget < 100:
            logger.warning(f"Low generation budget: {remaining_budget:.0f}ms")
            # Use degraded mode or cached response
            remaining_budget = max(100, remaining_budget)
        
        # Stage 5: Generation
        generation_start = datetime.utcnow()
        generated_text = await self._generate_response(
            decision,
            assembled_context,
            orchestrators["model"],
            int(remaining_budget)
        )
        generation_ms = (datetime.utcnow() - generation_start).total_seconds() * 1000
        latency_breakdown.generation_ms = generation_ms
        
        # Stage 6: TTS (in parallel with speculative next generation)
        tts_start = datetime.utcnow()
        
        tts_task = orchestrators["tts"].synthesize(generated_text)
        speculative_task = self._generate_speculative(
            decision,
            context,
            orchestrators
        )
        
        audio_output, _ = await asyncio.gather(tts_task, speculative_task)
        
        tts_ms = (datetime.utcnow() - tts_start).total_seconds() * 1000
        latency_breakdown.tts_ms = tts_ms
        
        # Calculate total
        total_ms = (datetime.utcnow() - turn_start).total_seconds() * 1000
        latency_breakdown.total_ms = total_ms
        
        # Track performance
        self._record_latency(latency_breakdown)
        
        # Check budget violation
        if total_ms > self.latency_target.total_target_ms:
            self.budget_violations += 1
            logger.warning(
                f"Latency budget violated: {total_ms:.0f}ms > {self.latency_target.total_target_ms}ms "
                f"(violations: {self.budget_violations}/{self.total_turns})"
            )
        
        logger.info(
            f"Turn complete: {total_ms:.0f}ms "
            f"(STT={stt_ms:.0f} Eval={latency_breakdown.analysis_ms:.0f} "
            f"Gen={generation_ms:.0f} TTS={tts_ms:.0f})"
        )
        
        return {
            "text": generated_text,
            "audio": audio_output,
            "transcript": transcript,
            "evaluation": evaluation,
            "decision": decision,
            "latency": latency_breakdown,
            "from_cache": False
        }
    
    async def _run_stt(
        self,
        audio: bytes,
        stt_client: Any,
        budget_ms: int
    ) -> str:
        """Run speech-to-text with timeout."""
        
        try:
            transcript = await asyncio.wait_for(
                stt_client.transcribe(audio),
                timeout=budget_ms / 1000
            )
            return transcript
        except asyncio.TimeoutError:
            logger.error(f"STT timeout after {budget_ms}ms")
            raise
    
    async def _run_evaluation(
        self,
        transcript: str,
        context: Dict[str, Any],
        eval_orchestrator: Any,
        budget_ms: int
    ) -> Any:
        """Run evaluation with timeout."""
        
        try:
            evaluation = await asyncio.wait_for(
                eval_orchestrator.evaluate_answer(
                    question=context.get("current_question", ""),
                    answer_transcript=transcript,
                    phase=context.get("current_phase"),
                    domain=context.get("domain"),
                    context=context
                ),
                timeout=budget_ms / 1000
            )
            return evaluation
        except asyncio.TimeoutError:
            logger.error(f"Evaluation timeout after {budget_ms}ms")
            # Return degraded evaluation
            from app.ai.orchestrators.contracts.evaluation_contracts import UnifiedEvaluation, RuleBasedMetrics, LLMBasedMetrics
            from app.ai.orchestrators.contracts.turn_contracts import AnswerQuality
            
            return UnifiedEvaluation(
                final_score=60.0,
                rule_based_score=60.0,
                llm_based_score=60.0,
                answer_quality=AnswerQuality.SATISFACTORY,
                rule_based_metrics=RuleBasedMetrics(),
                llm_based_metrics=LLMBasedMetrics(),
                confidence=0.5
            )
    
    async def _assemble_context(
        self,
        transcript: str,
        context: Dict[str, Any],
        context_orchestrator: Any,
        budget_ms: int
    ) -> Any:
        """Assemble context with timeout."""
        
        try:
            from app.ai.orchestrators.contracts.context_contracts import ContextSources, ContextPriority
            
            sources = ContextSources(
                resume_text=context.get("resume_text", ""),
                job_description=context.get("job_description", ""),
                conversation_history=context.get("conversation_history", []),
                knowledge_retrieved=context.get("knowledge_chunks", []),
                memory_entries=context.get("memory_entries", [])
            )
            
            assembly = await asyncio.wait_for(
                context_orchestrator.assemble_context(
                    session_id=context.get("session_id", ""),
                    candidate_id=context.get("candidate_id", ""),
                    current_phase=context.get("current_phase"),
                    domain=context.get("domain"),
                    sources=sources,
                    constraints=context.get("constraints"),
                    priority=ContextPriority.BALANCED
                ),
                timeout=budget_ms / 1000
            )
            return assembly
        except asyncio.TimeoutError:
            logger.error(f"Context assembly timeout after {budget_ms}ms")
            # Return minimal context
            return {"context": "", "total_tokens": 0}
    
    async def _make_decision(
        self,
        evaluation: Any,
        context: Dict[str, Any],
        turn_orchestrator: Any,
        budget_ms: int
    ) -> TurnDecision:
        """Make turn decision with timeout."""
        
        try:
            decision = await asyncio.wait_for(
                turn_orchestrator.analyze_turn(
                    session_id=context.get("session_id", ""),
                    turn_number=context.get("turn_number", 0),
                    transcript=context.get("last_transcript", ""),
                    evaluation=evaluation,
                    current_question=context.get("current_question_state"),
                    candidate_state=context.get("candidate_state"),
                    current_phase=context.get("current_phase"),
                    interviewer_mood=context.get("interviewer_mood"),
                    consecutive_followups=context.get("consecutive_followups", 0),
                    max_followup_depth=context.get("max_followup_depth", 3)
                ),
                timeout=budget_ms / 1000
            )
            return decision
        except asyncio.TimeoutError:
            logger.error(f"Decision timeout after {budget_ms}ms")
            # Return safe default decision
            return TurnDecision(
                action=TurnAction.NEXT_QUESTION,
                reason="timeout_fallback",
                confidence=0.5
            )
    
    async def _generate_response(
        self,
        decision: TurnDecision,
        context: Any,
        model_orchestrator: Any,
        budget_ms: int
    ) -> str:
        """Generate response with timeout."""
        
        try:
            # Build prompt based on decision
            prompt = self._build_generation_prompt(decision, context)
            
            response = await asyncio.wait_for(
                model_orchestrator.generate(
                    task=ModelTask.REALTIME_RESPONSE,
                    prompt=prompt,
                    context=getattr(context, 'context', ''),
                    max_tokens=150,
                    temperature=0.7,
                    timeout_ms=budget_ms
                ),
                timeout=budget_ms / 1000
            )
            
            return response.text
        except asyncio.TimeoutError:
            logger.error(f"Generation timeout after {budget_ms}ms")
            # Use rule-based fallback
            return self._get_fallback_response(decision)
    
    def _build_generation_prompt(self, decision: TurnDecision, context: Any) -> str:
        """Build generation prompt based on decision."""

        from app.ai.orchestrators.session.session_coverage_planner import SteerAction

        # ── Session-layer directive takes priority ──────────────────────────────
        session_dir = (decision.session_directive or {})
        steer = session_dir.get("steer_action", SteerAction.CONTINUE)

        if steer == SteerAction.PIVOT_TO:
            bridge = session_dir.get("bridge_phrase", "")
            target = (session_dir.get("target_area") or "a different area").replace("_", " ")
            return (
                f"{bridge}\n\n"
                f"Ask the candidate a focused question about {target}. "
                "Respond as the interviewer in 1-2 sentences. "
                "Lead with the bridge phrase, then ask the question naturally."
            )

        if steer == SteerAction.ZOOM_OUT:
            bridge = session_dir.get("bridge_phrase", "")
            return (
                f"{bridge}\n\n"
                "Invite the candidate to step back and reflect on the broader architectural "
                "picture: tradeoffs made, alternatives considered, or constraints that shaped decisions. "
                "Respond as the interviewer in 1-2 sentences."
            )

        if steer == SteerAction.INTRODUCE_CONSTRAINT:
            scenario = session_dir.get("constraint_scenario", "")
            return (
                f"Introduce this scenario: \"{scenario}\" "
                "Ask how they would adapt their current design. "
                "One scenario, one question."
            )

        if steer == SteerAction.PRESSURE_PROBE:
            probe = session_dir.get("adversarial_probe") or ""
            pressure_instr = session_dir.get("pressure_instruction", "")
            return (
                f"{pressure_instr}\n\n"
                + (f"Use this probe: \"{probe}\"\n\n" if probe else "")
                + "Respond as the interviewer in 1-2 sentences. Be direct and specific."
            )

        # ── Recovery support ─────────────────────────────────────────────────
        is_stumble = session_dir.get("is_in_stumble", False)
        is_collapsed = session_dir.get("is_collapsed", False)
        if is_collapsed or is_stumble:
            pressure_instr = session_dir.get("pressure_instruction", "")
            return (
                f"{pressure_instr}\n\n"
                "Respond as the interviewer in 1-2 sentences. "
                "Be warm and scaffolding — help the candidate regain their footing."
            )

        # ── BREADTH_REDIRECT (turn-layer keyword fixation guard) ──────────────
        if decision.action == TurnAction.BREADTH_REDIRECT:
            metadata = decision.metadata or {}
            redirect_prompt = metadata.get("breadth_redirect_prompt")
            if redirect_prompt:
                return (
                    f"Say to the candidate, verbatim: \"{redirect_prompt}\"\n\n"
                    "Then naturally bridge to a different architectural topic or trade-off."
                )
            return (
                "Ask the candidate to step back and describe the broader architectural "
                "decisions they considered beyond the current topic. "
                "Respond as the interviewer in 1-2 sentences."
            )

        # ── Standard turn-layer actions ───────────────────────────────────────
        action_prompts = {
            TurnAction.FOLLOW_UP:          "Generate a follow-up question to explore this topic further.",
            TurnAction.PROBE_DEEPER:       "Probe deeper into the candidate's answer to assess understanding.",
            TurnAction.CLARIFY:            "Ask for clarification on the candidate's response.",
            TurnAction.CHALLENGE_CANDIDATE:"Challenge the candidate's answer or assumptions.",
            TurnAction.GIVE_HINT:          "Provide a helpful hint to guide the candidate.",
            TurnAction.SIMPLIFY_QUESTION:  "Rephrase the question in simpler terms.",
            TurnAction.NEXT_QUESTION:      "Move to the next question in the interview.",
        }

        pressure_instr = session_dir.get("pressure_instruction", "")
        base = action_prompts.get(decision.action, "Continue the interview naturally.")
        if pressure_instr:
            base = f"{pressure_instr}\n\n{base}"

        return f"{base}\n\nRespond as the interviewer in 1-2 sentences."
    
    def _get_fallback_response(self, decision: TurnDecision) -> str:
        """Get rule-based fallback response."""

        # Session-layer steer actions get priority in fallback too
        from app.ai.orchestrators.session.session_coverage_planner import SteerAction
        session_dir = decision.session_directive or {}
        steer = session_dir.get("steer_action", SteerAction.CONTINUE)

        if steer == SteerAction.PIVOT_TO:
            target = (session_dir.get("target_area") or "a different area").replace("_", " ")
            bridge = session_dir.get("bridge_phrase") or f"Let's shift to {target}."
            return bridge

        if steer == SteerAction.ZOOM_OUT:
            return "Let's zoom out — how did these decisions fit into the overall system architecture?"

        if steer == SteerAction.PRESSURE_PROBE:
            probe = session_dir.get("adversarial_probe")
            return probe or "Walk me through what happens when that assumption breaks down."

        if session_dir.get("is_collapsed") or session_dir.get("is_in_stumble"):
            return "Take your time — let's think through this together."

        fallbacks = {
            TurnAction.FOLLOW_UP:          "Tell me more about that.",
            TurnAction.PROBE_DEEPER:       "Can you explain your reasoning?",
            TurnAction.CLARIFY:            "Could you clarify what you mean?",
            TurnAction.CHALLENGE_CANDIDATE:"How would you handle edge cases?",
            TurnAction.GIVE_HINT:          "Think about the data structures involved.",
            TurnAction.SIMPLIFY_QUESTION:  "Let me rephrase that question.",
            TurnAction.NEXT_QUESTION:      "Let's move on to the next topic.",
            TurnAction.BREADTH_REDIRECT:   (
                "Let's step back — what other architectural decisions did you consider "
                "beyond what we've been discussing?"
            ),
        }

        return fallbacks.get(decision.action, "Let's continue.")
    
    async def _generate_speculative(
        self,
        decision: TurnDecision,
        context: Dict[str, Any],
        orchestrators: Dict[str, Any]
    ) -> None:
        """
        Generate speculative responses for likely next actions.
        
        Predicts what the candidate might say and pre-generates likely responses.
        """
        
        try:
            # Predict likely next actions based on current action
            likely_actions = self._predict_next_actions(decision.action)
            
            # Generate for top 2 most likely
            for action in likely_actions[:2]:
                cache_key = self._make_cache_key(context, action)
                
                # Generate speculatively
                speculative_decision = TurnDecision(
                    action=action,
                    reason="speculative",
                    confidence=0.7
                )
                
                prompt = self._build_generation_prompt(speculative_decision, context)
                
                # Generate with low timeout (don't block main flow)
                try:
                    response = await asyncio.wait_for(
                        orchestrators["model"].generate(
                            task=ModelTask.REALTIME_RESPONSE,
                            prompt=prompt,
                            max_tokens=150,
                            temperature=0.7,
                            timeout_ms=200
                        ),
                        timeout=0.3
                    )
                    
                    # Cache for later
                    self.speculative_cache[cache_key] = SpeculativeGeneration(
                        action=action,
                        generated_text=response.text,
                        timestamp=datetime.utcnow(),
                        confidence=0.7
                    )
                    
                    logger.debug(f"Speculative generation cached for {action.value}")
                    
                except asyncio.TimeoutError:
                    logger.debug(f"Speculative generation timeout for {action.value}")
                    pass
        
        except Exception as e:
            logger.warning(f"Speculative generation failed: {e}")
    
    def _predict_next_actions(self, current_action: TurnAction) -> List[TurnAction]:
        """
predict likely next actions based on current action."""
        
        predictions = {
            TurnAction.FOLLOW_UP: [TurnAction.PROBE_DEEPER, TurnAction.NEXT_QUESTION, TurnAction.CLARIFY],
            TurnAction.PROBE_DEEPER: [TurnAction.FOLLOW_UP, TurnAction.CHALLENGE_CANDIDATE, TurnAction.NEXT_QUESTION],
            TurnAction.CLARIFY: [TurnAction.FOLLOW_UP, TurnAction.GIVE_HINT, TurnAction.NEXT_QUESTION],
            TurnAction.CHALLENGE_CANDIDATE: [TurnAction.PROBE_DEEPER, TurnAction.FOLLOW_UP, TurnAction.NEXT_QUESTION],
            TurnAction.GIVE_HINT: [TurnAction.FOLLOW_UP, TurnAction.CLARIFY, TurnAction.NEXT_QUESTION],
            TurnAction.SIMPLIFY_QUESTION: [TurnAction.FOLLOW_UP, TurnAction.GIVE_HINT, TurnAction.NEXT_QUESTION],
            TurnAction.NEXT_QUESTION: [TurnAction.FOLLOW_UP, TurnAction.PROBE_DEEPER, TurnAction.CLARIFY],
        }
        
        return predictions.get(current_action, [TurnAction.NEXT_QUESTION])
    
    async def _check_speculative_cache(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if we have a speculative response cached."""
        
        if not context.get("last_decision"):
            return None
        
        # Predict what action we're likely to take
        likely_actions = self._predict_next_actions(context["last_decision"].action)
        
        for action in likely_actions:
            cache_key = self._make_cache_key(context, action)
            
            if cache_key in self.speculative_cache:
                cached = self.speculative_cache[cache_key]
                
                # Check if not expired (5 seconds)
                age = (datetime.utcnow() - cached.timestamp).total_seconds()
                if age < 5:
                    return {
                        "text": cached.generated_text,
                        "action": cached.action
                    }
        
        return None
    
    def _make_cache_key(self, context: Dict[str, Any], action: TurnAction) -> str:
        """Make cache key for speculative generation."""
        
        session_id = context.get("session_id", "")
        turn = context.get("turn_number", 0)
        
        return f"{session_id}:{turn}:{action.value}"
    
    def _record_latency(self, breakdown: LatencyBreakdown) -> None:
        """Record latency metrics."""
        
        self.total_turns += 1
        self.total_latencies.append(breakdown.total_ms)
        
        # Record by stage
        stages = {
            "stt": breakdown.stt_ms,
            "analysis": breakdown.analysis_ms,
            "decision": breakdown.decision_ms,
            "context_assembly": breakdown.context_assembly_ms,
            "generation": breakdown.generation_ms,
            "tts": breakdown.tts_ms
        }
        
        for stage, latency in stages.items():
            if stage not in self.stage_latencies:
                self.stage_latencies[stage] = []
            self.stage_latencies[stage].append(latency)
            
            # Keep only recent (last 100)
            if len(self.stage_latencies[stage]) > 100:
                self.stage_latencies[stage] = self.stage_latencies[stage][-100:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        
        if not self.total_latencies:
            return {}
        
        avg_total = sum(self.total_latencies) / len(self.total_latencies)
        p95_total = sorted(self.total_latencies)[int(len(self.total_latencies) * 0.95)] if len(self.total_latencies) > 1 else avg_total
        
        violation_rate = self.budget_violations / self.total_turns if self.total_turns > 0 else 0
        
        stage_stats = {}
        for stage, latencies in self.stage_latencies.items():
            if latencies:
                stage_stats[stage] = {
                    "avg_ms": sum(latencies) / len(latencies),
                    "p95_ms": sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0]
                }
        
        cache_hit_rate = (
            self.speculative_hits / (self.speculative_hits + self.speculative_misses)
            if (self.speculative_hits + self.speculative_misses) > 0
            else 0
        )
        
        return {
            "total_turns": self.total_turns,
            "avg_latency_ms": avg_total,
            "p95_latency_ms": p95_total,
            "target_ms": self.latency_target.total_target_ms,
            "budget_violations": self.budget_violations,
            "violation_rate": violation_rate,
            "stage_latencies": stage_stats,
            "speculative_cache_hit_rate": cache_hit_rate,
            "speculative_hits": self.speculative_hits,
            "speculative_misses": self.speculative_misses
        }
