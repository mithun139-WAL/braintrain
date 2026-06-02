from typing import Annotated, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form

from app.deps import CurrentUser, DBSession
from app.db.models.user import User
from app.modules.knowledge.schemas import (
    AgentPersonaCreate,
    AgentPersonaResponse,
    AgentPersonaUpdate,
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    KnowledgeDocumentUpdate,
    JobAnalysisRequest,
    JobAnalysisResponse,
    CareerProfileResponse,
)
from app.modules.knowledge.service import AgentPersonaService, KnowledgeDocumentService
from app.modules.knowledge.service_optimizer import CareerOptimizerService

router = APIRouter()


# ── Dependency to verify administrator status ──────────────────────────────────

async def get_current_admin_user(current_user: CurrentUser) -> User:
    """
    Dependency that restricts endpoints to admin users.
    Checks plan_type == "ADMIN" or emails containing "admin" or "@braintrain.com".
    """
    email_str = current_user.email or ""
    is_admin_email = (
        "admin" in email_str.lower()
        or email_str.endswith("@braintrain.com")
        or email_str.lower() == "alphahappened139@gmail.com"
    )
    
    if current_user.plan_type.upper() != "ADMIN" and not is_admin_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation is restricted to administrators.",
        )
    return current_user

CurrentAdminUser = Annotated[User, Depends(get_current_admin_user)]


# ── Dependency to verify pro or admin status ──────────────────────────────────

async def get_current_pro_or_admin_user(current_user: CurrentUser) -> User:
    """
    Dependency that restricts endpoints to PRO or ADMIN users.
    """
    email_str = current_user.email or ""
    is_admin_email = (
        "admin" in email_str.lower()
        or email_str.endswith("@braintrain.com")
        or email_str.lower() == "alphahappened139@gmail.com"
    )
    user_plan = (current_user.plan_type or "FREE").upper()
    if user_plan not in ("PRO", "ADMIN") and not is_admin_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature is only available on the PRO or ADMIN plan. Upgrade to access.",
        )
    return current_user

CurrentProOrAdminUser = Annotated[User, Depends(get_current_pro_or_admin_user)]



# ── Agent Persona Routes ──────────────────────────────────────────────────────

@router.get("/personas", response_model=List[AgentPersonaResponse], summary="List all agent personas")
async def list_personas(db: DBSession, current_user: CurrentProOrAdminUser):
    return await AgentPersonaService.get_personas(db)


@router.get("/personas/{name}", response_model=AgentPersonaResponse, summary="Get a specific persona by name")
async def get_persona(name: str, db: DBSession, current_user: CurrentProOrAdminUser):
    persona = await AgentPersonaService.get_persona_by_name(db, name)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{name}' not found."
        )
    return persona


@router.post("/personas", response_model=AgentPersonaResponse, status_code=status.HTTP_201_CREATED, summary="Create a new persona")
async def create_persona(body: AgentPersonaCreate, db: DBSession, current_admin: CurrentAdminUser):
    existing = await AgentPersonaService.get_persona_by_name(db, body.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Persona with name '{body.name}' already exists."
        )
    return await AgentPersonaService.create_persona(db, body)


@router.put("/personas/{name}", response_model=AgentPersonaResponse, summary="Update an existing persona")
async def update_persona(name: str, body: AgentPersonaUpdate, db: DBSession, current_admin: CurrentAdminUser):
    updated = await AgentPersonaService.update_persona(db, name, body)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{name}' not found."
        )
    return updated


@router.delete("/personas/{name}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a persona")
async def delete_persona(name: str, db: DBSession, current_admin: CurrentAdminUser):
    success = await AgentPersonaService.delete_persona(db, name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{name}' not found."
        )
    return None


# ── Knowledge Base Document Routes ───────────────────────────────────────────

@router.get("/documents", response_model=List[KnowledgeDocumentResponse], summary="List all knowledge base documents")
async def list_documents(db: DBSession, current_user: CurrentProOrAdminUser):
    return await KnowledgeDocumentService.get_documents(db)


@router.get("/documents/{id}", response_model=KnowledgeDocumentResponse, summary="Get details of a knowledge document")
async def get_document(id: uuid.UUID, db: DBSession, current_user: CurrentProOrAdminUser):
    doc = await KnowledgeDocumentService.get_document_by_id(db, id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document with ID '{id}' not found."
        )
    return doc


@router.post("/documents", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED, summary="Create and index a knowledge document")
async def create_document(body: KnowledgeDocumentCreate, db: DBSession, current_admin: CurrentAdminUser):
    return await KnowledgeDocumentService.create_document(db, body)


@router.put("/documents/{id}", response_model=KnowledgeDocumentResponse, summary="Update a knowledge document")
async def update_document(id: uuid.UUID, body: KnowledgeDocumentUpdate, db: DBSession, current_admin: CurrentAdminUser):
    updated = await KnowledgeDocumentService.update_document(db, id, body)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document with ID '{id}' not found."
        )
    return updated


@router.delete("/documents/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a knowledge document")
async def delete_document(id: uuid.UUID, db: DBSession, current_admin: CurrentAdminUser):
    success = await KnowledgeDocumentService.delete_document(db, id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document with ID '{id}' not found."
        )
    return None


# ── Job Role Analyzer Route ───────────────────────────────────────────────────

@router.post("/analyze-job", response_model=JobAnalysisResponse, summary="Compare job role and extract common and unique skills")
async def analyze_job(
    body: JobAnalysisRequest,
    db: DBSession,
    current_user: CurrentProOrAdminUser,
):
    """
    Analyzes job title and description by comparing them against similar roles
    stored in the database and returning lists of common and unique skills.
    """
    return await KnowledgeDocumentService.analyze_job_skills(
        db=db,
        role_title=body.role_title,
        job_description=body.job_description,
    )


# ── Career Profile Optimizer Routes ───────────────────────────────────────────

@router.post("/career-optimize", response_model=CareerProfileResponse, status_code=status.HTTP_201_CREATED, summary="Optimize a candidate profile for transition")
async def optimize_candidate_profile(
    db: DBSession,
    current_user: CurrentProOrAdminUser,
    current_role: str = Form(...),
    target_role: str = Form(...),
    resume: Optional[UploadFile] = File(None),
    linkedin_pdf: Optional[UploadFile] = File(None),
    naukri_pdf: Optional[UploadFile] = File(None),
):
    resume_bytes = await resume.read() if resume else None
    resume_filename = resume.filename if resume else None
    
    linkedin_bytes = await linkedin_pdf.read() if linkedin_pdf else None
    linkedin_filename = linkedin_pdf.filename if linkedin_pdf else None
    
    naukri_bytes = await naukri_pdf.read() if naukri_pdf else None
    naukri_filename = naukri_pdf.filename if naukri_pdf else None
    
    return await CareerOptimizerService.optimize_profile(
        db=db,
        user_id=current_user.id,
        current_role=current_role,
        target_role=target_role,
        resume_bytes=resume_bytes,
        resume_filename=resume_filename,
        linkedin_bytes=linkedin_bytes,
        linkedin_filename=linkedin_filename,
        naukri_bytes=naukri_bytes,
        naukri_filename=naukri_filename,
    )


@router.get("/career-optimize/history", response_model=List[CareerProfileResponse], summary="List all user career profile optimizations")
async def list_optimization_history(db: DBSession, current_user: CurrentProOrAdminUser):
    return await CareerOptimizerService.list_history(db, current_user.id)


@router.get("/career-optimize/{id}", response_model=CareerProfileResponse, summary="Get details of a specific optimization run")
async def get_optimization_detail(id: uuid.UUID, db: DBSession, current_user: CurrentProOrAdminUser):
    detail = await CareerOptimizerService.get_by_id(db, id, current_user.id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optimization report with ID '{id}' not found."
        )
    return detail


@router.delete("/career-optimize/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a specific optimization run")
async def delete_optimization(id: uuid.UUID, db: DBSession, current_user: CurrentProOrAdminUser):
    success = await CareerOptimizerService.delete_by_id(db, id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optimization report with ID '{id}' not found."
        )
    return None


