"""
Follow-up Engine — classifies candidate answers and routes to appropriate follow-up.

Rules-based classification with fallback to LLM for nuanced cases.
"""
import re
from enum import Enum


class AnswerClass(str, Enum):
    GOOD = "GOOD"
    PARTIAL = "PARTIAL"
    VAGUE = "VAGUE"
    WRONG = "WRONG"
    STRONG_SIGNAL = "STRONG_SIGNAL"
    WEAK_SIGNAL = "WEAK_SIGNAL"
    BLUFFING = "BLUFFING"


def classify_answer(question: str, answer: str) -> AnswerClass:
    if not answer or len(answer.strip()) < 10:
        return AnswerClass.VAGUE

    score = 0
    signals = _analyze_answer_signals(answer)

    if signals["has_specific_detail"]:
        score += 2
    if signals["has_structure"]:
        score += 1
    if signals["has_tradeoffs"]:
        score += 2
    if signals["has_example"]:
        score += 2
    if signals["has_ownership"]:
        score += 1

    if signals["is_bluffing"]:
        return AnswerClass.BLUFFING
    if signals["is_circular"]:
        return AnswerClass.VAGUE
    if signals["has_contradiction"]:
        return AnswerClass.WRONG
    if signals["buzzword_dense"] and not signals["has_specific_detail"]:
        return AnswerClass.BLUFFING

    if score >= 6:
        return AnswerClass.STRONG_SIGNAL
    elif score >= 4:
        return AnswerClass.GOOD
    elif score >= 2:
        return AnswerClass.PARTIAL
    else:
        return AnswerClass.VAGUE


def _analyze_answer_signals(answer: str) -> dict:
    lower = answer.lower()

    detail_indicators = [
        r"\d+", r"(?:specifically|for example|in particular)",
        r"(?:implemented|built|designed|created|developed|architected)",
        r"(?:using|with|via)\s+(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    ]
    has_specific_detail = any(
        re.search(p, answer) for p in detail_indicators
    )

    structure_indicators = [
        r"(?:first|second|third|finally|initially|subsequently)",
        r"(?:on the one hand|on the other hand|conversely)",
        r"(?:the approach|the solution|the strategy)",
    ]
    has_structure = any(re.search(p, lower) for p in structure_indicators)

    tradeoff_indicators = [
        r"trade.?off|compromise|pros? and cons?|balance|"
        r"however|downside|disadvantage|caveat|limitation"
    ]
    has_tradeoffs = bool(re.search(tradeoff_indicators, lower))

    example_indicators = [
        r"(?:for example|for instance|e\.g\.|such as|like when)",
        r"(?:in one case|in my experience|specifically|concrete)",
    ]
    has_example = any(re.search(p, lower) for p in example_indicators)

    ownership_indicators = [
        r"(?:I\s+(?:led|built|designed|created|owned|drove|initiated))",
        r"(?:my team|my project|my responsibility)",
        r"(?:I was responsible|I owned|I architected)",
    ]
    has_ownership = any(re.search(p, answer) for p in ownership_indicators)

    buzzword_count = sum(
        1 for w in [
            "synergy", "leveraging", "utilize", "paradigm", "holistic",
            "robust", "scalable", "optimize", "innovative", "dynamic",
            "ecosystem", "best practice", "agile", "blockchain", "ml",
            "ai-driven", "cutting-edge", "next-generation", "bleeding edge",
        ]
        if w in lower
    )
    buzzword_dense = buzzword_count >= 3

    circular_patterns = [
        r"it depends on what you mean by",
        r"that's a great question",
        r"well, essentially",
        r"in other words, it's",
        r"to put it simply",
        r"the thing is",
    ]
    is_circular = any(re.search(p, lower) for p in circular_patterns) and len(answer) < 100

    contradiction_patterns = [
        (r"\b(?:yes|definitely|absolutely)\b", r"\b(?:but\s+(?:I'?m\s+)?not\s+sure|however\s+I\s+don'?t)"),
    ]
    has_contradiction = any(
        re.search(p1, lower) and re.search(p2, lower)
        for p1, p2 in contradiction_patterns
    )

    abstraction_patterns = [
        r"in theory",
        r"conceptually",
        r"abstractly",
        r"generally speaking",
        r"at a high level",
    ]
    abstraction_count = sum(1 for p in abstraction_patterns if re.search(p, lower))
    is_bluffing = (
        buzzword_dense and abstraction_count >= 2 and not has_specific_detail
    )

    return {
        "has_specific_detail": has_specific_detail,
        "has_structure": has_structure,
        "has_tradeoffs": has_tradeoffs,
        "has_example": has_example,
        "has_ownership": has_ownership,
        "buzzword_dense": buzzword_dense,
        "is_circular": is_circular,
        "has_contradiction": has_contradiction,
        "is_bluffing": is_bluffing,
        "abstraction_count": abstraction_count,
    }


def route_followup(
    classification: AnswerClass,
    question: str,
    answer: str,
    round_focus: list[str],
) -> dict:
    routes = {
        AnswerClass.STRONG_SIGNAL: {
            "action": "deepen",
            "acknowledgement": "Good. Let's go deeper.",
            "should_follow_up": True,
        },
        AnswerClass.GOOD: {
            "action": "probing",
            "acknowledgement": "Okay, tell me more about that approach.",
            "should_follow_up": True,
        },
        AnswerClass.PARTIAL: {
            "action": "clarify",
            "acknowledgement": "I want to understand better. Can you clarify?",
            "should_follow_up": True,
        },
        AnswerClass.VAGUE: {
            "action": "grounding",
            "acknowledgement": "Let's be more specific. Can you give me a concrete example?",
            "should_follow_up": True,
        },
        AnswerClass.WRONG: {
            "action": "guide",
            "acknowledgement": "Let me rephrase. Think about this differently...",
            "should_follow_up": True,
        },
        AnswerClass.BLUFFING: {
            "action": "pressure_test",
            "acknowledgement": "Let's get into the implementation details. How exactly would that work?",
            "should_follow_up": True,
        },
        AnswerClass.WEAK_SIGNAL: {
            "action": "explore",
            "acknowledgement": "I see. Let's explore that angle more.",
            "should_follow_up": True,
        },
    }

    return routes.get(classification, routes[AnswerClass.VAGUE])


def get_followup_question(
    classification: AnswerClass,
    question: str,
    answer: str,
    round_focus: list[str],
    persona: dict,
) -> str | None:
    action = route_followup(classification, question, answer, round_focus)

    if not action["should_follow_up"]:
        return None

    templates = {
        "deepen": [
            "How does your approach handle edge cases?",
            f"What were the trade-offs in your {_extract_topic(question)} design?",
            "How does this scale beyond your current use case?",
            "What would you improve about that implementation?",
        ],
        "probing": [
            "Can you walk me through a specific example?",
            "What was the most challenging part of implementing that?",
            "How did you measure the success of that approach?",
        ],
        "clarify": [
            "I'm not sure I follow. Can you break that down?",
            f"What do you mean specifically by '{_extract_vague_term(answer)}'?",
            "Can you give me a concrete scenario where this applied?",
        ],
        "grounding": [
            "Give me a specific example from your experience.",
            "Walk me through exactly what you built.",
            "Tell me about a real project where you used this.",
        ],
        "guide": [
            "Let's approach this from a different angle. What would a basic implementation look like?",
            "Think about this step by step. What's the first thing you'd do?",
            "Consider the simplest possible solution first.",
        ],
        "pressure_test": [
            "That sounds good in theory. Can you write the actual implementation?",
            "I hear the concepts, but what specific code would you write?",
            "Let's stop at the abstraction level. Show me the actual approach.",
        ],
        "explore": [
            "That's interesting. How does this compare to alternatives?",
            "What led you to choose this over other options?",
            "If you were to rebuild this, what would you change?",
        ],
    }

    candidates = templates.get(action["action"], templates["probing"])
    import random
    return random.choice(candidates)


def _extract_topic(question: str) -> str:
    words = question.split()
    for w in words:
        if w[0].isupper() and len(w) > 3:
            return w
    return "system"


def _extract_vague_term(answer: str) -> str:
    vague_terms = ["thing", "stuff", "process", "approach", "way", "method", "solution"]
    for term in vague_terms:
        if term in answer.lower():
            return term
    return "that"


def check_topic_boundary(
    question: str,
    allowed_topics: list[str],
) -> bool:
    if not allowed_topics:
        return True

    topic_map = {
        "frontend": ["react", "vue", "angular", "css", "html", "javascript", "typescript",
                     "component", "rendering", "dom", "browser", "ui", "ux", "style",
                     "state management", "redux", "context"],
        "backend": ["api", "database", "sql", "nosql", "server", "endpoint", "rest",
                    "graphql", "microservice", "cache", "redis", "postgres"],
        "system_design": ["distributed", "scalability", "load balancer", "sharding",
                          "replication", "consistency", "availability", "latency"],
        "infrastructure": ["docker", "kubernetes", "deployment", "ci/cd", "terraform",
                           "monitoring", "observability"],
    }

    question_lower = question.lower()
    for topic in allowed_topics:
        keywords = topic_map.get(topic.lower(), [])
        if any(kw in question_lower for kw in keywords):
            return True

    return True
