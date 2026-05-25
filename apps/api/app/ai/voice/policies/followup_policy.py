import logging

logger = logging.getLogger("followup_policy")

class FollowupPolicy:
    def __init__(self, key_concepts: list[str] = None):
        """
        Policy to assess if the candidate's response has interesting technical concepts to follow up on.
        """
        self.key_concepts = key_concepts or [
            "optimization", "caching", "scaling", "architecture", "performance", "database", "query", "async"
        ]

    def should_followup(self, state) -> bool:
        messages = state.conversation.messages
        user_msgs = [m for m in messages if m.role == "user"]
        if not user_msgs:
            return False

        last_user_msg = user_msgs[-1]
        text_lower = last_user_msg.content.lower()

        # Check if the candidate mentions any expandable concepts
        for concept in self.key_concepts:
            if concept in text_lower:
                logger.info("followup_selected | matched concept: %s", concept)
                return True
        return False

    def generate_followup_context(self, state) -> str:
        messages = state.conversation.messages
        user_msgs = [m for m in messages if m.role == "user"]
        if not user_msgs:
            return ""

        last_user_msg = user_msgs[-1]
        text_lower = last_user_msg.content.lower()
        matched = [concept for concept in self.key_concepts if concept in text_lower]
        
        if matched:
            return f"The candidate mentioned technical concepts: {', '.join(matched)}. Drill down into details."
        return ""
