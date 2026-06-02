import logging
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.llm.prompt_manager import PromptManager

logger = logging.getLogger("clarification_prompt_builder")

class ClarificationPromptBuilder:
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager

    def build_clarification(self, state: InterviewState) -> str:
        """
        Builds Layer 5 clarification directives if the candidate's last answer is vague, 
        incomplete, or low confidence.
        """
        # Find candidate's last response
        last_candidate_text = ""
        for msg in reversed(state.conversation.messages):
            if msg.role in ("Candidate", "user"):
                last_candidate_text = msg.content
                break

        if not last_candidate_text:
            return ""

        words = last_candidate_text.split()
        word_count = len(words)
        text_lower = last_candidate_text.lower()
        
        directives = []
        
        # 1. Base clarification instruction
        base_clarification = self.prompt_manager.get_clarification_prompt()
        if base_clarification:
            directives.append(base_clarification)

        # 2. Check for brief response
        if word_count < 15:
            directives.append(
                "The candidate's response is very short or potentially incomplete. "
                "Ask a specific, narrow clarifying question to prompt them to expand or elaborate."
            )
            
        # 3. Check for low-confidence phrasing
        low_confidence_keywords = ["maybe", "probably", "i guess", "not sure", "don't know", "i think"]
        if any(kw in text_lower for kw in low_confidence_keywords):
            directives.append(
                "The candidate expressed low confidence or uncertainty. "
                "Ask a clarifying question to verify their understanding or guide them to a clear answer."
            )

        if directives:
            full_clarification = "[CLARIFICATION DIRECTIVES:\n" + "\n".join(f"- {d}" for d in directives) + "]"
            logger.info("clarification_prompt_created | count: %d", len(directives))
            return full_clarification

        return ""
