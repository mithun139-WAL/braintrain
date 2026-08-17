"""
Journey Orchestrator — orchestrates the entire interview journey lifecycle.

Responsibilities:
- Create sessions from generated rounds
- Inject persona into each session
- Inject verified candidate profile
- Track cross-round memory
- Coordinate round transitions
"""
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.topic import Topic
from app.interview_journey.analyzers.company_signal_extractor import extract_company_signals
from app.interview_journey.analyzers.jd_analyzer import analyze_jd
from app.interview_journey.analyzers.resume_analyzer import analyze_resume
from app.interview_journey.analyzers.verified_profile_builder import build_verified_profile
from app.interview_journey.personas.persona_generator import generate_persona
from app.interview_journey.planners.company_process_researcher import research_company_process
from app.interview_journey.planners.difficulty_mapper import map_difficulty
from app.interview_journey.planners.interview_strategy_generator import generate_strategy
from app.interview_journey.planners.round_generator import generate_rounds
from app.interview_journey.planners.prerequisites_generator import generate_prerequisites
from app.interview_journey.repository import journey_repository as journey_repo
from app.interview_journey.repository import journey_session_repository as jr_session_repo
from app.modules.sessions.repository import create_session as create_interview_session

logger = logging.getLogger(__name__)

_ROUND_TYPE_INTERVIEW_MAP = {
    "TECHNICAL":        "TECHNICAL",
    "SYSTEM_DESIGN":    "TECHNICAL",
    "CODING":           "TECHNICAL",
    "ARCHITECTURE":     "TECHNICAL",
    "HIRING_BAR":       "TECHNICAL",
    "BEHAVIORAL":       "BEHAVIORAL",
    "CULTURE_FIT":      "BEHAVIORAL",
    "HR":               "BEHAVIORAL",
    # New round types added in v1.1 pipeline
    "RECRUITER_SCREEN": "BEHAVIORAL",
    "HM_SCREEN":        "BEHAVIORAL",
    "FOUNDER_SCREEN":   "BEHAVIORAL",
    "PANEL_ROUND":      "TECHNICAL",
    "AI_FLUENCY":       "TECHNICAL",
}



async def analyze_and_plan(
    db: AsyncSession,
    journey_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict:
    journey = await journey_repo.get_journey_by_id(db, journey_id, user_id)
    if not journey:
        raise ValueError("Journey not found")

    resume_analysis = analyze_resume(journey.resume_text)
    jd_analysis = analyze_jd(journey.job_description)
    company_signals = extract_company_signals(journey.company_name, journey.job_description)
    
    if company_signals.get("company_style", "STANDARD") == "STANDARD":
        company_signals["company_style"] = jd_analysis.get("culture_style", "STANDARD")

    verified_profile = build_verified_profile(resume_analysis, jd_analysis, company_signals)

    rounds, process = await generate_pipeline_stages(
        resume_analysis, jd_analysis, company_signals,
        company_name=journey.company_name,
        role_title=journey.role_title,
    )

    prerequisites = await generate_prerequisites(resume_analysis, jd_analysis, company_signals)

    # Delete existing sessions for this journey to prevent duplicates
    await jr_session_repo.delete_journey_sessions(db, journey_id)

    generated_plan = {
        "candidate_level": resume_analysis["candidate_level"],
        "role_category": jd_analysis["role_category"],
        "role_level": jd_analysis["role_level"],
        "strengths": resume_analysis["strengths"],
        "weaknesses": resume_analysis["weaknesses"],
        "rounds": [],
        "prerequisites": prerequisites,
        "process_research": {
            "source": process["source"],
            "confidence": process["confidence"],
            "notes": process["notes"],
        },
    }

    for idx, round_data in enumerate(rounds):
        round_type = round_data["round_type"]
        strategy = generate_strategy(
            candidate_level=resume_analysis["candidate_level"],
            role_level=jd_analysis["role_level"],
            company_signals=company_signals,
            round_type=round_type,
        )
        difficulty = map_difficulty(
            candidate_level=resume_analysis["candidate_level"],
            role_level=jd_analysis["role_level"],
            round_type=round_type,
            company_signals=company_signals,
        )
        persona = generate_persona(round_type, company_signals, strategy)

        enriched_round = {
            **round_data,
            "difficulty": difficulty,
            "strategy": strategy,
        }

        generated_plan["rounds"].append(enriched_round)

        jr_session = await jr_session_repo.create_journey_session(
            db,
            journey_id=journey_id,
            round_name=round_data["name"],
            round_type=round_type,
            interviewer_persona=persona,
            round_focus={
                "focus": round_data.get("focus", {}),
                "strategy": strategy,
                "goals": round_data.get("goals", []),
            },
            difficulty=difficulty,
            order_index=idx,
        )

    await journey_repo.update_journey(
        db,
        journey,
        extracted_skills={
            "technologies": resume_analysis["verified_technologies"],
            "must_have": jd_analysis["must_have_skills"],
            "preferred": jd_analysis["preferred_skills"],
        },
        extracted_signals={
            "resume_analysis": resume_analysis,
            "jd_analysis": jd_analysis,
            "company_signals": company_signals,
            "verified_profile": verified_profile,
        },
        candidate_level=resume_analysis["candidate_level"],
        role_category=jd_analysis["role_category"],
        generated_plan=generated_plan,
        status="ACTIVE",
    )
    await db.commit()

    return {
        "journey_id": str(journey.id),
        "status": "ACTIVE",
        "candidate_level": resume_analysis["candidate_level"],
        "role_category": jd_analysis["role_category"],
        "strengths": resume_analysis["strengths"],
        "weaknesses": resume_analysis["weaknesses"],
        "rounds": generated_plan["rounds"],
        "verified_profile": verified_profile,
        "prerequisites": prerequisites,
    }


async def start_round(
    db: AsyncSession,
    journey_id: uuid.UUID,
    round_index: int,
    user_id: uuid.UUID,
) -> dict:
    journey = await journey_repo.get_journey_by_id(db, journey_id, user_id)
    if not journey:
        raise ValueError("Journey not found")

    sessions = await jr_session_repo.get_journey_sessions(db, journey_id)
    if round_index >= len(sessions):
        raise ValueError(f"Round index {round_index} out of range")

    jr_session = sessions[round_index]
    generated_plan = journey.generated_plan or {}
    rounds = generated_plan.get("rounds", [])
    round_data = rounds[round_index] if round_index < len(rounds) else {}

    extracted_signals = journey.extracted_signals or {}
    verified_profile = extracted_signals.get("verified_profile", {})

    # ── Create an InterviewSession for this round ──────────────────────────
    topic = await _resolve_journey_topic(db)
    round_type = jr_session.round_type or "TECHNICAL"
    interview_type = _ROUND_TYPE_INTERVIEW_MAP.get(round_type, "TECHNICAL")
    duration = round_data.get("estimated_duration_minutes", 45)

    persona = jr_session.interviewer_persona or {}
    personality_config = {
        "journey_context": {
            "journey_id": str(journey.id),
            "journey_session_id": str(jr_session.id),
            "company_name": journey.company_name,
            "role_title": journey.role_title,
            "round_name": jr_session.round_name,
            "round_type": round_type,
            "difficulty": jr_session.difficulty,
            "persona": persona,
            "round_focus": jr_session.round_focus or {},
            "strategy": round_data.get("strategy", {}),
            "verified_candidate_profile": verified_profile,
        }
    }

    interview_session = await create_interview_session(
        db,
        user_id=user_id,
        topic_id=topic.id,
        interview_mode="ONE_ON_ONE_AI",
        interview_type=interview_type,
        difficulty=jr_session.difficulty or "MEDIUM",
        adaptive=True,
        duration_minutes=duration,
        is_voice=True,
        personality_config=personality_config,
    )

    await jr_session_repo.attach_session_id(db, jr_session, interview_session.id)
    await db.commit()

    # ── Build return context ───────────────────────────────────────────────
    session_context = {
        "interview_journey_context": {
            "company_name": journey.company_name,
            "role_title": journey.role_title,
            "round_name": jr_session.round_name,
            "round_type": round_type,
            "round_focus": jr_session.round_focus,
            "verified_candidate_profile": verified_profile,
            "persona": persona,
            "strategy": round_data.get("strategy", {}),
            "difficulty": jr_session.difficulty,
        }
    }

    return {
        "journey_session_id": str(jr_session.id),
        "journey_id": str(journey.id),
        "round_name": jr_session.round_name,
        "round_type": round_type,
        "difficulty": jr_session.difficulty,
        "persona": persona,
        "round_focus": jr_session.round_focus,
        "session_context": session_context,
        "interview_session_id": str(interview_session.id),
    }


async def generate_pipeline_stages(
    resume_analysis: dict,
    jd_analysis: dict,
    company_signals: dict,
    company_name: str | None,
    role_title: str,
) -> tuple[list[dict], dict]:
    """
    Assembles the full interview round sequence for a journey.

    Calls research_company_process to get the stage order (archetype or, when
    search is wired, real company data), then slots rounds from generate_rounds
    into the sequence.

    Returns (rounds, process) so callers can persist process metadata.
    """
    process = await research_company_process(company_name, role_title, company_signals)
    all_rounds = generate_rounds(resume_analysis, jd_analysis, company_signals)
    return all_rounds, process



async def _resolve_journey_topic(db: AsyncSession) -> Topic:
    """Find or create a generic topic for journey-backed interview sessions."""
    result = await db.execute(
        select(Topic).where(
            Topic.is_global == True,
            Topic.name == "Problem Solving & Decision Making",
            Topic.deleted_at.is_(None),
        )
    )
    topic = result.scalar_one_or_none()
    if topic:
        return topic

    result = await db.execute(
        select(Topic).where(
            Topic.is_global == True,
            Topic.deleted_at.is_(None),
        ).limit(1)
    )
    topic = result.scalar_one_or_none()
    if topic:
        return topic

    raise ValueError("No suitable topic found for journey session")


async def complete_round(
    db: AsyncSession,
    journey_session_id: uuid.UUID,
    interview_session_id: uuid.UUID,
) -> dict:
    jr_session = await jr_session_repo.get_journey_session_by_id(db, journey_session_id)
    if not jr_session:
        raise ValueError("Journey session not found")

    await jr_session_repo.attach_session_id(db, jr_session, interview_session_id)
    await jr_session_repo.mark_completed(db, jr_session)
    await db.commit()

    sessions = await jr_session_repo.get_journey_sessions(db, jr_session.journey_id)
    all_completed = all(s.completed for s in sessions)

    if all_completed:
        journey = await journey_repo.get_journey_by_id(
            db, jr_session.journey_id, jr_session.journey.user_id
        )
        if journey:
            await journey_repo.update_journey(db, journey, status="COMPLETED")
            await db.commit()

    return {
        "journey_session_id": str(jr_session.id),
        "completed": True,
        "journey_completed": all_completed,
    }


def build_round_prompt_layers(
    journey_context: dict,
) -> dict:
    verified_profile = journey_context.get("verified_candidate_profile", {})
    persona = journey_context.get("persona", {})
    round_focus = journey_context.get("round_focus", {})

    return {
        "system_rules": _build_system_rules(),
        "round_objective": _build_round_objective(round_focus, journey_context),
        "verified_profile": _build_verified_profile_section(verified_profile),
        "persona": _build_persona_section(persona),
        "conversation_state": "{{conversation_memory}}",
    }


def _build_system_rules() -> str:
    return """## SYSTEM RULES (HARD CONSTRAINTS)

1. Never invent candidate experience — only ask about what's in their verified profile.
2. Stay within the round scope — do not switch domains unexpectedly.
3. Avoid unrelated domains — if this is a frontend round, do not ask backend system design.
4. Ask one question at a time — do not multi-task.
5. Be truthful about the candidate's background — do not fabricate achievements or projects.
6. If the candidate seems confused, clarify rather than changing the subject.
7. Probe weak answers naturally — use follow-ups, not dismissiveness.
8. Adapt pressure level dynamically based on candidate responses."""


def _build_round_objective(round_focus: dict, context: dict) -> str:
    focus = round_focus.get("focus", {})
    areas = focus.get("areas", [])
    goals = round_focus.get("goals", [])
    strategy = round_focus.get("strategy", {})

    lines = ["## ROUND OBJECTIVE", f"Round: {context.get('round_name', 'Unknown')}"]
    lines.append(f"Focus areas: {', '.join(areas)}" if areas else "")
    lines.append(f"Difficulty: {context.get('difficulty', 'MEDIUM')}")
    lines.append("Goals:")
    for goal in goals:
        lines.append(f"- {goal}")
    lines.append(f"\nStrategy: Pressure level = {strategy.get('pressure_level', 'MEDIUM')}, "
                  f"Follow-up intensity = {strategy.get('followup_intensity', 'MEDIUM')}")
    return "\n".join(lines)


def _build_verified_profile_section(profile: dict) -> str:
    lines = ["## VERIFIED CANDIDATE PROFILE", "Only these facts are verified:"]
    skills = profile.get("verified_skills", [])
    if skills:
        lines.append(f"Verified skills: {', '.join(skills)}")
    experiences = profile.get("verified_experiences", [])
    if experiences:
        for exp in experiences:
            title = exp.get("title", "")
            company = exp.get("company", "")
            details = exp.get("details", [])
            lines.append(f"- {title} at {company}")
            if details:
                lines.append(f"  Details: {'; '.join(details[:3])}")
    projects = profile.get("verified_projects", [])
    if projects:
        lines.append("Projects:")
        for proj in projects:
            lines.append(f"- {proj.get('name', 'Unnamed')}")
    unknowns = profile.get("unknowns", [])
    if unknowns:
        lines.append("\nUNKNOWNS (do not assume):")
        for u in unknowns:
            lines.append(f"- {u}")
    return "\n".join(lines)


def _build_persona_section(persona: dict) -> str:
    lines = ["## INTERVIEWER PERSONA"]
    lines.append(f"You are {persona.get('name', 'Interviewer')}, {persona.get('role', 'interviewer')}.")
    lines.append(f"Speaking style: {persona.get('speaking_style', 'professional')}")
    lines.append(f"Pressure style: {persona.get('pressure_style', 'balanced')}")

    warmth = persona.get("warmth", 0.5)
    strictness = persona.get("strictness", 0.5)

    if strictness > 0.7:
        lines.append("Challenge the candidate. Push for depth.")
    if warmth > 0.6:
        lines.append("Be encouraging. Make the candidate feel at ease.")

    patterns = persona.get("signature_patterns", [])
    if patterns:
        lines.append("You tend to say things like:")
        for p in patterns[:3]:
            lines.append(f"- {p}")

    return "\n".join(lines)
