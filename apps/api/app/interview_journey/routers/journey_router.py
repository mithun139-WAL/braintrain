"""
Interview Journey router — API endpoints for the full interview journey feature.

Routes:
  POST   /journeys                     — create a new interview journey
  POST   /journeys/upload-resume       — upload and parse resume file
  POST   /journeys/analyze             — analyze resume + JD, generate plan
  GET    /journeys                     — list user's journeys
  GET    /journeys/{id}                — get journey details
  GET    /journeys/{id}/rounds         — get rounds for a journey
  POST   /journeys/{id}/start-round    — prepare a round for session launch
  POST   /journeys/{id}/complete-round — mark a round as completed
  GET    /journeys/{id}/final-report   — generate final hiring report
"""
import logging
import uuid

from fastapi import APIRouter, File, UploadFile

from app.deps import CurrentUser, DBSession
from app.interview_journey.analyzers.resume_parser import parse_resume
from app.interview_journey.orchestrator import analyze_and_plan, complete_round, start_round
from app.interview_journey.repository import journey_repository as journey_repo
from app.interview_journey.repository import journey_session_repository as jr_session_repo
from app.interview_journey.schemas.journey_schemas import (
    AnalyzeJourneyRequest,
    AnalyzeResponse,
    CompleteRoundRequest,
    CompleteRoundResponse,
    CreateJourneyRequest,
    EditJourneyRequest,
    JourneyFinalReportResponse,
    JourneyListResponse,
    JourneyResponse,
    JourneyRoundResponse,
    StartRoundRequest,
    StartRoundResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=JourneyResponse, status_code=201)
async def create_journey(
    body: CreateJourneyRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    journey = await journey_repo.create_journey(
        db,
        user_id=current_user.id,
        role_title=body.role_title,
        job_description=body.job_description,
        resume_text=body.resume_text,
        company_name=body.company_name,
    )
    await db.commit()

    return JourneyResponse(
        id=journey.id,
        user_id=journey.user_id,
        company_name=journey.company_name,
        role_title=journey.role_title,
        status=journey.status,
        candidate_level=journey.candidate_level,
        role_category=journey.role_category,
        extracted_skills=journey.extracted_skills,
        extracted_signals=journey.extracted_signals,
        generated_plan=journey.generated_plan,
        created_at=journey.created_at,
        updated_at=journey.updated_at,
        sessions=[],
    )


@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
):
    content = await file.read()
    text = parse_resume(content, file.filename or "resume.pdf")
    return {"resume_text": text, "filename": file.filename}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_journey(
    body: AnalyzeJourneyRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    result = await analyze_and_plan(db, body.journey_id, current_user.id)
    return AnalyzeResponse(**result)


@router.get("", response_model=JourneyListResponse)
async def list_journeys(
    current_user: CurrentUser,
    db: DBSession,
    page: int = 1,
    limit: int = 20,
):
    journeys, total = await journey_repo.get_journeys_by_user(
        db, current_user.id, page=page, limit=limit
    )
    return JourneyListResponse(
        data=[
            JourneyResponse(
                id=j.id,
                user_id=j.user_id,
                company_name=j.company_name,
                role_title=j.role_title,
                status=j.status,
                candidate_level=j.candidate_level,
                role_category=j.role_category,
                extracted_skills=j.extracted_skills,
                extracted_signals=j.extracted_signals,
                generated_plan=j.generated_plan,
                created_at=j.created_at,
                updated_at=j.updated_at,
                sessions=[
                    JourneyRoundResponse(
                        id=s.id,
                        round_name=s.round_name,
                        round_type=s.round_type,
                        difficulty=s.difficulty,
                        order_index=s.order_index,
                        completed=s.completed,
                        session_id=s.session_id,
                        interviewer_persona=s.interviewer_persona,
                        round_focus=s.round_focus,
                        created_at=s.created_at,
                    )
                    for s in (j.sessions or [])
                ],
            )
            for j in journeys
        ],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{journey_id}", response_model=JourneyResponse)
async def get_journey(
    journey_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    journey = await journey_repo.get_journey_by_id(db, journey_id, current_user.id)
    if not journey:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Journey not found")
    return JourneyResponse(
        id=journey.id,
        user_id=journey.user_id,
        company_name=journey.company_name,
        role_title=journey.role_title,
        status=journey.status,
        candidate_level=journey.candidate_level,
        role_category=journey.role_category,
        extracted_skills=journey.extracted_skills,
        extracted_signals=journey.extracted_signals,
        generated_plan=journey.generated_plan,
        created_at=journey.created_at,
        updated_at=journey.updated_at,
        sessions=[
            JourneyRoundResponse(
                id=s.id,
                round_name=s.round_name,
                round_type=s.round_type,
                difficulty=s.difficulty,
                order_index=s.order_index,
                completed=s.completed,
                session_id=s.session_id,
                interviewer_persona=s.interviewer_persona,
                round_focus=s.round_focus,
                created_at=s.created_at,
            )
            for s in (journey.sessions or [])
        ],
    )


@router.get("/{journey_id}/rounds", response_model=list[JourneyRoundResponse])
async def get_journey_rounds(
    journey_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    journey = await journey_repo.get_journey_by_id(db, journey_id, current_user.id)
    if not journey:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Journey not found")
    sessions = await jr_session_repo.get_journey_sessions(db, journey_id)
    return [
        JourneyRoundResponse(
            id=s.id,
            round_name=s.round_name,
            round_type=s.round_type,
            difficulty=s.difficulty,
            order_index=s.order_index,
            completed=s.completed,
            session_id=s.session_id,
            interviewer_persona=s.interviewer_persona,
            round_focus=s.round_focus,
            created_at=s.created_at,
        )
        for s in sessions
    ]


@router.post("/{journey_id}/start-round", response_model=StartRoundResponse)
async def start_journey_round(
    journey_id: uuid.UUID,
    body: StartRoundRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    result = await start_round(db, journey_id, body.round_index, current_user.id)
    return StartRoundResponse(**result)


@router.post("/{journey_id}/complete-round", response_model=CompleteRoundResponse)
async def complete_journey_round(
    journey_id: uuid.UUID,
    body: CompleteRoundRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    result = await complete_round(db, body.journey_session_id, body.interview_session_id)
    return CompleteRoundResponse(**result)


@router.get("/{journey_id}/final-report", response_model=JourneyFinalReportResponse)
async def get_final_report(
    journey_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    journey = await journey_repo.get_journey_by_id(db, journey_id, current_user.id)
    if not journey:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Journey not found")

    from app.interview_journey.final_report_generator import generate_final_report
    report = generate_final_report(journey)
    return JourneyFinalReportResponse(**report)


@router.patch("/{journey_id}", response_model=JourneyResponse)
async def edit_journey(
    journey_id: uuid.UUID,
    body: EditJourneyRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    journey = await journey_repo.get_journey_by_id(db, journey_id, current_user.id)
    if not journey:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Journey not found")

    update_data = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}

    if update_data:
        await journey_repo.update_journey(db, journey, **update_data)
        await db.commit()

    return JourneyResponse(
        id=journey.id,
        user_id=journey.user_id,
        company_name=journey.company_name,
        role_title=journey.role_title,
        status=journey.status,
        candidate_level=journey.candidate_level,
        role_category=journey.role_category,
        extracted_skills=journey.extracted_skills,
        extracted_signals=journey.extracted_signals,
        generated_plan=journey.generated_plan,
        created_at=journey.created_at,
        updated_at=journey.updated_at,
        sessions=[
            JourneyRoundResponse(
                id=s.id,
                round_name=s.round_name,
                round_type=s.round_type,
                difficulty=s.difficulty,
                order_index=s.order_index,
                completed=s.completed,
                session_id=s.session_id,
                interviewer_persona=s.interviewer_persona,
                round_focus=s.round_focus,
                created_at=s.created_at,
            )
            for s in (journey.sessions or [])
        ],
    )


@router.delete("/{journey_id}", status_code=204)
async def delete_journey(
    journey_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    journey = await journey_repo.get_journey_by_id(db, journey_id, current_user.id)
    if not journey:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Journey not found")

    await journey_repo.delete_journey(db, journey)
    await db.commit()
    return None

