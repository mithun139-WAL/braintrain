"""
Dynamic Round Generator — creates realistic interview rounds based on
resume analysis, JD analysis, and company context.
"""


def generate_rounds(
    resume_analysis: dict,
    jd_analysis: dict,
    company_signals: dict,
) -> list[dict]:
    role_category = jd_analysis.get("role_category", "GENERAL")
    role_level = jd_analysis.get("role_level", "MID")
    candidate_level = resume_analysis.get("candidate_level", "MID")

    rounds = []

    round_builders = _get_round_builders(role_category, role_level, candidate_level)
    for builder in round_builders:
        round_data = builder(resume_analysis, jd_analysis, company_signals)
        rounds.append(round_data)

    _enrich_rounds_with_context(rounds, resume_analysis, jd_analysis)
    return rounds


def _get_round_builders(
    role_category: str,
    role_level: str,
    candidate_level: str,
) -> list:
    builders = [_build_behavioral_round]

    if role_category == "FRONTEND":
        builders.extend([
            _build_frontend_core_round,
            _build_frontend_architecture_round,
            _build_frontend_system_design_round,
        ])
    elif role_category == "BACKEND":
        builders.extend([
            _build_backend_core_round,
            _build_system_design_round,
            _build_backend_deep_dive_round,
        ])
    elif role_category == "FULLSTACK":
        builders.extend([
            _build_frontend_core_round,
            _build_backend_core_round,
            _build_system_design_round,
        ])
    elif role_category == "DATA":
        builders.extend([
            _build_data_core_round,
            _build_system_design_round,
            _build_ml_deep_dive_round,
        ])
    elif role_category == "DEVOPS":
        builders.extend([
            _build_infrastructure_round,
            _build_system_design_round,
            _build_incident_response_round,
        ])
    else:
        builders.extend([
            _build_technical_core_round,
            _build_system_design_round,
        ])

    if role_level in ("SENIOR", "STAFF") or candidate_level in ("SENIOR", "STAFF"):
        builders.append(_build_hiring_bar_round)

    return builders


def _build_behavioral_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    style = jd_analysis.get("culture_style", "STANDARD")
    return {
        "name": "Behavioral & Cultural Fit",
        "round_type": "BEHAVIORAL",
        "focus": {
            "areas": ["leadership", "collaboration", "conflict resolution", "communication"],
            "style_specific": style,
        },
        "difficulty": "MEDIUM",
        "estimated_duration_minutes": 30,
        "goals": [
            "Assess communication clarity",
            "Evaluate collaboration patterns",
            "Understand decision-making process",
            "Gauge cultural alignment",
        ],
    }


def _build_frontend_core_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    return {
        "name": "Frontend Fundamentals",
        "round_type": "TECHNICAL",
        "focus": {
            "areas": [
                "core JavaScript/TypeScript",
                "component architecture",
                "state management",
                "rendering patterns",
                "CSS/styling architecture",
            ],
        },
        "difficulty": "MEDIUM",
        "estimated_duration_minutes": 45,
        "goals": [
            "Verify frontend fundamentals depth",
            "Evaluate component decomposition",
            "Assess state management understanding",
            "Test rendering optimization knowledge",
        ],
    }


def _build_frontend_architecture_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    return {
        "name": "Frontend Architecture",
        "round_type": "ARCHITECTURE",
        "focus": {
            "areas": [
                "application architecture",
                "performance optimization",
                "accessibility",
                "bundling and build systems",
                "error handling patterns",
            ],
        },
        "difficulty": "HARD",
        "estimated_duration_minutes": 60,
        "goals": [
            "Evaluate architectural thinking",
            "Assess performance optimization skills",
            "Test accessibility knowledge",
            "Understand build pipeline experience",
        ],
    }


def _build_frontend_system_design_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    return {
        "name": "Frontend System Design",
        "round_type": "SYSTEM_DESIGN",
        "focus": {
            "areas": [
                "frontend architecture at scale",
                "micro-frontends",
                "caching strategies",
                "performance budgets",
                "monitoring and observability",
            ],
        },
        "difficulty": "HARD",
        "estimated_duration_minutes": 45,
        "goals": [
            "Assess large-scale frontend design",
            "Evaluate trade-off reasoning",
            "Test caching and performance strategy",
        ],
    }


def _build_backend_core_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    return {
        "name": "Backend Engineering",
        "round_type": "TECHNICAL",
        "focus": {
            "areas": [
                "API design",
                "database modeling",
                "performance",
                "error handling",
                "testing strategies",
            ],
        },
        "difficulty": "MEDIUM",
        "estimated_duration_minutes": 45,
        "goals": [
            "Verify backend fundamentals",
            "Evaluate API design decisions",
            "Assess database knowledge",
            "Test error handling patterns",
        ],
    }


def _build_system_design_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    return {
        "name": "System Design",
        "round_type": "SYSTEM_DESIGN",
        "focus": {
            "areas": [
                "distributed systems",
                "scalability",
                "data flow",
                "trade-off analysis",
                "reliability patterns",
            ],
        },
        "difficulty": "HARD",
        "estimated_duration_minutes": 60,
        "goals": [
            "Evaluate system-level thinking",
            "Assess scalability knowledge",
            "Test trade-off articulation",
            "Understand reliability design",
        ],
    }


def _build_backend_deep_dive_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    return {
        "name": "Backend Deep Dive",
        "round_type": "TECHNICAL",
        "focus": {
            "areas": [
                "concurrency",
                "distributed transactions",
                "caching strategies",
                "message queues",
                "observability",
            ],
        },
        "difficulty": "HARD",
        "estimated_duration_minutes": 45,
        "goals": [
            "Evaluate concurrency understanding",
            "Assess distributed systems knowledge",
            "Test caching strategy design",
        ],
    }


def _build_hiring_bar_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    return {
        "name": "Hiring Bar / Leadership",
        "round_type": "HIRING_BAR",
        "focus": {
            "areas": [
                "technical leadership",
                "mentorship",
                "cross-functional influence",
                "technical vision",
                "conflict navigation",
            ],
        },
        "difficulty": "HARD",
        "estimated_duration_minutes": 45,
        "goals": [
            "Assess leadership maturity",
            "Evaluate cross-functional impact",
            "Test technical vision articulation",
            "Gauge conflict resolution approach",
        ],
    }


def _build_data_core_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    return {
        "name": "Data Engineering",
        "round_type": "TECHNICAL",
        "focus": {
            "areas": [
                "data modeling",
                "ETL pipelines",
                "query optimization",
                "data warehousing",
                "data quality",
            ],
        },
        "difficulty": "MEDIUM",
        "estimated_duration_minutes": 45,
        "goals": [
            "Verify data engineering fundamentals",
            "Evaluate pipeline design",
            "Assess data modeling skills",
        ],
    }


def _build_ml_deep_dive_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    return {
        "name": "ML System Design",
        "round_type": "SYSTEM_DESIGN",
        "focus": {
            "areas": [
                "model deployment",
                "feature engineering",
                "training pipelines",
                "model monitoring",
            ],
        },
        "difficulty": "HARD",
        "estimated_duration_minutes": 60,
        "goals": [
            "Evaluate ML system design",
            "Assess production ML knowledge",
            "Test data pipeline understanding",
        ],
    }


def _build_infrastructure_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    return {
        "name": "Infrastructure & Platform",
        "round_type": "TECHNICAL",
        "focus": {
            "areas": [
                "containerization",
                "orchestration",
                "CI/CD pipelines",
                "infrastructure as code",
                "monitoring and alerting",
            ],
        },
        "difficulty": "MEDIUM",
        "estimated_duration_minutes": 45,
        "goals": [
            "Verify infrastructure knowledge",
            "Evaluate CI/CD pipeline design",
            "Assess monitoring strategy",
        ],
    }


def _build_incident_response_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    return {
        "name": "Incident Response & Reliability",
        "round_type": "TECHNICAL",
        "focus": {
            "areas": [
                "incident management",
                "runbooks",
                "post-mortems",
                "SLOs and SLIs",
                "chaos engineering",
            ],
        },
        "difficulty": "HARD",
        "estimated_duration_minutes": 45,
        "goals": [
            "Assess incident response maturity",
            "Evaluate reliability engineering",
            "Test SLO/SLI framework knowledge",
        ],
    }


def _build_technical_core_round(
    resume_analysis: dict, jd_analysis: dict, company_signals: dict
) -> dict:
    return {
        "name": "Technical Core",
        "round_type": "TECHNICAL",
        "focus": {
            "areas": [
                "algorithms and data structures",
                "problem solving",
                "coding",
                "system thinking",
            ],
        },
        "difficulty": "MEDIUM",
        "estimated_duration_minutes": 60,
        "goals": [
            "Evaluate problem-solving approach",
            "Assess coding ability",
            "Test algorithmic thinking",
        ],
    }


def _enrich_rounds_with_context(
    rounds: list[dict],
    resume_analysis: dict,
    jd_analysis: dict,
) -> None:
    tech_stack = resume_analysis.get("verified_technologies", [])
    jd_focus = jd_analysis.get("likely_interview_focus", [])

    for round_data in rounds:
        round_focus = round_data.get("focus", {})
        areas = round_focus.get("areas", [])
        if tech_stack and areas:
            round_focus["relevant_technologies"] = [
                t for t in tech_stack
                if any(a.lower() in t.lower() or t.lower() in a.lower() for a in areas)
            ][:5]
