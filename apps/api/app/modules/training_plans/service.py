"""
Training plans service — AI-generated 7-day improvement plans.

Generation logic:
  1. Load the most recent evaluation report for the user
  2. Identify the weakest dimension
  3. Generate 7 days × 2 tasks = 14 micro-exercises targeting that dimension
  4. Supersede any existing ACTIVE plan

In stub mode: returns a fixed but realistic plan template.
"""
import uuid
import logging
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.training_plans import repository as repo
from app.modules.training_plans.schemas import (
    CompleteTaskResponse,
    TrainingPlanListResponse,
    TrainingPlanResponse,
    TrainingTaskResponse,
)

logger = logging.getLogger(__name__)

# ── exercise_type → TaskType mapping ──────────────────────────────────────────

_EXERCISE_TO_TASK_TYPE = {
    "mirror_practice": "PRACTICE",
    "recording":       "DRILL",
    "writing":         "REFLECTION",
    "voice_exercise":  "EXERCISE",
}

# ── Per-exercise generic instructions ─────────────────────────────────────────

_INSTRUCTIONS: dict[str, List[str]] = {
    "mirror_practice": [
        "Find a quiet space with a mirror or an open camera feed.",
        "Read the exercise description carefully before starting.",
        "Perform the exercise as described — stay focused on the specific goal.",
        "Repeat at least twice, noting what improves each time.",
    ],
    "recording": [
        "Set up your recording device in a quiet, well-lit space.",
        "Read the exercise description carefully before starting.",
        "Record yourself completing the task in a single take — no pausing.",
        "Play back immediately and note one thing that went well and one to improve.",
        "Record a second take applying that improvement.",
    ],
    "writing": [
        "Open a document, notes app, or notebook.",
        "Read the exercise description carefully before starting.",
        "Write your first draft without editing or second-guessing yourself.",
        "Review once for clarity — remove filler words and vague phrases.",
        "Save your response; you may want to revisit it later in the week.",
    ],
    "voice_exercise": [
        "Find a quiet space where you can speak aloud without distraction.",
        "Take three slow, deep breaths to relax your voice and body.",
        "Read the exercise description carefully before starting.",
        "Perform the exercise out loud as described.",
        "Repeat at least twice, focusing on consistency and projection.",
    ],
}

_SUCCESS_CRITERIA: dict[str, str] = {
    "mirror_practice": "You notice a visible improvement in posture, eye contact, or composure by your second or third repetition.",
    "recording":       "On playback, you can identify at least one clear, specific improvement compared to your first take.",
    "writing":         "Your written response is structured, direct, and free of vague or filler language.",
    "voice_exercise":  "Your voice sounds steady, projected, and confident throughout the entire exercise.",
}

# ── Stub plan templates ────────────────────────────────────────────────────────

_TASK_TEMPLATES = {
    "confidence": [
        ("Power Stance Practice", "Stand in a power pose for 2 minutes before answering. Record yourself and note your posture and eye contact.", "mirror_practice", 5),
        ("Slow Down Drill", "Answer a practice question at 70% of your normal speed. Record it and review.", "recording", 10),
        ("Pause & Breathe", "Before every sentence, take one deliberate breath. Do this for a full 5-minute answer.", "mirror_practice", 5),
        ("Vocal Projection", "Read a paragraph aloud projecting your voice to the back of the room. Repeat 3 times.", "voice_exercise", 10),
        ("Eye Contact Practice", "Have a 3-minute conversation maintaining eye contact for 80% of the time.", "mirror_practice", 5),
        ("Affirmation Reset", "Write 3 specific things you did well in your last interview. Read them aloud.", "writing", 5),
        ("Cold Open Practice", "Answer a question without any warm-up. Aim to sound confident from the first word.", "recording", 10),
        ("Filler Word Audit", "Record a 2-minute answer. Count every 'um', 'uh', 'like'. Your goal: reduce by 50%.", "recording", 10),
        ("Momentum Builder", "Answer 5 questions in a row without stopping. Focus on energy, not perfection.", "mirror_practice", 15),
        ("Confident Closer", "Practice ending every answer with a strong, direct concluding sentence.", "recording", 10),
        ("Posture Check", "Sit straight, shoulders back, and record a 3-minute answer. Notice the difference.", "recording", 10),
        ("Volume Control", "Answer a question at 3 different volume levels. Find your confident baseline.", "voice_exercise", 10),
        ("Speed Variation", "Practice the same answer at fast, medium, and slow speeds. Pick the most impactful.", "recording", 15),
        ("Performance Review", "Watch all your recordings from this week. Write 3 specific improvements you see.", "writing", 15),
    ],
    "clarity": [
        ("One-Sentence Summary", "For every answer, start with a single sentence that captures the full point.", "writing", 10),
        ("SBI Framework", "Practice Situation-Behavior-Impact for 3 behavioral questions.", "writing", 15),
        ("Jargon Audit", "Rewrite a technical answer removing all jargon. Explain it to a 10-year-old.", "writing", 10),
        ("Headline First", "State your conclusion before your reasoning. Reverse your natural order.", "mirror_practice", 10),
        ("Three-Point Rule", "Structure every answer with exactly three supporting points. No more, no less.", "mirror_practice", 10),
        ("Active Voice Drill", "Rewrite 5 passive sentences ('was done by me') as active ('I did').", "writing", 10),
        ("Complexity Ladder", "Explain one concept at 3 levels: expert, manager, child.", "writing", 15),
        ("Transition Words", "Practice using 'First', 'Additionally', 'Therefore', 'In summary' in your answers.", "mirror_practice", 10),
        ("Cut the Qualifiers", "Answer without using 'sort of', 'kind of', 'maybe', 'I think'. Be definitive.", "recording", 10),
        ("Analogy Practice", "Explain a complex concept using an everyday analogy.", "writing", 15),
        ("Edit Pass", "Record an answer, transcribe it, then edit the transcript for maximum clarity.", "recording", 20),
        ("Precision Vocabulary", "Replace 3 vague words ('good', 'nice', 'thing') with precise alternatives.", "writing", 10),
        ("Flow Check", "Read your answer aloud and pause at every comma. Fix anything that doesn't flow.", "recording", 15),
        ("Final Polish", "Record your best answer of the week. Compare it to Day 1. Write what changed.", "writing", 15),
    ],
    "technical": [
        ("Core Concept Review", "Write a 200-word explanation of your strongest technical concept from memory.", "writing", 15),
        ("System Design Sketch", "Draw a basic system architecture for a feature you've built. Explain each layer.", "writing", 15),
        ("Trade-off Analysis", "Pick a technical decision. Write 3 pros and 3 cons. Which would you choose today?", "writing", 10),
        ("Rubber Duck Debug", "Explain a past bug you fixed to a rubber duck (or a friend). Step by step.", "mirror_practice", 15),
        ("Algorithm Walkthrough", "Trace through a sorting algorithm step-by-step on paper. Explain the Big-O.", "writing", 15),
        ("Database Design", "Design a schema for a feature. Consider normalization and query performance.", "writing", 20),
        ("API Design Practice", "Design a RESTful API for a given feature. Write the endpoints and payloads.", "writing", 15),
        ("Code Review", "Review a piece of your old code. What would you change today and why?", "writing", 15),
        ("Failure Analysis", "Write a post-mortem for a technical failure. Root cause, impact, prevention.", "writing", 20),
        ("Concept Contrast", "Compare two similar technologies (REST vs GraphQL, SQL vs NoSQL). When to use each.", "writing", 15),
        ("Live Coding Prep", "Solve one LeetCode medium problem with a verbal explanation while coding.", "recording", 30),
        ("Architecture Critique", "Find a public system design case study. Critique the architecture choices.", "writing", 20),
        ("Scalability Drill", "Take any feature and design it to handle 100x traffic. What changes?", "writing", 15),
        ("Week Synthesis", "Write a 1-page technical summary of everything you practiced this week.", "writing", 20),
    ],
    "general": [
        ("STAR Warm-Up", "Answer one behavioral question using STAR format. Time yourself to stay under 2 minutes.", "recording", 10),
        ("Strength Inventory", "List your top 5 professional strengths with specific examples for each.", "writing", 15),
        ("Question Bank Review", "Write 5 questions you're most afraid of being asked. Practice each once.", "writing", 20),
        ("Active Listening", "In your next conversation, focus 100% on listening. Summarize back what you heard.", "mirror_practice", 15),
        ("Story Library", "Write 3 impactful professional stories you can adapt for different questions.", "writing", 20),
        ("Body Language Audit", "Record yourself and note: posture, hand gestures, eye contact, facial expression.", "recording", 15),
        ("Research Prep", "Research the company and role for a mock interview. Prepare 3 specific questions.", "writing", 20),
        ("Pressure Test", "Ask a friend to give you a difficult follow-up question after every answer.", "mirror_practice", 20),
        ("Energy Management", "Do 5 minutes of movement before a mock interview. Note the difference in energy.", "mirror_practice", 10),
        ("Feedback Collection", "Ask someone who knows your work to describe your top 3 strengths and 1 weakness.", "writing", 15),
        ("Mock Interview", "Complete a full 30-minute mock interview with timed questions.", "recording", 30),
        ("Debrief Practice", "After a mock interview, write what went well and what to improve. Be specific.", "writing", 15),
        ("Mindset Reset", "Write your professional vision: where you want to be in 3 years. Make it vivid.", "writing", 15),
        ("Final Performance Review", "Watch your best recording from this week. Write your 3 biggest improvements.", "writing", 15),
    ],
}

# ── Helpers ────────────────────────────────────────────────────────────────────


def _difficulty_for_day(day_number: int) -> str:
    """Ramp difficulty across the 7-day plan."""
    if day_number <= 2:
        return "BEGINNER"
    if day_number <= 5:
        return "INTERMEDIATE"
    return "ADVANCED"


def _status_for_frontend(status: str) -> str:
    """Map DB status values to the frontend enum."""
    if status == "SUPERSEDED":
        return "ARCHIVED"
    return status  # ACTIVE | COMPLETED pass through


def _build_task_response(task, focus_area: str) -> TrainingTaskResponse:
    exercise_type = task.exercise_type or "writing"
    return TrainingTaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        task_type=_EXERCISE_TO_TASK_TYPE.get(exercise_type, "EXERCISE"),
        focus_area=focus_area,
        duration_minutes=task.estimated_minutes,
        difficulty=_difficulty_for_day(task.day_number),
        completed=task.is_completed,
        completed_at=task.completed_at,
        instructions=_INSTRUCTIONS.get(exercise_type, _INSTRUCTIONS["writing"]),
        success_criteria=_SUCCESS_CRITERIA.get(exercise_type, ""),
    )


def _build_plan_response(plan) -> TrainingPlanResponse:
    focus = plan.focus_dimension or "general"
    tasks = sorted(plan.tasks, key=lambda t: (t.day_number, t.sequence_order))
    completed = sum(1 for t in tasks if t.is_completed)
    total = len(tasks)
    pct = round((completed / total) * 100, 1) if total else 0.0
    return TrainingPlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        status=_status_for_frontend(plan.status),
        focus_areas=[focus],
        ai_reasoning=plan.summary or "",
        generated_at=plan.created_at,
        expires_at=plan.end_date,
        tasks=[_build_task_response(t, focus) for t in tasks],
        completed_task_count=completed,
        total_task_count=total,
        completion_percentage=pct,
    )


def _determine_focus(evaluation_report) -> str:
    """Pick the weakest non-zero dimension from an evaluation report."""
    if not evaluation_report:
        return "general"
    dims: dict[str, float] = {
        "confidence": evaluation_report.confidence_score or 0,
        "clarity":    evaluation_report.clarity_score    or 0,
    }
    # Only include technical if it was evaluated for this session
    if evaluation_report.technical_score:
        dims["technical"] = evaluation_report.technical_score
    if not any(dims.values()):
        return "general"
    return min(dims, key=lambda k: dims[k])


# ── Encouragement messages ─────────────────────────────────────────────────────

_ENCOURAGEMENT = {
    "BEGINNER":     "Great start! Consistency is everything — come back tomorrow.",
    "INTERMEDIATE": "You're building momentum. Every rep compounds.",
    "ADVANCED":     "Elite territory. You're doing what most candidates never will.",
}


# ── Public service methods ─────────────────────────────────────────────────────


async def generate_plan(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: Optional[uuid.UUID] = None,
) -> TrainingPlanResponse:
    """Generate a new 7-day training plan and supersede any existing active plan."""
    focus_dimension = "general"
    source_session_id = session_id

    if session_id:
        from sqlalchemy import select
        from app.db.models.evaluation_report import EvaluationReport
        result = await db.execute(
            select(EvaluationReport).where(EvaluationReport.session_id == session_id)
        )
        report = result.scalar_one_or_none()
        if report:
            focus_dimension = _determine_focus(report)
    else:
        # Use most recent evaluation report across all of this user's sessions
        from sqlalchemy import select
        from app.db.models.evaluation_report import EvaluationReport
        from app.db.models.interview_session import InterviewSession
        result = await db.execute(
            select(EvaluationReport)
            .join(InterviewSession, EvaluationReport.session_id == InterviewSession.id)
            .where(InterviewSession.user_id == user_id)
            .order_by(EvaluationReport.created_at.desc())   # ← was evaluated_at (bug fixed)
            .limit(1)
        )
        report = result.scalar_one_or_none()
        if report:
            focus_dimension = _determine_focus(report)
            source_session_id = report.session_id

    # Supersede old active plans
    await repo.supersede_active_plans(db, user_id)

    summary_map = {
        "confidence": "A 7-day plan focused on building vocal confidence, reducing hesitation, and projecting authority in high-stakes conversations.",
        "clarity":    "A 7-day plan targeting answer clarity, structured communication, and precision vocabulary for interview excellence.",
        "technical":  "A 7-day technical depth program covering system design, algorithm analysis, and code explanation skills.",
        "general":    "A comprehensive 7-day communication improvement plan covering structure, confidence, clarity, and presence.",
    }
    summary = summary_map.get(focus_dimension, summary_map["general"])

    plan = await repo.create_plan(
        db,
        user_id=user_id,
        focus_dimension=focus_dimension,
        summary=summary,
        source_session_id=source_session_id,
        duration_days=7,
    )

    templates = _TASK_TEMPLATES.get(focus_dimension, _TASK_TEMPLATES["general"])
    task_idx = 0
    for day in range(1, 8):
        for seq in range(1, 3):
            if task_idx < len(templates):
                title, description, exercise_type, est_minutes = templates[task_idx]
                await repo.create_task(
                    db,
                    training_plan_id=plan.id,
                    day_number=day,
                    sequence_order=seq,
                    title=title,
                    description=description,
                    exercise_type=exercise_type,
                    estimated_minutes=est_minutes,
                )
                task_idx += 1

    await db.commit()

    plan = await repo.get_plan(db, plan.id, user_id)
    logger.info("TrainingPlan %s created for user %s (focus: %s)", plan.id, user_id, focus_dimension)
    return _build_plan_response(plan)


async def get_current_plan(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> TrainingPlanResponse:
    plan = await repo.get_active_plan(db, user_id)
    if not plan:
        raise NotFoundException("No active training plan. Generate one first.")
    return _build_plan_response(plan)


async def list_plans(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    limit: int = 10,
) -> TrainingPlanListResponse:
    plans, total = await repo.list_plans(db, user_id, page=page, limit=limit)
    return TrainingPlanListResponse(
        data=[_build_plan_response(p) for p in plans],
        total=total,
    )


async def complete_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
) -> CompleteTaskResponse:
    task = await repo.get_task(db, task_id, user_id)
    if not task:
        raise NotFoundException("Training task not found")

    task = await repo.complete_task(db, task)
    await db.commit()

    # Reload the plan to get updated completion counts
    plan = await repo.get_plan(db, task.training_plan_id, user_id)
    completed = sum(1 for t in plan.tasks if t.is_completed)
    total = len(plan.tasks)
    pct = round((completed / total) * 100, 1) if total else 0.0

    # Pick encouragement based on progress tier
    if pct >= 85:
        tier = "ADVANCED"
    elif pct >= 40:
        tier = "INTERMEDIATE"
    else:
        tier = "BEGINNER"

    return CompleteTaskResponse(
        task=_build_task_response(task, plan.focus_dimension or "general"),
        plan=_build_plan_response(plan),
        message=_ENCOURAGEMENT[tier],
    )
