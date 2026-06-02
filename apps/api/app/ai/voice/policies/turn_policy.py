import logging
from app.ai.voice.decisions.action import InterviewAction
from app.ai.voice.decisions.decision import ConversationDecision
from app.ai.voice.policies.interruption_policy import InterruptionPolicy
from app.ai.voice.policies.followup_policy import FollowupPolicy
from app.ai.voice.policies.difficulty_policy import DifficultyPolicy
from app.ai.voice.policies.response_policy import ResponsePolicy

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

    def decide_next_action(self, state) -> ConversationDecision:
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
        hard_end = target_duration - 1.0
        wrap_start = target_duration - 3.0
        
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

        # Rule 4: Topic Exhaustion / Strict Followup Cap
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
