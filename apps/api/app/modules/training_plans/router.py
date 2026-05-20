"""
Training plans router.

Routes:
  POST  /training-plans/generate         generate a new AI training plan
  GET   /training-plans/current          get the user's current active plan
  GET   /training-plans                  list plan history
  POST  /training-plans/tasks/:id/complete  mark a task as done
"""
import uuid
from typing import Optional

from fastapi import APIRouter

from app.deps import CurrentUser, DBSession
from app.modules.training_plans import service
from app.modules.training_plans.schemas import (
    CompleteTaskResponse,
    GeneratePlanRequest,
    TrainingPlanListResponse,
    TrainingPlanResponse,
)

router = APIRouter()


@router.post(
    "/generate",
    response_model=TrainingPlanResponse,
    status_code=201,
    summary="Generate a new 7-day AI training plan",
)
async def generate_plan(
    body: GeneratePlanRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> TrainingPlanResponse:
    return await service.generate_plan(db, current_user.id, session_id=body.session_id)


@router.get(
    "/current",
    response_model=TrainingPlanResponse,
    status_code=200,
    summary="Get the current active training plan",
)
async def get_current_plan(
    db: DBSession,
    current_user: CurrentUser,
) -> TrainingPlanResponse:
    return await service.get_current_plan(db, current_user.id)


@router.get(
    "",
    response_model=TrainingPlanListResponse,
    status_code=200,
    summary="List the user's training plan history",
)
async def list_plans(
    db: DBSession,
    current_user: CurrentUser,
    page: int = 1,
    limit: int = 10,
) -> TrainingPlanListResponse:
    return await service.list_plans(db, current_user.id, page=page, limit=limit)


@router.post(
    "/tasks/{task_id}/complete",
    response_model=CompleteTaskResponse,
    status_code=200,
    summary="Mark a training task as completed",
)
async def complete_task(
    task_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> CompleteTaskResponse:
    return await service.complete_task(db, task_id, current_user.id)
