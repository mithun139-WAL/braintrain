"""
Stub coaching AI provider — returns pre-canned encouraging responses.

Used in development (no OPENAI_API_KEY) and FREE-tier users.
Responses are context-aware: they reference the focus area and message history length.
"""
from typing import List


class StubCoachProvider:
    """
    Deterministic stub that generates coaching responses without any API calls.
    Cycles through a bank of helpful, encouraging messages.
    """

    _RESPONSES_BY_FOCUS = {
        "confidence": [
            "Your confidence is something you build through repetition. Let's focus on one thing: when you start your next answer, take a 2-second pause before speaking. This signals that you're thoughtful, not nervous.",
            "Great reflection! A practical exercise: record yourself answering a question for 90 seconds. Watch it back and count how many filler words you use. Awareness is the first step.",
            "You're doing well! Remember: the interviewer wants you to succeed. They're on your side. Approach the next question as a conversation, not a test.",
        ],
        "clarity": [
            "Clarity comes from structure. Try the SBI framework: Situation, Behavior, Impact. It forces you to be specific and concise every time.",
            "One powerful technique: summarize your answer in one sentence BEFORE you expand on it. 'In short, I did X because Y, and the result was Z.' Then elaborate.",
            "Watch out for over-qualification. Phrases like 'sort of', 'kind of', 'I think maybe' weaken your message. Be direct and own your statements.",
        ],
        "technical": [
            "When explaining technical concepts, start with the 'why' before the 'how'. Interviewers want to know you understand the problem space, not just the implementation.",
            "Practice the rubber duck method: explain the technical concept to me as if I'm a non-technical colleague. This reveals gaps in your understanding.",
            "Draw the architecture before describing it. Even in a verbal interview, say 'Let me walk you through this layer by layer.' It shows systems thinking.",
        ],
        "general": [
            "Let's start by identifying your top goal for today's session. What aspect of interviewing do you feel least confident about?",
            "Based on typical interview patterns, the most common gap I see is answer structure. Would you like to practice the STAR method?",
            "Remember: interviews are a two-way conversation. You're evaluating the company too. This reframe can dramatically reduce anxiety.",
        ],
    }

    _GENERIC = [
        "That's a great point. Let's dig deeper into this. Can you give me a specific example from your experience?",
        "I hear you. Let me ask: if you had to distill your answer into one sentence, what would it be?",
        "Good awareness! The next step is turning that insight into a habit. Let's create a concrete practice exercise for this.",
        "You're making real progress. What feels like the biggest blocker for you right now?",
    ]

    async def get_response(
        self,
        messages: List[dict],
        focus_area: str = "general",
        context_summary: str | None = None,
    ) -> str:
        """
        Generate a contextual coaching response.

        messages: list of {"role": "user"|"assistant", "content": str}
        focus_area: from CoachingSession.focus_area
        context_summary: optional evaluation summary for context
        """
        pool = self._RESPONSES_BY_FOCUS.get(focus_area, self._RESPONSES_BY_FOCUS["general"])
        idx = (len(messages) // 2) % len(pool)
        return pool[idx]
