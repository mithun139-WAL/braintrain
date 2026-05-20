"""
Question Bank router — HTTP layer for question bank CRUD.

All routes are JWT-protected.
Route prefix /question-bank is applied when mounted in main.py.

Routes:
  POST /question-bank                                — create a question
  GET  /question-bank?topicId=...                   — list questions for a topic
  GET  /question-bank/{id}                          — get a question by ID
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Query

from app.deps import CurrentUser, DBSession
from app.modules.question_bank import service
from app.modules.question_bank.schemas import (
    CreateQuestionBankRequest,
    QuestionBankResponse,
)

router = APIRouter()


@router.post("", response_model=QuestionBankResponse, status_code=201)
async def create_question(
    body: CreateQuestionBankRequest, current_user: CurrentUser, db: DBSession
):
    return await service.create_question(db, body, current_user.id)


@router.get("", response_model=list[QuestionBankResponse])
async def list_questions(
    current_user: CurrentUser,
    db: DBSession,
    topic_id: uuid.UUID = Query(..., alias="topicId"),
    interview_type: Optional[str] = Query(None, alias="interviewType"),
    difficulty: Optional[str] = Query(None),
):
    return await service.list_questions(
        db,
        topic_id=topic_id,
        user_id=current_user.id,
        interview_type=interview_type,
        difficulty=difficulty,
    )


@router.get("/{question_id}", response_model=QuestionBankResponse)
async def get_by_id(
    question_id: uuid.UUID, current_user: CurrentUser, db: DBSession
):
    return await service.get_by_id(db, question_id)
