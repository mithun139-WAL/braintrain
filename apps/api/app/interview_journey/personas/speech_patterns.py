"""
Speech Pattern Rules — defines how each speaking style behaves in interview dialogue.
"""


SPEECH_PATTERNS = {
    "concise": {
        "avg_sentence_length": "short",
        "uses_transitional_phrases": False,
        "directness": 0.9,
        "small_talk": False,
        "question_style": "direct_questions",
        "interjection_frequency": "high",
        "typical_openers": [
            "Let's start.",
            "Walk me through...",
            "Explain your approach to...",
        ],
        "followup_openers": [
            "Why?",
            "How?",
            "What else?",
        ],
    },
    "probing": {
        "avg_sentence_length": "medium",
        "uses_transitional_phrases": False,
        "directness": 0.7,
        "small_talk": False,
        "question_style": "socratic",
        "interjection_frequency": "medium",
        "typical_openers": [
            "I'm curious about...",
            "Tell me more about why...",
            "What led you to that conclusion?",
        ],
        "followup_openers": [
            "What makes you say that?",
            "Can you elaborate?",
            "Walk me through your reasoning.",
        ],
    },
    "friendly": {
        "avg_sentence_length": "medium",
        "uses_transitional_phrases": True,
        "directness": 0.5,
        "small_talk": True,
        "question_style": "conversational",
        "interjection_frequency": "low",
        "typical_openers": [
            "Thanks for joining! Let's dive in.",
            "I'd love to hear about your experience with...",
            "Great to meet you! Let's start with...",
        ],
        "followup_openers": [
            "That's interesting! Can you tell me more?",
            "I appreciate that. What about...",
            "Nice. How did you approach...",
        ],
    },
    "warm": {
        "avg_sentence_length": "longer",
        "uses_transitional_phrases": True,
        "directness": 0.4,
        "small_talk": True,
        "question_style": "conversational",
        "interjection_frequency": "very_low",
        "typical_openers": [
            "It's great to chat with you! Let's explore...",
            "I'm really looking forward to hearing about...",
            "Let's start with something I think you'll enjoy...",
        ],
        "followup_openers": [
            "That's really thoughtful. What else comes to mind?",
            "I love that perspective. Can you build on it?",
            "Excellent point! Let's go deeper there.",
        ],
    },
    "direct": {
        "avg_sentence_length": "short",
        "uses_transitional_phrases": False,
        "directness": 0.95,
        "small_talk": False,
        "question_style": "direct_questions",
        "interjection_frequency": "medium",
        "typical_openers": [
            "Right, let's get into it.",
            "I want to understand...",
            "Tell me directly about...",
        ],
        "followup_openers": [
            "Be more specific.",
            "Give me an example.",
            "What actually happened?",
        ],
    },
    "calm": {
        "avg_sentence_length": "medium",
        "uses_transitional_phrases": True,
        "directness": 0.6,
        "small_talk": False,
        "question_style": "reflective",
        "interjection_frequency": "low",
        "typical_openers": [
            "Let's take a thoughtful look at...",
            "I'd like to understand your thinking on...",
            "Take your time with this one...",
        ],
        "followup_openers": [
            "Consider the tradeoffs...",
            "How does that fit with...",
            "What principles guide that decision?",
        ],
    },
}


def get_speech_pattern(speaking_style: str) -> dict:
    return SPEECH_PATTERNS.get(speaking_style, SPEECH_PATTERNS["concise"])


def build_persona_prompt_layer(persona: dict) -> str:
    name = persona.get("name", "Interviewer")
    role = persona.get("role", "Interviewer")
    style = persona.get("speaking_style", "concise")
    patterns = get_speech_pattern(style)

    lines = [
        f"You are {name}, a {role} interviewing this candidate.",
        f"Your speaking style is {style} — {_describe_style(style)}.",
        f"Pressure style: {persona.get('pressure_style', 'balanced')}.",
    ]

    if persona.get("warmth", 0.5) < 0.4:
        lines.append("Keep a professional distance. Do not over-praise.")
    elif persona.get("warmth", 0.5) > 0.7:
        lines.append("Be encouraging and supportive. Make the candidate comfortable.")

    if persona.get("interruption_frequency", 0.5) > 0.6:
        lines.append("Interrupt when the candidate is being vague or off-track.")
    else:
        lines.append("Let the candidate finish their thoughts before following up.")

    lines.extend([
        "Never invent candidate experience — only ask about what's in their verified profile.",
        "Stay within the round scope. Do not switch domains unexpectedly.",
        "Ask one question at a time.",
    ])

    return "\n".join(lines)


def _describe_style(style: str) -> str:
    descriptions = {
        "concise": "direct and to the point, minimal small talk",
        "probing": "asks deep follow-ups, challenges assumptions",
        "friendly": "conversational and approachable",
        "warm": "encouraging and supportive",
        "direct": "blunt and straightforward",
        "calm": "measured and thoughtful",
    }
    return descriptions.get(style, "professional and focused")
