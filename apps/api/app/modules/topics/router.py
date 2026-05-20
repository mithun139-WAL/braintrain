"""
Topics router — HTTP layer for topic CRUD.

All routes are JWT-protected (CurrentUser dependency).
Route prefix /topics is applied when this router is mounted in main.py.

Routes:
  GET    /topics          — list all accessible topics (global + user-owned)
  POST   /topics          — create a new user-owned topic
  GET    /topics/{id}     — get a single accessible topic by ID
  DELETE /topics/{id}     — soft-delete a user-owned topic
"""
import uuid

from fastapi import APIRouter

from app.deps import CurrentUser, DBSession
from app.modules.topics import service
from app.modules.topics.schemas import (
    CreateTopicRequest,
    MessageResponse,
    TopicResponse,
)

router = APIRouter()


@router.get("", response_model=list[TopicResponse])
async def list_topics(current_user: CurrentUser, db: DBSession):
    return await service.list_topics(db, current_user.id)


@router.post("", response_model=TopicResponse, status_code=201)
async def create_topic(
    body: CreateTopicRequest, current_user: CurrentUser, db: DBSession
):
    return await service.create_topic(db, body, current_user.id)


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: uuid.UUID, current_user: CurrentUser, db: DBSession
):
    return await service.get_topic(db, topic_id, current_user.id)


@router.delete("/{topic_id}", response_model=MessageResponse)
async def delete_topic(
    topic_id: uuid.UUID, current_user: CurrentUser, db: DBSession
):
    return await service.delete_topic(db, topic_id, current_user.id)
