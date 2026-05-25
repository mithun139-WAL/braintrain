import logging

logger = logging.getLogger("interruption_policy")

class InterruptionPolicy:
    def __init__(self, word_count_threshold: int = 150, verbosity_threshold: float = 80.0):
        """
        Policy to assess if the interviewer should interrupt a rambling candidate.
        """
        self.word_count_threshold = word_count_threshold
        self.verbosity_threshold = verbosity_threshold

    def should_interrupt(self, state) -> bool:
        # Check last user response length
        messages = state.conversation.messages
        user_msgs = [m for m in messages if m.role == "user"]
        if not user_msgs:
            return False

        last_user_msg = user_msgs[-1]
        word_count = len(last_user_msg.content.split())
        
        # Dynamic threshold based on signals
        signals = getattr(state, "behavioral_signals", None)
        verbosity_score = signals.verbosity_score if signals else state.candidate.verbosity_score

        effective_word_threshold = self.word_count_threshold
        if verbosity_score > 75.0:
            # High verbosity / rambling reduces the word count threshold dynamically
            effective_word_threshold = int(self.word_count_threshold * 0.6)
        
        # Verbosity checks
        is_too_long = word_count > effective_word_threshold
        is_too_verbose = verbosity_score > self.verbosity_threshold
        
        if is_too_long or is_too_verbose:
            logger.info("interrupt_decision | triggered | word_count: %d (threshold: %d) | verbosity: %.2f", word_count, effective_word_threshold, verbosity_score)
            return True
        
        return False
