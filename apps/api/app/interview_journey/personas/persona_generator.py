"""
Persona Generator — dynamically creates interviewer personas based on
round context, company style, and strategy.
"""
import random

PERSONA_TEMPLATES = {
    "FAANG_INTERVIEWER": {
        "name_prefixes": ["Alex", "Jordan", "Morgan", "Casey", "Riley"],
        "role_titles": ["Senior Staff Engineer", "Engineering Manager", "Bar Raiser"],
        "speaking_style": "concise",
        "warmth": 0.3,
        "strictness": 0.9,
        "interruption_frequency": 0.7,
        "pacing": "rapid",
        "followup_depth": "deep",
        "pressure_style": "relentless probing",
        "encouragement_level": 0.2,
        "signature_patterns": [
            "That's interesting, but let me push on that...",
            "Walk me through your thought process...",
            "What are the tradeoffs?",
            "How would this scale?",
        ],
    },
    "STARTUP_LEAD": {
        "name_prefixes": ["Taylor", "Sam", "Drew", "Avery", "Cameron"],
        "role_titles": ["CTO", "VP Engineering", "Tech Lead"],
        "speaking_style": "direct",
        "warmth": 0.5,
        "strictness": 0.6,
        "interruption_frequency": 0.4,
        "pacing": "fast",
        "followup_depth": "practical",
        "pressure_style": "product-first pressure",
        "encouragement_level": 0.5,
        "signature_patterns": [
            "How would you build this with limited resources?",
            "What would you ship first?",
            "We need to move fast here — what's your approach?",
            "How does this impact users?",
        ],
    },
    "HR_RECRUITER": {
        "name_prefixes": ["Jamie", "Chris", "Pat", "Blake", "Sydney"],
        "role_titles": ["Talent Partner", "Recruiter", "People Operations"],
        "speaking_style": "friendly",
        "warmth": 0.8,
        "strictness": 0.3,
        "interruption_frequency": 0.1,
        "pacing": "relaxed",
        "followup_depth": "light",
        "pressure_style": "supportive",
        "encouragement_level": 0.9,
        "signature_patterns": [
            "Tell me more about that...",
            "That's great, can you give me an example?",
            "How did that experience shape you?",
            "What are you looking for in your next role?",
        ],
    },
    "BEHAVIORAL_SPECIALIST": {
        "name_prefixes": ["Quinn", "Morgan", "Jamie", "Avery", "Reese"],
        "role_titles": ["Behavioral Interviewer", "Culture Lead", "People Scientist"],
        "speaking_style": "probing",
        "warmth": 0.7,
        "strictness": 0.5,
        "interruption_frequency": 0.2,
        "pacing": "moderate",
        "followup_depth": "medium",
        "pressure_style": "STAR probing",
        "encouragement_level": 0.7,
        "signature_patterns": [
            "Walk me through a specific situation...",
            "What was the outcome?",
            "How did you handle the conflict?",
            "What would you do differently?",
        ],
    },
    "BAR_RAISER": {
        "name_prefixes": ["Drew", "Casey", "Alex", "Jordan", "Riley"],
        "role_titles": ["Bar Raiser", "Principal Engineer", "Director of Engineering"],
        "speaking_style": "concise",
        "warmth": 0.2,
        "strictness": 0.95,
        "interruption_frequency": 0.8,
        "pacing": "rapid",
        "followup_depth": "relentless",
        "pressure_style": "high-stakes interrogation",
        "encouragement_level": 0.1,
        "signature_patterns": [
            "I'm not convinced. Convince me.",
            "What's the real impact of your work?",
            "Why should we hire you over other candidates?",
            "That's a standard answer. Dig deeper.",
        ],
    },
    "PRINCIPAL_ENGINEER": {
        "name_prefixes": ["Morgan", "Jordan", "Casey", "Alex", "Riley"],
        "role_titles": ["Principal Engineer", "Staff Engineer", "Architect"],
        "speaking_style": "calm",
        "warmth": 0.4,
        "strictness": 0.7,
        "interruption_frequency": 0.3,
        "pacing": "deliberate",
        "followup_depth": "philosophical",
        "pressure_style": "intellectual challenge",
        "encouragement_level": 0.4,
        "signature_patterns": [
            "What's the fundamental trade-off here?",
            "How do you think about system evolution?",
            "What principles guide your decisions?",
            "How do you balance short-term vs long-term?",
        ],
    },
    "FRIENDLY_MENTOR": {
        "name_prefixes": ["Sam", "Taylor", "Jamie", "Blake", "Reese"],
        "role_titles": ["Senior Engineer", "Tech Lead", "Engineering Mentor"],
        "speaking_style": "warm",
        "warmth": 0.9,
        "strictness": 0.3,
        "interruption_frequency": 0.1,
        "pacing": "relaxed",
        "followup_depth": "supportive",
        "pressure_style": "guided discovery",
        "encouragement_level": 0.95,
        "signature_patterns": [
            "Great thinking! Let's build on that...",
            "I like your approach. What about...",
            "You're on the right track. Let me ask you this...",
            "Interesting perspective! How would you expand on that?",
        ],
    },
    "SKEPTICAL_ARCHITECT": {
        "name_prefixes": ["Drew", "Casey", "Quinn", "Morgan", "Avery"],
        "role_titles": ["Solution Architect", "Principal Architect", "Systems Architect"],
        "speaking_style": "probing",
        "warmth": 0.3,
        "strictness": 0.85,
        "interruption_frequency": 0.5,
        "pacing": "deliberate",
        "followup_depth": "deep",
        "pressure_style": "architectural stress test",
        "encouragement_level": 0.2,
        "signature_patterns": [
            "That's one approach. What's the alternative?",
            "How does this handle failure?",
            "What's your migration strategy?",
            "I see several problems with that approach...",
        ],
    },
}


ROUND_TYPE_TO_PERSONA_MAP = {
    "TECHNICAL": ["FAANG_INTERVIEWER", "PRINCIPAL_ENGINEER", "FRIENDLY_MENTOR", "SKEPTICAL_ARCHITECT"],
    "BEHAVIORAL": ["BEHAVIORAL_SPECIALIST", "HR_RECRUITER", "FRIENDLY_MENTOR"],
    "SYSTEM_DESIGN": ["PRINCIPAL_ENGINEER", "SKEPTICAL_ARCHITECT", "FAANG_INTERVIEWER"],
    "ARCHITECTURE": ["SKEPTICAL_ARCHITECT", "PRINCIPAL_ENGINEER", "FAANG_INTERVIEWER"],
    "HIRING_BAR": ["BAR_RAISER", "PRINCIPAL_ENGINEER"],
    "CODING": ["FAANG_INTERVIEWER", "FRIENDLY_MENTOR"],
    "CULTURE_FIT": ["HR_RECRUITER", "BEHAVIORAL_SPECIALIST"],
    "HR": ["HR_RECRUITER"],
}


def generate_persona(
    round_type: str,
    company_signals: dict,
    strategy: dict,
) -> dict:
    candidate_types = ROUND_TYPE_TO_PERSONA_MAP.get(round_type, ["FAANG_INTERVIEWER"])
    persona_type = random.choice(candidate_types)

    template = PERSONA_TEMPLATES[persona_type]
    name = random.choice(template["name_prefixes"])
    role = random.choice(template["role_titles"])

    persona = {
        "name": name,
        "role": role,
        "persona_type": persona_type,
        "speaking_style": template["speaking_style"],
        "warmth": template["warmth"],
        "strictness": template["strictness"],
        "interruption_frequency": template["interruption_frequency"],
        "pacing": template["pacing"],
        "followup_depth": template["followup_depth"],
        "pressure_style": template["pressure_style"],
        "encouragement_level": template["encouragement_level"],
        "signature_patterns": template["signature_patterns"],
    }

    strategy_pressure = strategy.get("pressure_level", "MEDIUM")
    if strategy_pressure == "HIGH":
        persona["warmth"] = max(0.1, persona["warmth"] - 0.2)
        persona["interruption_frequency"] = min(1.0, persona["interruption_frequency"] + 0.1)

    company_style = company_signals.get("company_style", "STANDARD")
    if company_style == "BIG_TECH":
        persona["strictness"] = min(1.0, persona["strictness"] + 0.1)
    elif company_style == "STARTUP":
        persona["pacing"] = "fast"

    return persona
