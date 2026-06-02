from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


# ── Agent Persona Schemas ─────────────────────────────────────────────────────

class AgentPersonaBase(BaseModel):
    name: str = Field(..., description="Unique name of the persona")
    archetype: str = Field(..., description="Interviewer archetype (e.g., Skeptical Architect)")
    pacing_speed: float = Field(1.0, ge=0.5, le=1.5)
    interruption_frequency: float = Field(0.5, ge=0.0, le=1.0)
    silence_tolerance: float = Field(1.0, ge=0.1, le=5.0)
    skepticism_level: float = Field(0.5, ge=0.0, le=1.0)
    technical_depth: float = Field(0.5, ge=0.0, le=1.0)
    followup_aggressiveness: float = Field(0.5, ge=0.0, le=1.0)
    verbosity_tolerance: float = Field(0.5, ge=0.0, le=1.0)
    ambiguity_tolerance: float = Field(0.5, ge=0.0, le=1.0)
    pressure_intensity: float = Field(0.5, ge=0.0, le=1.0)
    conversational_warmth: float = Field(0.5, ge=0.0, le=1.0)
    challenge_escalation: str = Field("Standard")
    acknowledgment_patterns: List[str] = Field(default_factory=list)
    custom_prompts: Dict[str, str] = Field(default_factory=dict)


class AgentPersonaCreate(AgentPersonaBase):
    pass


class AgentPersonaUpdate(BaseModel):
    name: Optional[str] = None
    archetype: Optional[str] = None
    pacing_speed: Optional[float] = Field(None, ge=0.5, le=1.5)
    interruption_frequency: Optional[float] = Field(None, ge=0.0, le=1.0)
    silence_tolerance: Optional[float] = Field(None, ge=0.1, le=5.0)
    skepticism_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    technical_depth: Optional[float] = Field(None, ge=0.0, le=1.0)
    followup_aggressiveness: Optional[float] = Field(None, ge=0.0, le=1.0)
    verbosity_tolerance: Optional[float] = Field(None, ge=0.0, le=1.0)
    ambiguity_tolerance: Optional[float] = Field(None, ge=0.0, le=1.0)
    pressure_intensity: Optional[float] = Field(None, ge=0.0, le=1.0)
    conversational_warmth: Optional[float] = Field(None, ge=0.0, le=1.0)
    challenge_escalation: Optional[str] = None
    acknowledgment_patterns: Optional[List[str]] = None
    custom_prompts: Optional[Dict[str, str]] = None


class AgentPersonaResponse(AgentPersonaBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Knowledge Document Schemas ───────────────────────────────────────────────

class KnowledgeDocumentBase(BaseModel):
    title: str = Field(..., description="Document title")
    source: str = Field(..., description="Source URL or filename/path")
    source_type: str = Field(..., description="Format: markdown, pdf, yaml, json, txt")
    domain: str = Field(..., description="Domain: frontend, backend, system_design, behavioral, interview_experience, company_rubric")
    topic: str = Field(..., description="Topic: react, aws, distributed_systems, leadership, google, amazon")
    difficulty: str = Field("MEDIUM", description="Target difficulty: EASY, MEDIUM, HARD")
    content: str = Field(..., description="Raw text/markdown document content")
    meta_data: Dict[str, Any] = Field(default_factory=dict, description="Metadata key-values")


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    pass


class KnowledgeDocumentUpdate(BaseModel):
    title: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    domain: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    content: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class KnowledgeDocumentResponse(KnowledgeDocumentBase):
    id: uuid.UUID
    chunk_count: int
    token_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Job Role Comparison Schemas ───────────────────────────────────────────────

class JobAnalysisRequest(BaseModel):
    role_title: str = Field(..., description="Job role title to compare")
    job_description: str = Field(..., description="Full job description text")


class SimilarRoleInfo(BaseModel):
    id: uuid.UUID
    role_title: str
    company_name: Optional[str] = None


class JobAnalysisResponse(BaseModel):
    input_role_title: str
    common_skills: List[str] = Field(default_factory=list, description="Common skills standard for this role type")
    unique_skills: List[str] = Field(default_factory=list, description="Unique skills specific to this job description")
    similar_roles_compared: List[SimilarRoleInfo] = Field(default_factory=list, description="List of similar roles compared in the database")


class CareerProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    current_role: str
    target_role: str
    resume_filename: Optional[str] = None
    linkedin_filename: Optional[str] = None
    naukri_filename: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    analysis_result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


