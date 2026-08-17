"""
Dynamic Round Generator — creates realistic interview rounds based on
resume analysis, JD analysis, and company context following the 5-stage image flow.
"""

def generate_rounds(
    resume_analysis: dict,
    jd_analysis: dict,
    company_signals: dict,
) -> list[dict]:
    builders = [
        _build_technical_screen_round,
        _build_coding_round,
        _build_system_design_round,
        _build_behavioral_round,
        _build_ai_fluency_round,
    ]
    rounds = []
    for builder in builders:
        round_data = builder(resume_analysis, jd_analysis, company_signals)
        rounds.append(round_data)

    _enrich_rounds_with_context(rounds, resume_analysis, jd_analysis)
    return rounds


def _build_technical_screen_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    role_category = jd_analysis.get("role_category", "GENERAL")
    must_have = jd_analysis.get("must_have_skills", [])
    
    relevant_techs = [s for s in must_have if len(s.split()) <= 2][:3]
    if not relevant_techs:
        relevant_techs = ["core programming tools"]

    areas = [
        "CS fundamentals",
        "Role fit and experience walkthrough",
        "Interview readiness and basic skills",
    ]
    if role_category == "FRONTEND":
        areas.extend(["CSS/DOM basics", "JavaScript core concepts"])
    elif role_category == "BACKEND":
        areas.extend(["Databases/SQL basics", "HTTP/API structure"])
    elif role_category == "FULLSTACK":
        areas.extend(["Frontend/Backend basics", "HTTP/Web fundamentals"])
    else:
        areas.extend(["Basic software engineering principles"])
    
    areas.extend(relevant_techs)

    return {
        "name": "Technical Screen",
        "round_type": "RECRUITER_SCREEN",
        "focus": {
            "areas": areas,
        },
        "difficulty": "EASY",
        "estimated_duration_minutes": 30,
        "goals": [
            "Assess core CS fundamentals and role readiness",
            "Verify experience matching the job description",
            "Evaluate communication skills and high-level technical grounding",
        ],
    }


def _build_coding_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    must_have = jd_analysis.get("must_have_skills", [])
    tech_stack = resume_analysis.get("verified_technologies", [])
    
    lang = "Clean coding language"
    languages = ["Python", "TypeScript", "JavaScript", "Go", "Rust", "Java", "C++", "Ruby", "Kotlin", "Swift"]
    for l in languages:
        if any(l.lower() in skill.lower() for skill in must_have) or any(l.lower() in t.lower() for t in tech_stack):
            lang = l
            break

    areas = [
        "Problem-solving speed",
        "Coding accuracy and style",
        "Data structures and algorithms",
        f"Hands-on implementation in {lang}",
    ]

    return {
        "name": "Coding",
        "round_type": "CODING",
        "focus": {
            "areas": areas,
        },
        "difficulty": "MEDIUM",
        "estimated_duration_minutes": 60,
        "goals": [
            "Verify clean, correct, and bug-free code construction under pressure",
            "Evaluate time complexity and space complexity optimization",
            "Assess edge-case handling and overall problem-solving approach",
        ],
    }


def _build_system_design_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    role_category = jd_analysis.get("role_category", "GENERAL")
    
    areas = ["Scalable system design", "Architecture decisions and trade-offs"]
    if role_category == "FRONTEND":
        areas.extend(["Frontend architecture at scale", "Micro-frontends & state routing", "Performance budget optimization"])
    elif role_category in ("BACKEND", "FULLSTACK"):
        areas.extend(["Distributed systems architecture", "Database selection and caching", "Data consistency & partition tolerance"])
    elif role_category == "DATA":
        areas.extend(["Data pipeline design", "ETL/Batch/Stream processing", "Data warehousing at scale"])
    elif role_category == "DEVOPS":
        areas.extend(["Infrastructure scalability", "CI/CD & high availability", "Observability/alerting architecture"])
    else:
        areas.extend(["High-level component interaction", "API design and data consistency"])

    return {
        "name": "System Design",
        "round_type": "SYSTEM_DESIGN",
        "focus": {
            "areas": areas,
        },
        "difficulty": "HARD",
        "estimated_duration_minutes": 60,
        "goals": [
            "Evaluate ability to design scalable, fault-tolerant, and reliable systems",
            "Verify trade-off analysis and justification of architectural choices",
            "Assess data flow and boundary component design matching JD complexity",
        ],
    }


def _build_behavioral_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    culture = jd_analysis.get("culture_style", "STANDARD")
    areas = [
        "STAR method storytelling",
        "Leadership and collaboration",
        "Conflict resolution and team dynamics",
    ]
    if culture == "STARTUP":
        areas.extend(["Handling ambiguity", "Pace of delivery & rapid ownership"])
    elif culture == "ENTERPRISE":
        areas.extend(["Process-driven execution", "Compliance and stability focus"])
    else:
        areas.extend(["Career motivation", "Ownership and accountability"])

    return {
        "name": "Behavioral",
        "round_type": "BEHAVIORAL",
        "focus": {
            "areas": areas,
            "style_specific": culture,
        },
        "difficulty": "MEDIUM",
        "estimated_duration_minutes": 45,
        "goals": [
            "Assess team and culture fit based on past actions",
            "Evaluate candidate's communication style and self-reflection",
            "Verify STAR format structure (Situation, Task, Action, Result) in storytelling",
        ],
    }


def _build_ai_fluency_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    tech_stack = resume_analysis.get("verified_technologies", [])
    primary_tech = tech_stack[0] if tech_stack else "modern software frameworks"
    
    areas = [
        "Building with AI APIs (e.g. Gemini, OpenAI)",
        "Prompt engineering techniques",
        "AI-assisted code generation & debugging",
        f"Integrating AI tools with {primary_tech}",
    ]

    return {
        "name": "AI Fluency",
        "round_type": "AI_FLUENCY",
        "focus": {
            "areas": areas,
        },
        "difficulty": "MEDIUM",
        "estimated_duration_minutes": 30,
        "goals": [
            "Verify ability to leverage AI agents & tools to improve development speed",
            "Assess prompt engineering capabilities and model steering",
            "Evaluate understanding of LLM application design pattern trade-offs",
        ],
    }


def _enrich_rounds_with_context(
    rounds: list[dict],
    resume_analysis: dict,
    jd_analysis: dict,
) -> None:
    tech_stack = resume_analysis.get("verified_technologies", [])
    for round_data in rounds:
        round_focus = round_data.get("focus", {})
        areas = round_focus.get("areas", [])
        if tech_stack and areas:
            round_focus["relevant_technologies"] = [
                t for t in tech_stack
                if any(a.lower() in t.lower() or t.lower() in a.lower() for a in areas)
            ][:5]
