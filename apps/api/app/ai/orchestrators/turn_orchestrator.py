"""
Turn Orchestrator - Manages individual interview turns and action decisions.

This orchestrator analyzes each candidate response and deterministically
decides the next action (follow-up, probe, hint, next question, etc.).
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from pydantic import BaseModel

from app.ai.orchestrators.contracts.turn_contracts import (
    TurnAction,
    AnswerQuality,
    TurnDecision,
    FollowUpStrategy
)
from app.ai.orchestrators.contracts.evaluation_contracts import UnifiedEvaluation
from app.ai.orchestrators.contracts.interview_contracts import (
    InterviewPhase,
    ChallengeLevel,
    InterviewerMood
)
from app.ai.orchestrators.state.interview_runtime_state import (
    TurnState,
    QuestionState,
    CandidateRuntimeState
)
from app.ai.orchestrators.policies.escalation_policy import (
    EscalationPolicy,
    EscalationTracker,
    EscalationTrigger,
    detect_candidate_stuck,
    detect_repeated_confusion,
    detect_off_topic_pattern,
    detect_insufficient_depth
)
from app.ai.orchestrators.policies.topic_fixation_policy import (
    TopicFixationTracker,
    TopicFixationConfig,
)

logger = logging.getLogger(__name__)


class TurnOrchestrator:
    """
    Orchestrator for individual interview turns.
    
    Responsibilities:
    - Analyze candidate response
    - Determine next action based on answer quality
    - Manage follow-up depth
    - Detect escalation conditions
    - Route to appropriate generation strategy
    """
    
    def __init__(
        self,
        escalation_policy: Optional[EscalationPolicy] = None,
        fixation_config: Optional[TopicFixationConfig] = None
    ):
        self.escalation_policy = escalation_policy or EscalationPolicy()
        self.escalation_tracker: Optional[EscalationTracker] = None

        # Session-level topic-fixation trackers keyed by session_id
        self._fixation_trackers: Dict[str, TopicFixationTracker] = {}
        self._fixation_config = fixation_config or TopicFixationConfig()

        # Action routing table based on answer quality
        self.action_routing = self._build_action_routing()

        logger.info("Initialized TurnOrchestrator")
    
    def _build_action_routing(self) -> Dict[AnswerQuality, List[TurnAction]]:
        """
        Build deterministic routing from AnswerQuality to TurnAction.
        
        This is the core decision logic that prevents LLM from making routing decisions.
        """
        return {
            AnswerQuality.EXCELLENT: [
                TurnAction.CHALLENGE_CANDIDATE,
                TurnAction.PROBE_DEEPER,
                TurnAction.NEXT_QUESTION
            ],
            AnswerQuality.GOOD: [
                TurnAction.PROBE_DEEPER,
                TurnAction.FOLLOW_UP,
                TurnAction.NEXT_QUESTION
            ],
            AnswerQuality.SATISFACTORY: [
                TurnAction.FOLLOW_UP,
                TurnAction.NEXT_QUESTION
            ],
            AnswerQuality.PARTIAL: [
                TurnAction.CLARIFY,
                TurnAction.FOLLOW_UP,
                TurnAction.GIVE_HINT
            ],
            AnswerQuality.INSUFFICIENT: [
                TurnAction.CLARIFY,
                TurnAction.GIVE_HINT,
                TurnAction.SIMPLIFY_QUESTION
            ],
            AnswerQuality.INCORRECT: [
                TurnAction.GIVE_HINT,
                TurnAction.SIMPLIFY_QUESTION,
                TurnAction.NEXT_QUESTION
            ],
            AnswerQuality.OFF_TOPIC: [
                TurnAction.CLARIFY,
                TurnAction.FOLLOW_UP
            ],
            AnswerQuality.VAGUE: [
                TurnAction.CLARIFY,
                TurnAction.PROBE_DEEPER
            ],
            AnswerQuality.CONTRADICTORY: [
                TurnAction.CLARIFY,
                TurnAction.CHALLENGE_CANDIDATE
            ]
        }
    
    async def analyze_turn(
        self,
        session_id: str,
        turn_number: int,
        transcript: str,
        evaluation: UnifiedEvaluation,
        current_question: QuestionState,
        candidate_state: CandidateRuntimeState,
        current_phase: InterviewPhase,
        interviewer_mood: InterviewerMood,
        consecutive_followups: int,
        max_followup_depth: int
    ) -> TurnDecision:
        """
        Analyze turn and decide next action.

        Priority order for action selection:
          1. Escalation conditions
          1.5 Topic fixation / breadth guard  ← NEW
          2. Follow-up depth limit
          3. Phase-specific constraints
          4. Answer quality routing
          5. Interviewer mood adjustments
        """

        # Initialize escalation tracker if needed
        if not self.escalation_tracker:
            self.escalation_tracker = EscalationTracker(session_id=session_id)

        # --- Topic fixation tracker (per session) ---
        if session_id not in self._fixation_trackers:
            self._fixation_trackers[session_id] = TopicFixationTracker(
                session_id=session_id,
                config=self._fixation_config
            )
        fixation_tracker = self._fixation_trackers[session_id]

        # Record this turn's topics BEFORE making a decision
        fixation_tracker.record_turn(
            transcript=transcript,
            question_text=current_question.question_text
        )

        # Create turn state
        turn_state = TurnState(
            turn_index=turn_number,
            session_id=session_id,
            question_state=current_question,
            candidate_transcript=transcript
        )

        # Detect escalation conditions
        await self._check_escalations(
            evaluation.answer_quality,
            candidate_state,
            current_phase
        )

        # Determine action based on answer quality and context
        action = await self._determine_action(
            evaluation.answer_quality,
            current_question,
            candidate_state,
            current_phase,
            interviewer_mood,
            consecutive_followups,
            max_followup_depth,
            fixation_tracker=fixation_tracker
        )

        # Determine follow-up strategy if applicable
        followup_strategy = None
        if action in [TurnAction.FOLLOW_UP, TurnAction.PROBE_DEEPER, TurnAction.CLARIFY]:
            followup_strategy = await self._determine_followup_strategy(
                action,
                evaluation.answer_quality,
                current_question,
                current_phase
            )

        # Build metadata — include fixation summary if a redirect fired
        decision_metadata: Dict[str, Any] = {
            "turn_number": turn_number,
            "answer_quality": evaluation.answer_quality.value,
            "final_score": evaluation.final_score,
            "phase": current_phase.value,
            "consecutive_followups": consecutive_followups,
            "topic_exposure": fixation_tracker.get_topic_summary(),
        }
        if action == TurnAction.BREADTH_REDIRECT:
            _, dominant_topic, redirect_prompt = fixation_tracker.check_fixation()
            decision_metadata["breadth_redirect_topic"] = dominant_topic
            decision_metadata["breadth_redirect_prompt"] = redirect_prompt

        # Create decision
        decision = TurnDecision(
            action=action,
            reason=self._generate_reason(action, evaluation.answer_quality),
            confidence=evaluation.confidence,
            followup_strategy=followup_strategy,
            should_adjust_difficulty=self._should_adjust_difficulty(
                evaluation.answer_quality,
                candidate_state
            ),
            metadata=decision_metadata
        )

        logger.info(
            f"Turn decision: action={action.value} quality={evaluation.answer_quality.value} "
            f"score={evaluation.final_score:.1f} session={session_id}"
        )

        return decision
    
    async def _determine_action(
        self,
        answer_quality: AnswerQuality,
        current_question: QuestionState,
        candidate_state: CandidateRuntimeState,
        current_phase: InterviewPhase,
        interviewer_mood: InterviewerMood,
        consecutive_followups: int,
        max_followup_depth: int,
        fixation_tracker: Optional[TopicFixationTracker] = None
    ) -> TurnAction:
        """
        Deterministically determine next action.

        Priority order:
        1.   Escalation conditions (from policy)
        1.5  Topic fixation / breadth redirect guard  ← NEW
        2.   Follow-up depth limits
        3.   Phase-specific constraints
        4.   Answer quality routing
        5.   Interviewer mood adjustments
        """

        # Get possible actions for this answer quality
        possible_actions = self.action_routing.get(
            answer_quality,
            [TurnAction.NEXT_QUESTION]
        )

        # 1. Check escalation conditions
        escalation_action = await self._check_escalation_override(
            answer_quality,
            candidate_state,
            current_phase
        )
        if escalation_action:
            return escalation_action

        # 1.5 Topic fixation / breadth guard
        #
        # Only fires when the candidate (or the question itself) keeps pulling
        # the conversation back to a single concept across multiple turns — even
        # when `consecutive_followups` has reset between questions.
        if fixation_tracker is not None:
            should_redirect, dominant_topic, _ = fixation_tracker.check_fixation()
            if should_redirect:
                logger.info(
                    "Breadth redirect fired: session=%s topic=%s",
                    fixation_tracker.session_id,
                    dominant_topic,
                )
                return TurnAction.BREADTH_REDIRECT

        # 2. Check follow-up depth limit
        if consecutive_followups >= max_followup_depth:
            # Must move on
            if TurnAction.NEXT_QUESTION in possible_actions:
                return TurnAction.NEXT_QUESTION
            else:
                return TurnAction.MOVE_TO_NEXT_ROUND

        # 3. Phase-specific logic
        if current_phase == InterviewPhase.INTRODUCTION:
            # Introduction: keep it simple, move quickly
            if answer_quality in [AnswerQuality.GOOD, AnswerQuality.EXCELLENT]:
                return TurnAction.NEXT_QUESTION
            elif answer_quality == AnswerQuality.SATISFACTORY:
                return TurnAction.FOLLOW_UP if consecutive_followups < 1 else TurnAction.NEXT_QUESTION

        elif current_phase == InterviewPhase.WRAP_UP:
            # Wrap up: don't probe, just acknowledge
            return TurnAction.NEXT_QUESTION

        # 4. Answer quality-based selection
        selected_action = possible_actions[0]  # Default to first option

        # Excellent answers: challenge or probe
        if answer_quality == AnswerQuality.EXCELLENT:
            if interviewer_mood == InterviewerMood.SKEPTICAL:
                selected_action = TurnAction.CHALLENGE_CANDIDATE
            elif consecutive_followups < 2:
                selected_action = TurnAction.PROBE_DEEPER
            else:
                selected_action = TurnAction.NEXT_QUESTION

        # Good answers: probe once then move on
        elif answer_quality == AnswerQuality.GOOD:
            if consecutive_followups == 0:
                selected_action = TurnAction.PROBE_DEEPER
            elif consecutive_followups == 1:
                selected_action = TurnAction.FOLLOW_UP
            else:
                selected_action = TurnAction.NEXT_QUESTION

        # Satisfactory answers: optional follow-up
        elif answer_quality == AnswerQuality.SATISFACTORY:
            if consecutive_followups < 1 and current_phase in [
                InterviewPhase.TECHNICAL_ROUND_1,
                InterviewPhase.TECHNICAL_ROUND_2
            ]:
                selected_action = TurnAction.FOLLOW_UP
            else:
                selected_action = TurnAction.NEXT_QUESTION

        # Partial answers: clarify or hint
        elif answer_quality == AnswerQuality.PARTIAL:
            if consecutive_followups == 0:
                selected_action = TurnAction.CLARIFY
            elif consecutive_followups == 1:
                selected_action = TurnAction.FOLLOW_UP
            elif consecutive_followups >= 2:
                selected_action = TurnAction.GIVE_HINT

        # Insufficient/Incorrect: provide help
        elif answer_quality in [AnswerQuality.INSUFFICIENT, AnswerQuality.INCORRECT]:
            if consecutive_followups == 0:
                selected_action = TurnAction.CLARIFY
            elif consecutive_followups == 1:
                selected_action = TurnAction.GIVE_HINT
            else:
                # Candidate stuck, move on
                selected_action = TurnAction.SIMPLIFY_QUESTION if len(possible_actions) > 2 else TurnAction.NEXT_QUESTION

        # Off-topic: redirect
        elif answer_quality == AnswerQuality.OFF_TOPIC:
            if consecutive_followups < 2:
                selected_action = TurnAction.CLARIFY
            else:
                selected_action = TurnAction.NEXT_QUESTION

        # Vague: ask for details
        elif answer_quality == AnswerQuality.VAGUE:
            if consecutive_followups < 2:
                selected_action = TurnAction.CLARIFY
            else:
                selected_action = TurnAction.PROBE_DEEPER if TurnAction.PROBE_DEEPER in possible_actions else TurnAction.NEXT_QUESTION

        # Contradictory: challenge
        elif answer_quality == AnswerQuality.CONTRADICTORY:
            if consecutive_followups < 1:
                selected_action = TurnAction.CHALLENGE_CANDIDATE
            else:
                selected_action = TurnAction.CLARIFY

        return selected_action
    
    async def _determine_followup_strategy(
        self,
        action: TurnAction,
        answer_quality: AnswerQuality,
        current_question: QuestionState,
        current_phase: InterviewPhase
    ) -> FollowUpStrategy:
        """Determine follow-up strategy based on action and context."""
        
        # Map action to strategy
        if action == TurnAction.PROBE_DEEPER:
            return FollowUpStrategy(strategy_type="probe_deeper", tone="neutral")
        elif action == TurnAction.CLARIFY:
            return FollowUpStrategy(strategy_type="clarify", tone="supportive")
        elif action == TurnAction.CHALLENGE_CANDIDATE:
            return FollowUpStrategy(strategy_type="challenge", tone="challenging")
        elif action == TurnAction.FOLLOW_UP:
            # Context-dependent
            if answer_quality in [AnswerQuality.GOOD, AnswerQuality.EXCELLENT]:
                return FollowUpStrategy(strategy_type="probe_deeper", tone="neutral")
            elif answer_quality == AnswerQuality.VAGUE:
                return FollowUpStrategy(strategy_type="clarify", tone="supportive")
            else:
                return FollowUpStrategy(strategy_type="explore_related", tone="neutral")
        else:
            return FollowUpStrategy(strategy_type="explore_related", tone="neutral")
    
    async def _check_escalations(
        self,
        answer_quality: AnswerQuality,
        candidate_state: CandidateRuntimeState,
        current_phase: InterviewPhase
    ) -> None:
        """Check for escalation conditions and record them."""
        
        if not self.escalation_tracker:
            return
        
        timestamp = datetime.utcnow().timestamp()
        recent_qualities = candidate_state.answer_quality_history[-5:]
        
        # Detect various escalation conditions
        if detect_candidate_stuck(answer_quality, recent_qualities):
            self.escalation_tracker.record_trigger(
                EscalationTrigger.CANDIDATE_STUCK,
                timestamp
            )
        
        if detect_repeated_confusion(answer_quality, recent_qualities):
            self.escalation_tracker.record_trigger(
                EscalationTrigger.REPEATED_CONFUSION,
                timestamp
            )
        
        if detect_off_topic_pattern(answer_quality, recent_qualities):
            self.escalation_tracker.record_trigger(
                EscalationTrigger.OFF_TOPIC_PATTERN,
                timestamp
            )
        
        if detect_insufficient_depth(answer_quality, recent_qualities):
            self.escalation_tracker.record_trigger(
                EscalationTrigger.TECHNICAL_DEPTH_INSUFFICIENT,
                timestamp
            )
    
    async def _check_escalation_override(
        self,
        answer_quality: AnswerQuality,
        candidate_state: CandidateRuntimeState,
        current_phase: InterviewPhase
    ) -> Optional[TurnAction]:
        """
        Check if escalation policy should override normal action.
        
        Returns TurnAction if escalation should occur, None otherwise.
        """
        
        if not self.escalation_tracker:
            return None
        
        # Check each escalation trigger
        for trigger in EscalationTrigger:
            consecutive = self.escalation_tracker.get_consecutive_count(trigger)
            total = self.escalation_tracker.get_total_count(trigger)
            
            should_escalate, escalation_action = self.escalation_policy.should_escalate(
                trigger,
                consecutive,
                total,
                current_phase
            )
            
            if should_escalate and escalation_action:
                # Map escalation action to turn action
                turn_action = self._map_escalation_to_turn_action(escalation_action)
                
                if turn_action:
                    logger.warning(
                        f"Escalation triggered: {trigger.value} -> {escalation_action.value}"
                    )
                    
                    # Record action taken
                    self.escalation_tracker.record_action(
                        trigger,
                        escalation_action,
                        datetime.utcnow().timestamp()
                    )
                    
                    return turn_action
        
        return None
    
    def _map_escalation_to_turn_action(self, escalation_action) -> Optional[TurnAction]:
        """Map escalation action to turn action."""
        from app.ai.orchestrators.policies.escalation_policy import EscalationAction
        
        mapping = {
            EscalationAction.SIMPLIFY_QUESTION: TurnAction.SIMPLIFY_QUESTION,
            EscalationAction.PROVIDE_HINT: TurnAction.GIVE_HINT,
            EscalationAction.MOVE_TO_EASIER_TOPIC: TurnAction.NEXT_QUESTION,
            EscalationAction.SKIP_TO_NEXT_PHASE: TurnAction.MOVE_TO_NEXT_ROUND,
        }
        
        return mapping.get(escalation_action)
    
    def _should_adjust_difficulty(
        self,
        answer_quality: AnswerQuality,
        candidate_state: CandidateRuntimeState
    ) -> bool:
        """
        Determine if difficulty should be adjusted for next question.
        """
        
        # Excellent performance: increase difficulty
        if answer_quality == AnswerQuality.EXCELLENT:
            if candidate_state.performance_trend == "improving":
                return True
        
        # Poor performance: decrease difficulty
        elif answer_quality in [
            AnswerQuality.INSUFFICIENT,
            AnswerQuality.INCORRECT,
            AnswerQuality.PARTIAL
        ]:
            if candidate_state.performance_trend == "declining":
                return True
        
        return False
    
    def _generate_reason(self, action: TurnAction, quality: AnswerQuality) -> str:
        """Generate human-readable reason for the action."""

        reasons = {
            (TurnAction.NEXT_QUESTION, AnswerQuality.EXCELLENT): "Excellent answer, moving to next topic",
            (TurnAction.NEXT_QUESTION, AnswerQuality.GOOD): "Good answer, progressing forward",
            (TurnAction.NEXT_QUESTION, AnswerQuality.SATISFACTORY): "Satisfactory answer, continuing",
            (TurnAction.PROBE_DEEPER, AnswerQuality.EXCELLENT): "Strong answer, probing for deeper understanding",
            (TurnAction.PROBE_DEEPER, AnswerQuality.GOOD): "Good foundation, exploring further",
            (TurnAction.FOLLOW_UP, AnswerQuality.GOOD): "Following up to assess depth",
            (TurnAction.FOLLOW_UP, AnswerQuality.SATISFACTORY): "Seeking additional details",
            (TurnAction.CLARIFY, AnswerQuality.VAGUE): "Answer unclear, requesting clarification",
            (TurnAction.CLARIFY, AnswerQuality.OFF_TOPIC): "Response off-topic, redirecting",
            (TurnAction.CLARIFY, AnswerQuality.PARTIAL): "Partial answer, seeking clarity",
            (TurnAction.GIVE_HINT, AnswerQuality.INSUFFICIENT): "Candidate struggling, providing hint",
            (TurnAction.GIVE_HINT, AnswerQuality.INCORRECT): "Incorrect approach, offering guidance",
            (TurnAction.CHALLENGE_CANDIDATE, AnswerQuality.EXCELLENT): "Challenging strong candidate",
            (TurnAction.CHALLENGE_CANDIDATE, AnswerQuality.CONTRADICTORY): "Addressing contradiction",
            (TurnAction.SIMPLIFY_QUESTION, AnswerQuality.INSUFFICIENT): "Simplifying question to aid understanding",
            (TurnAction.MOVE_TO_NEXT_ROUND, AnswerQuality.EXCELLENT): "Advancing to next round",
        }

        # BREADTH_REDIRECT reason is quality-agnostic
        if action == TurnAction.BREADTH_REDIRECT:
            return "Topic fixation detected — steering candidate toward broader architectural context"

        key = (action, quality)
        return reasons.get(key, f"Action: {action.value} based on {quality.value} answer")
    
    async def should_reset_followup_chain(
        self,
        action: TurnAction,
        consecutive_followups: int
    ) -> bool:
        """
        Determine if follow-up chain should be reset.
        
        Reset when moving to new question or phase.
        """
        reset_actions = [
            TurnAction.NEXT_QUESTION,
            TurnAction.MOVE_TO_NEXT_ROUND
        ]
        
        return action in reset_actions
