"""
SQLAlchemy database model for Agent Personas.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentPersona(Base):
    """
    SQLAlchemy database model representing interviewer personas.
    """
    __tablename__ = "agent_personas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    archetype: Mapped[str] = mapped_column(String, nullable=False)
    pacing_speed: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    interruption_frequency: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    silence_tolerance: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    skepticism_level: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    technical_depth: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    followup_aggressiveness: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    verbosity_tolerance: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    ambiguity_tolerance: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    pressure_intensity: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    conversational_warmth: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    challenge_escalation: Mapped[str] = mapped_column(String, default="Standard", nullable=False)
    acknowledgment_patterns: Mapped[list] = mapped_column(JSONB, default=list, server_default='[]', nullable=False)
    custom_prompts: Mapped[dict] = mapped_column(JSONB, default=dict, server_default='{}', nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AgentPersona id={self.id} name='{self.name}' archetype='{self.archetype}'>"
