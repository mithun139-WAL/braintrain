"""
Questions module — Pydantic schemas.

Single route response: the QuestionInstance created for the session.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel


class QuestionResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    content: str
    difficulty: str
    sequence_order: int
    generated_at: datetime

    model_config = {"from_attributes": True}
