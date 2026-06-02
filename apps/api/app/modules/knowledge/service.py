import uuid
import logging
from typing import List, Optional
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.agent_persona import AgentPersona
from app.db.models.knowledge_document import KnowledgeDocument
from app.db.models.knowledge_chunk import KnowledgeChunk
from app.db.models.interview_journey import InterviewJourney
from app.ai.voice.memory.memory_encoder import MemoryEncoder
from app.modules.knowledge.schemas import (
    AgentPersonaCreate,
    AgentPersonaUpdate,
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
)

logger = logging.getLogger("knowledge_service")



# ── Text Chunking Helper ──────────────────────────────────────────────────────

def split_content_into_chunks(text: str, chunk_size_words: int = 250, overlap_words: int = 50) -> List[str]:
    """
    Splits text into chunks of roughly chunk_size_words with overlap_words.
    """
    words = text.split()
    if not words:
        return []
    if len(words) <= chunk_size_words:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size_words
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        # Prevent infinite loops if parameters are bad
        step = chunk_size_words - overlap_words
        if step <= 0:
            step = 1
        start += step
        if start >= len(words) - overlap_words:
            # If the remaining words are fewer than the overlap, we stop to avoid near-duplicate final chunks
            break
    return chunks


# ── Agent Persona Service ─────────────────────────────────────────────────────

class AgentPersonaService:
    @staticmethod
    async def get_personas(db: AsyncSession) -> List[AgentPersona]:
        stmt = select(AgentPersona).order_by(AgentPersona.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_persona_by_name(db: AsyncSession, name: str) -> Optional[AgentPersona]:
        stmt = select(AgentPersona).where(AgentPersona.name.ilike(name))
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def create_persona(db: AsyncSession, schema: AgentPersonaCreate) -> AgentPersona:
        persona = AgentPersona(
            name=schema.name,
            archetype=schema.archetype,
            pacing_speed=schema.pacing_speed,
            interruption_frequency=schema.interruption_frequency,
            silence_tolerance=schema.silence_tolerance,
            skepticism_level=schema.skepticism_level,
            technical_depth=schema.technical_depth,
            followup_aggressiveness=schema.followup_aggressiveness,
            verbosity_tolerance=schema.verbosity_tolerance,
            ambiguity_tolerance=schema.ambiguity_tolerance,
            pressure_intensity=schema.pressure_intensity,
            conversational_warmth=schema.conversational_warmth,
            challenge_escalation=schema.challenge_escalation,
            acknowledgment_patterns=schema.acknowledgment_patterns,
            custom_prompts=schema.custom_prompts,
        )
        db.add(persona)
        await db.commit()
        await db.refresh(persona)
        return persona

    @staticmethod
    async def update_persona(
        db: AsyncSession, name: str, schema: AgentPersonaUpdate
    ) -> Optional[AgentPersona]:
        persona = await AgentPersonaService.get_persona_by_name(db, name)
        if not persona:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(persona, key, value)

        await db.commit()
        await db.refresh(persona)
        return persona

    @staticmethod
    async def delete_persona(db: AsyncSession, name: str) -> bool:
        persona = await AgentPersonaService.get_persona_by_name(db, name)
        if not persona:
            return False

        await db.delete(persona)
        await db.commit()
        return True


# ── Knowledge Document Service ───────────────────────────────────────────────

class KnowledgeDocumentService:
    @staticmethod
    async def get_documents(db: AsyncSession) -> List[KnowledgeDocument]:
        stmt = select(KnowledgeDocument).order_by(KnowledgeDocument.updated_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_document_by_id(db: AsyncSession, doc_id: uuid.UUID) -> Optional[KnowledgeDocument]:
        stmt = select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def create_document(db: AsyncSession, schema: KnowledgeDocumentCreate) -> KnowledgeDocument:
        # Create parent document
        doc = KnowledgeDocument(
            title=schema.title,
            source=schema.source,
            source_type=schema.source_type,
            domain=schema.domain,
            topic=schema.topic,
            difficulty=schema.difficulty,
            content=schema.content,
            meta_data=schema.meta_data,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        # Chunk and embed
        await KnowledgeDocumentService._process_document_chunks(db, doc)
        await db.refresh(doc)
        return doc

    @staticmethod
    async def update_document(
        db: AsyncSession, doc_id: uuid.UUID, schema: KnowledgeDocumentUpdate
    ) -> Optional[KnowledgeDocument]:
        doc = await KnowledgeDocumentService.get_document_by_id(db, doc_id)
        if not doc:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        content_changed = "content" in update_data

        for key, value in update_data.items():
            setattr(doc, key, value)

        await db.commit()

        if content_changed:
            # Delete old chunks
            await db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == doc.id))
            await db.commit()
            # Generate new chunks
            await KnowledgeDocumentService._process_document_chunks(db, doc)
            await db.refresh(doc)
        else:
            await db.refresh(doc)

        return doc

    @staticmethod
    async def delete_document(db: AsyncSession, doc_id: uuid.UUID) -> bool:
        doc = await KnowledgeDocumentService.get_document_by_id(db, doc_id)
        if not doc:
            return False

        await db.delete(doc)
        await db.commit()
        return True

    @staticmethod
    async def _process_document_chunks(db: AsyncSession, doc: KnowledgeDocument) -> None:
        """
        Splits a document's content into semantic chunks, generates vectors, and saves them.
        """
        chunks_text = split_content_into_chunks(doc.content, chunk_size_words=250, overlap_words=50)
        encoder = MemoryEncoder()

        total_tokens = 0
        chunk_objects = []

        for index, text in enumerate(chunks_text):
            # Estimate token count (standard 1 token ≈ 4 chars)
            tokens = len(text) // 4
            total_tokens += tokens

            # Generate vector embedding (1536 dimensions)
            embedding = await encoder.encode(text)

            chunk = KnowledgeChunk(
                document_id=doc.id,
                chunk_text=text,
                chunk_index=index,
                token_count=tokens,
                embedding=embedding,
                meta_data=doc.meta_data,
            )
            db.add(chunk)
            chunk_objects.append(chunk)

        # Update parent stats
        doc.chunk_count = len(chunk_objects)
        doc.token_count = total_tokens
        await db.commit()

    @staticmethod
    async def get_similar_journeys(db: AsyncSession, role_title: str, limit: int = 5) -> List[InterviewJourney]:
        """
        Retrieves other interview journeys with similar role title keywords.
        Falls back to returning recent journeys if none or few match.
        """
        stop_words = {"senior", "junior", "lead", "staff", "principal", "associate", "intern", "co-op", "manager", "director", "vp", "for", "and", "in", "of", "the", "a", "an"}
        words = [w.strip(",.-_").lower() for w in role_title.split() if w.strip(",.-_")]
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        if not keywords:
            keywords = words
            
        if not keywords:
            stmt = select(InterviewJourney).order_by(InterviewJourney.created_at.desc()).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
            
        conditions = [InterviewJourney.role_title.ilike(f"%{kw}%") for kw in keywords]
        stmt = select(InterviewJourney).where(or_(*conditions)).order_by(InterviewJourney.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        similar = list(result.scalars().all())
        
        if len(similar) < 3:
            existing_ids = {s.id for s in similar}
            stmt = select(InterviewJourney).where(InterviewJourney.id.not_in(existing_ids) if existing_ids else True).order_by(InterviewJourney.created_at.desc()).limit(limit - len(similar))
            result = await db.execute(stmt)
            fallback_items = list(result.scalars().all())
            for item in fallback_items:
                if item.id not in existing_ids:
                    similar.append(item)
                    existing_ids.add(item.id)
            
        return similar[:limit]


    @staticmethod
    async def analyze_job_skills(db: AsyncSession, role_title: str, job_description: str) -> dict:
        """
        Compare job title and description with similar roles, returning standard and unique skills.
        """
        similar_journeys = await KnowledgeDocumentService.get_similar_journeys(db, role_title)
        similar_roles_compared = [
            {
                "id": j.id,
                "role_title": j.role_title,
                "company_name": j.company_name
            }
            for j in similar_journeys
        ]
        
        similar_context = ""
        if similar_journeys:
            similar_context = "Here are some similar roles and their job descriptions stored in our system:\n\n"
            for i, sj in enumerate(similar_journeys):
                similar_context += f"Similar Role {i+1}:\n"
                similar_context += f"Title: {sj.role_title}\n"
                if sj.company_name:
                    similar_context += f"Company: {sj.company_name}\n"
                similar_context += f"Job Description:\n{sj.job_description}\n\n"
        else:
            similar_context = "No similar roles were found in our database. Please evaluate this role against standard industry expectations for this job title.\n"
            
        system_context = (
            "You are a Senior Technical Recruiter and Job Analyst. Your job is to compare a target job role against general industry standards "
            "and other similar job roles, then extract the skills. You must output the result strictly in JSON format matching this schema:\n"
            "{\n"
            "  \"common_skills\": [\"list\", \"of\", \"standard/common\", \"skills\", \"expected\", \"for\", \"this\", \"general\", \"role\"],\n"
            "  \"unique_skills\": [\"list\", \"of\", \"unique/specific\", \"skills\", \"or\", \"requirements\", \"custom\", \"to\", \"this\", \"target\", \"description\"]\n"
            "}\n"
            "Do not include any extra text outside the JSON."
        )
        
        prompt = (
            f"Target Job Role: {role_title}\n"
            f"Target Job Description:\n{job_description}\n\n"
            f"{similar_context}\n"
            "Analyze the target job title and description. Compare it to the other similar roles (if provided) and general industry expectations for this job title.\n"
            "Extract two groups of skills:\n"
            "1. Common Skills: Core, standard skills typically required for this job title (e.g. general languages, basic tools, common methodologies, soft skills).\n"
            "2. Unique Skills: Specialized, custom, or highly specific skills or niche technologies mentioned in this specific job description that are NOT generic to the role type.\n"
            "Return the JSON response now."
        )
        
        def get_fallback_skills():
            all_words = (role_title + " " + job_description).lower()
            common = ["Communication", "Problem Solving", "Teamwork"]
            unique = []
            
            if "react" in all_words or "frontend" in all_words:
                common.extend(["JavaScript", "HTML/CSS", "React", "Git"])
                unique.extend(["State Management", "Tailwind CSS", "Vite"])
            if "python" in all_words or "backend" in all_words or "django" in all_words:
                common.extend(["Python", "SQL", "REST APIs", "Git"])
                unique.extend(["FastAPI/Django", "PostgreSQL", "Docker", "Asyncio"])
            if "aws" in all_words or "cloud" in all_words or "devops" in all_words:
                common.extend(["Cloud Computing", "CI/CD", "Linux", "Git"])
                unique.extend(["AWS Services", "Terraform", "Kubernetes"])
                
            if not unique:
                unique = ["Role-specific tools", "Domain knowledge"]
            return list(set(common)), list(set(unique))

        from app.ai.orchestrators.clients.model_clients import get_model_client
        from app.ai.orchestrators.contracts.model_contracts import ModelProvider
        import json
        
        model_client = get_model_client()
        
        provider = ModelProvider.STUB
        if model_client.is_available(ModelProvider.OPENAI):
            provider = ModelProvider.OPENAI
        elif model_client.is_available(ModelProvider.NIM):
            provider = ModelProvider.NIM
            
        if provider == ModelProvider.STUB:
            common, unique = get_fallback_skills()
            return {
                "input_role_title": role_title,
                "common_skills": common,
                "unique_skills": unique,
                "similar_roles_compared": similar_roles_compared
            }
            
        try:
            raw_response = await model_client.complete(
                provider=provider,
                prompt=prompt,
                context=system_context,
                json_mode=True,
                max_tokens=800,
                temperature=0.3
            )
            
            parsed = json.loads(raw_response)
            
            return {
                "input_role_title": role_title,
                "common_skills": parsed.get("common_skills", []),
                "unique_skills": parsed.get("unique_skills", []),
                "similar_roles_compared": similar_roles_compared
            }
        except Exception as e:
            logger.error("Job description analysis failed, falling back to smart keywords: %s", e)
            common, unique = get_fallback_skills()
            return {
                "input_role_title": role_title,
                "common_skills": common,
                "unique_skills": unique,
                "similar_roles_compared": similar_roles_compared
            }


