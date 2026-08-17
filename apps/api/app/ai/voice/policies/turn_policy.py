import logging
from app.ai.voice.decisions.action import InterviewAction
from app.ai.voice.decisions.decision import ConversationDecision
from app.ai.voice.policies.interruption_policy import InterruptionPolicy
from app.ai.voice.policies.followup_policy import FollowupPolicy
from app.ai.voice.policies.difficulty_policy import DifficultyPolicy
from app.ai.voice.policies.response_policy import ResponsePolicy
from app.ai.voice.planning.sufficiency import SufficiencyScorer
from app.ai.voice.planning.turn_decision import TurnDecisionAction, decide_next_turn

logger = logging.getLogger("turn_policy")

class TurnPolicy:
    def __init__(
        self,
        interruption_policy: InterruptionPolicy,
        followup_policy: FollowupPolicy,
        difficulty_policy: DifficultyPolicy,
        response_policy: ResponsePolicy,
        min_words: int = 3,
        max_topic_turns: int = 3,  # Max consecutive turns on one topic before forcing breadth
        sufficiency_scorer: SufficiencyScorer | None = None,
    ):
        """
        Coordinates Turn-taking behavior rules.
        """
        self.interruption_policy = interruption_policy
        self.followup_policy = followup_policy
        self.difficulty_policy = difficulty_policy
        self.response_policy = response_policy
        
        self.min_words = min_words
        self.max_topic_turns = max_topic_turns
        self.sufficiency_scorer = sufficiency_scorer or SufficiencyScorer()

    async def decide_next_action(self, state) -> ConversationDecision:
        messages = state.conversation.messages
        user_msgs = [m for m in messages if m.role == "user"]
        
        if not user_msgs:
            # First turn fallback
            decision = ConversationDecision(
                action=InterviewAction.ASK_QUESTION,
                reason="interview_start",
                confidence=1.0,
            )
            logger.info("turn_decision_created | action: %s | reason: %s", decision.action.value, decision.reason)
            return decision

        last_user_msg = user_msgs[-1]
        word_count = len(last_user_msg.content.split())

        # Rule 0: Session Time Limit Check (2-Phase Wrap-Up)
        import datetime
        elapsed_minutes = (datetime.datetime.utcnow() - state.conversation.started_at).total_seconds() / 60.0
        
        target_duration = getattr(state, "target_duration_minutes", 15)
        state.minutes_remaining = max(0.0, float(target_duration) - elapsed_minutes)
        
        wrap_start = target_duration * 0.73
        hard_end = target_duration * 0.93
        
        if elapsed_minutes >= hard_end:
            decision = ConversationDecision(
                action=InterviewAction.END_INTERVIEW,
                reason="hard_time_limit_reached",
                confidence=1.0,
            )
            logger.info("turn_decision_created | action: %s | reason: %s", decision.action.value, decision.reason)
            return decision
            
        if elapsed_minutes >= wrap_start:
            decision = ConversationDecision(
                action=InterviewAction.WRAP_UP_INTERVIEW,
                reason="wrap_up_phase_started",
                confidence=1.0,
            )
            logger.info("turn_decision_created | action: %s | reason: %s", decision.action.value, decision.reason)
            return decision

        # Rule 1: Empty or extremely short response
        if word_count < self.min_words:
            decision = ConversationDecision(
                action=InterviewAction.ASK_CLARIFICATION,
                reason="answer_too_short",
                confidence=0.9,
            )
            logger.info("turn_decision_created | action: %s | reason: %s", decision.action.value, decision.reason)
            return decision

        # Rule 2: Excessive Verbosity (Interruption check)
        if self.interruption_policy.should_interrupt(state):
            decision = ConversationDecision(
                action=InterviewAction.INTERRUPT,
                reason="candidate_rambling",
                confidence=0.85,
            )
            state.candidate.interruptions_attempted += 1
            logger.info("turn_decision_created | action: %s | reason: %s", decision.action.value, decision.reason)
            return decision

        # Rule 3: Weak Confidence
        signals = getattr(state, "behavioral_signals", None)
        if signals:
            is_hesitant = signals.hesitation_score > 40.0
            is_inconfident = signals.confidence_score < 40.0
        else:
            is_hesitant = state.candidate.hesitation_count > 3
            is_inconfident = state.candidate.confidence_score < 40.0

        if is_hesitant or is_inconfident:
            # Still count this as a "followup" turn — candidate stayed on same topic
            if hasattr(state.conversation, "topic_followup_count"):
                state.conversation.topic_followup_count += 1
            decision = ConversationDecision(
                action=InterviewAction.ENCOURAGE,
                reason="confidence_drop_detected",
                confidence=0.8,
            )
            logger.info("turn_decision_created | action: %s | reason: %s", decision.action.value, decision.reason)
            return decision

        # Rule 4: Topic plan coverage (Steps 1-4 of the topic-coverage fix).
        # If this session has a generated InterviewPlan, let it drive
        # PROBE/PIVOT/NEXT_TOPIC/WRAP_UP instead of the flat legacy cap below —
        # this is what stops indefinite drilling into one topic and makes sure
        # the plan's other topics actually get covered.
        plan = getattr(state.conversation, "plan", None)
        if plan is not None and plan.current() is not None:
            topic = plan.current()
            topic.turns_spent += 1

            sufficiency = None
            try:
                sufficiency = await self.sufficiency_scorer.score(
                    topic_label=topic.label,
                    question_text=state.conversation.current_question_text or topic.label,
                    answer_text=last_user_msg.content,
                )
            except Exception as exc:
                logger.warning("turn_policy | sufficiency scoring failed, proceeding without it: %s", exc)

            import json
            depth_before = topic.depth_count
            turn_decision = decide_next_turn(plan, sufficiency)
            depth_after = topic.depth_count

            log_record = {
                "turn_index": state.conversation.turn_count,
                "candidate_answer_excerpt": last_user_msg.content[:120],
                "extracted_entity_or_topic": state.conversation.current_topic,
                "resolved_topic_id": state.conversation.current_topic,
                "depth_count_before": depth_before,
                "depth_count_after": depth_after,
                "target_depth": topic.target_depth,
                "sufficiency_score": sufficiency.score if sufficiency is not None else None,
                "decision_action": turn_decision.action.value,
                "plan_current_topic_id": topic.topic_id,
            }
            logger.info("TURN_DECISION_RECORD: %s", json.dumps(log_record))

            if turn_decision.action == TurnDecisionAction.WRAP_UP:
                decision = ConversationDecision(
                    action=InterviewAction.WRAP_UP_INTERVIEW,
                    reason=turn_decision.rationale,
                    confidence=0.9,
                )
            elif turn_decision.action == TurnDecisionAction.NEXT_TOPIC:
                next_topic = next((t for t in plan.topics if t.topic_id == turn_decision.topic_id), None)
                state.conversation.topic_followup_count = 0
                state.candidate.topic_switches += 1
                decision = ConversationDecision(
                    action=InterviewAction.MOVE_TOPIC,
                    reason=turn_decision.rationale,
                    confidence=0.9,
                    metadata={"next_topic_label": next_topic.label if next_topic else ""},
                )
            elif turn_decision.action == TurnDecisionAction.PIVOT:
                decision = ConversationDecision(
                    action=InterviewAction.PIVOT_TOPIC,
                    reason=turn_decision.rationale,
                    confidence=0.85,
                    metadata={"topic_label": topic.label},
                )
            else:  # PROBE
                state.candidate.followup_count += 1
                decision = ConversationDecision(
                    action=InterviewAction.ASK_FOLLOWUP,
                    reason=turn_decision.rationale,
                    confidence=0.8,
                    metadata={
                        "followup_context": (
                            f"Ask one deeper follow-up on the candidate's last answer, but ensure it relates to the active topic "
                            f"'{topic.label}'. If the candidate's answer was off-topic or went on a tangent, do NOT follow them down "
                            f"the tangent. Instead, guide them back to the active topic '{topic.label}' with a follow-up question. "
                            f"This is follow-up #{topic.depth_count} of at most {topic.target_depth}."
                        )
                    },
                )

            logger.info(
                "turn_decision_created | action: %s | reason: %s | topic: %s",
                decision.action.value, decision.reason, topic.label,
            )
            return decision

        # ── Legacy fallback (no plan generated for this session) ────────────────

        # Rule 4b: Topic Exhaustion / Strict Followup Cap
        # Cap is 2 to match FollowupPolicy._MAX_FOLLOWUPS_PER_TOPIC
        if getattr(state.conversation, "topic_followup_count", 0) >= 2:
            state.conversation.topic_followup_count = 0  # Reset for next topic
            decision = ConversationDecision(
                action=InterviewAction.MOVE_TOPIC,
                reason="topic_exhausted_or_max_followups",
                confidence=0.9,
            )
            state.candidate.topic_switches += 1
            logger.info("turn_decision_created | action: %s | reason: %s", decision.action.value, decision.reason)
            return decision

        # Rule 5: Good Technical Depth / concepts identified
        if self.followup_policy.should_followup(state):
            followup_ctx = self.followup_policy.generate_followup_context(state)
            decision = ConversationDecision(
                action=InterviewAction.ASK_FOLLOWUP,
                reason="candidate_showing_depth",
                confidence=0.8,
                metadata={"followup_context": followup_ctx}
            )
            state.candidate.followup_count += 1
            if hasattr(state.conversation, "topic_followup_count"):
                state.conversation.topic_followup_count += 1
            logger.info("turn_decision_created | action: %s | reason: %s", decision.action.value, decision.reason)
            return decision

        # Fallback to standard question asking progression
        decision = ConversationDecision(
            action=InterviewAction.ASK_QUESTION,
            reason="standard_progression",
            confidence=1.0,
        )
        logger.info("turn_decision_created | action: %s | reason: %s", decision.action.value, decision.reason)
        return decision
