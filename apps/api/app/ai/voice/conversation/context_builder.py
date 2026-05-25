import logging
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.decisions.decision import ConversationDecision

logger = logging.getLogger("context_builder")

class ContextBuilder:
    def __init__(self):
        pass

    def build_messages(self, state: InterviewState, decision: ConversationDecision, tone: str) -> list[dict]:
        """
        Converts internal structured state messages into direct LLM prompt payload.
        Injects system directive hints based on turn decision policies.
        
        :param state: The live InterviewState.
        :param decision: The calculated ConversationDecision.
        :param tone: The selected conversational tone.
        :return: A list of message dictionaries: [{"role": str, "content": str}].
        """
        llm_messages = []
        for msg in state.conversation.messages:
            role = msg.role
            # Map system-defined roles to LLM-compatible provider roles
            if role == "panelist":
                role = "assistant"
            
            llm_messages.append({
                "role": role,
                "content": msg.content
            })

        # Append the policy instruction as a system directive
        directive = f"[SYSTEM DIRECTIVE: Action={decision.action.value}, Reason={decision.reason}, Tone={tone}]"
        
        # If there is followup context, append it to the system directive
        followup_context = decision.metadata.get("followup_context") if decision.metadata else None
        if followup_context:
            directive += f" {followup_context}"

        llm_messages.append({
            "role": "system",
            "content": directive
        })

        logger.info("context_built | message_count: %d | instruction: %s", len(llm_messages), directive)
        return llm_messages
