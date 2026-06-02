import uuid
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.career_profile import CareerProfile
from app.interview_journey.analyzers.resume_parser import parse_resume
from app.ai.orchestrators.clients.model_clients import get_model_client
from app.ai.orchestrators.contracts.model_contracts import ModelProvider

logger = logging.getLogger("career_optimizer")


class CareerOptimizerService:
    @staticmethod
    async def list_history(db: AsyncSession, user_id: uuid.UUID) -> List[CareerProfile]:
        """Lists past optimization results for a specific user."""
        stmt = select(CareerProfile).where(CareerProfile.user_id == user_id).order_by(CareerProfile.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, doc_id: uuid.UUID, user_id: uuid.UUID) -> Optional[CareerProfile]:
        """Retrieves a specific profile optimization result for the user."""
        stmt = select(CareerProfile).where(CareerProfile.id == doc_id, CareerProfile.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_by_id(db: AsyncSession, doc_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Deletes a career optimization run from database."""
        profile = await CareerOptimizerService.get_by_id(db, doc_id, user_id)
        if not profile:
            return False
        await db.delete(profile)
        await db.commit()
        return True

    @staticmethod
    async def optimize_profile(
        db: AsyncSession,
        user_id: uuid.UUID,
        current_role: str,
        target_role: str,
        resume_bytes: Optional[bytes] = None,
        resume_filename: Optional[str] = None,
        linkedin_bytes: Optional[bytes] = None,
        linkedin_filename: Optional[str] = None,
        naukri_bytes: Optional[bytes] = None,
        naukri_filename: Optional[str] = None,
    ) -> CareerProfile:
        """
        Extracts, scores (via Hybrid Evaluation), and generates transition optimization content
        for a user moving from current_role to target_role.
        """
        # Step 1: Text extraction
        resume_text = parse_resume(resume_bytes, resume_filename) if resume_bytes else ""
        linkedin_text = parse_resume(linkedin_bytes, linkedin_filename) if linkedin_bytes else ""
        naukri_text = parse_resume(naukri_bytes, naukri_filename) if naukri_bytes else ""

        combined_text = (
            f"=== RESUME ===\n{resume_text}\n\n"
            f"=== LINKEDIN ===\n{linkedin_text}\n\n"
            f"=== NAUKRI ===\n{naukri_text}"
        ).strip()

        # Step 2: Role Intelligence (define target profile requirements)
        target_profile = await CareerOptimizerService._get_target_role_profile(target_role)

        # Step 3: Extract structured profile features using LLM (if content exists)
        extracted_data = {}
        if combined_text:
            extracted_data = await CareerOptimizerService._extract_profile_data(combined_text)
        else:
            # Empty fallback when no docs are uploaded
            extracted_data = {
                "experience": [],
                "skills": [],
                "projects": [],
                "education": [],
                "certifications": [],
                "headlines": [],
                "summaries": [],
                "technologies": [],
                "career_progression": ""
            }

        # Step 4: Hybrid Evaluation: Rule Engine (60% weight) + LLM Engine (40% weight)
        analysis_result = await CareerOptimizerService._evaluate_profile_hybrid(
            current_role, target_role, extracted_data, target_profile
        )

        # Create record in DB
        profile = CareerProfile(
            user_id=user_id,
            current_role=current_role,
            target_role=target_role,
            resume_filename=resume_filename,
            resume_content=resume_text or None,
            linkedin_filename=linkedin_filename,
            linkedin_content=linkedin_text or None,
            naukri_filename=naukri_filename,
            naukri_content=naukri_text or None,
            extracted_data=extracted_data,
            analysis_result=analysis_result
        )

        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile

    @staticmethod
    async def _get_target_role_profile(target_role: str) -> Dict[str, List[str]]:
        """Determines required/preferred skills for standard target roles, or dynamically asks LLM."""
        standard_roles = {
            "applied ai engineer": {
                "required": ["Python", "FastAPI", "RAG", "LangChain", "Vector DB", "LLMOps"],
                "preferred": ["OpenTelemetry", "Evaluation Pipelines", "AI Agents", "Prompt Engineering"]
            },
            "ai engineer": {
                "required": ["Python", "ML Foundations", "LLM Frameworks", "APIs", "Deployment"],
                "preferred": ["PyTorch", "Model Fine-tuning", "NLP", "Hugging Face"]
            },
            "frontend engineer": {
                "required": ["React", "TypeScript", "Next.js", "JavaScript", "HTML/CSS"],
                "preferred": ["TailwindCSS", "State Management", "UI/UX Design", "Jest", "Vite"]
            },
            "backend engineer": {
                "required": ["Python", "SQL", "REST APIs", "System Design", "Git"],
                "preferred": ["FastAPI", "PostgreSQL", "Docker", "Redis", "Microservices"]
            }
        }

        normalized = target_role.lower().strip()
        for key, profile in standard_roles.items():
            if key in normalized or normalized in key:
                return profile

        # Fallback: Dynamic profile requirements via LLM
        model_client = get_model_client()
        provider = ModelProvider.OPENAI if model_client.is_available(ModelProvider.OPENAI) else ModelProvider.STUB
        
        if provider == ModelProvider.STUB:
            return {
                "required": ["Problem Solving", "Software Engineering", "Core Tech Skills"],
                "preferred": ["Advanced Tools", "System Architecture", "Leadership"]
            }

        prompt = (
            f"Define a target role profile for the job title: '{target_role}'.\n"
            "Identify standard technical required skills (essential, core technologies) "
            "and preferred skills (advanced, nice-to-have technologies).\n"
            "Return the output STRICTLY as a JSON matching this exact schema:\n"
            "{\n"
            "  \"required\": [\"skill1\", \"skill2\"],\n"
            "  \"preferred\": [\"skill3\", \"skill4\"]\n"
            "}"
        )
        try:
            raw = await model_client.complete(
                provider=provider,
                prompt=prompt,
                context="You are a Technical Recruiter and Role Intelligence specialist.",
                json_mode=True,
                max_tokens=400,
                temperature=0.2
            )
            parsed = json.loads(raw)
            return {
                "required": parsed.get("required", []),
                "preferred": parsed.get("preferred", [])
            }
        except Exception as e:
            logger.error("Failed to dynamically load target role profile: %s", e)
            return {
                "required": ["Problem Solving", "Software Engineering"],
                "preferred": ["System Design", "Cloud Infrastructure"]
            }

    @staticmethod
    async def _extract_profile_data(combined_text: str) -> Dict[str, Any]:
        """Extracts structured fields from user documents using LLM."""
        model_client = get_model_client()
        provider = ModelProvider.OPENAI if model_client.is_available(ModelProvider.OPENAI) else ModelProvider.STUB
        
        if provider == ModelProvider.STUB:
            return {
                "experience": [{"title": "Software Engineer", "company": "BrainTrain Corp", "details": ["Built features"]}],
                "skills": ["Python", "React"],
                "projects": [{"name": "AI Web App", "details": ["Used OpenAI"]}],
                "education": [{"text": "B.Tech Computer Science"}],
                "certifications": [],
                "headlines": ["Software Engineer"],
                "summaries": ["Passionate developer"],
                "technologies": ["Python", "React"],
                "career_progression": "Standard progression"
            }

        prompt = (
            "You are a Career Transition Agent. Analyze the uploaded profile text "
            "and extract sections into a structured JSON representation.\n\n"
            f"Profile text:\n{combined_text}\n\n"
            "Format the JSON output strictly to match this schema:\n"
            "{\n"
            "  \"experience\": [\n"
            "    {\"title\": \"job title\", \"company\": \"company name\", \"details\": [\"achievement 1\", \"achievement 2\"]}\n"
            "  ],\n"
            "  \"skills\": [\"skill1\", \"skill2\"],\n"
            "  \"projects\": [\n"
            "    {\"name\": \"project name\", \"details\": [\"detail 1\", \"detail 2\"]}\n"
            "  ],\n"
            "  \"education\": [{\"text\": \"degree from school\"}],\n"
            "  \"certifications\": [\"cert1\", \"cert2\"],\n"
            "  \"headlines\": [\"headline 1\"],\n"
            "  \"summaries\": [\"summary 1\"],\n"
            "  \"technologies\": [\"tech1\", \"tech2\"],\n"
            "  \"career_progression\": \"brief analysis of user's career progression (e.g. Frontend -> Full Stack)\"\n"
            "}"
        )

        try:
            raw = await model_client.complete(
                provider=provider,
                prompt=prompt,
                context="You are a professional resume parser and profile extractor.",
                json_mode=True,
                max_tokens=2000,
                temperature=0.1
            )
            return json.loads(raw)
        except Exception as e:
            logger.error("Profile extraction failed: %s", e)
            return {
                "experience": [],
                "skills": [],
                "projects": [],
                "education": [],
                "certifications": [],
                "headlines": [],
                "summaries": [],
                "technologies": [],
                "career_progression": "Could not extract progression details."
            }

    @staticmethod
    async def _evaluate_profile_hybrid(
        current_role: str,
        target_role: str,
        extracted: Dict[str, Any],
        target_profile: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Calculates 60% rule engine scores + 40% LLM evaluations and generates optimization recommendations."""
        
        # ── 1. RULE ENGINE (60%) ──
        
        # Profile Completeness (max 100)
        completeness_score = 0
        if extracted.get("experience"): completeness_score += 25
        if extracted.get("skills") or extracted.get("technologies"): completeness_score += 20
        if extracted.get("projects"): completeness_score += 20
        if extracted.get("education"): completeness_score += 15
        if extracted.get("certifications"): completeness_score += 10
        if extracted.get("headlines") or extracted.get("summaries"): completeness_score += 10
        
        # Skills Coverage (max 100)
        required_skills = target_profile.get("required", [])
        preferred_skills = target_profile.get("preferred", [])
        user_skills_lower = {s.lower() for s in (extracted.get("skills", []) + extracted.get("technologies", []))}
        
        req_match = 0
        for s in required_skills:
            if any(s.lower() in us or us in s.lower() for us in user_skills_lower):
                req_match += 1
        req_score = (req_match / len(required_skills) * 100) if required_skills else 100
        
        pref_match = 0
        for s in preferred_skills:
            if any(s.lower() in us or us in s.lower() for us in user_skills_lower):
                pref_match += 1
        pref_score = (pref_match / len(preferred_skills) * 100) if preferred_skills else 100
        
        skills_coverage_score = 0.7 * req_score + 0.3 * pref_score

        # ATS Readiness (max 100)
        # Checks: quantified metrics present in details, and presence of standard sections
        has_quantification = False
        all_details = []
        for exp in extracted.get("experience", []):
            all_details.extend(exp.get("details", []))
        for proj in extracted.get("projects", []):
            all_details.extend(proj.get("details", []))
            
        import re
        # Check for numbers/percentages, e.g., 20%, 5k, etc.
        metric_matches = [d for d in all_details if re.search(r'\b\d+(?:\.\d+)?%|\b\d+x\b|\b\d+\s*(?:million|thousand|users|credits|ms|sec)\b|\b\$\d+', d)]
        if len(metric_matches) >= 2:
            has_quantification = True
            
        ats_score = completeness_score * 0.7
        if has_quantification:
            ats_score += 30
        else:
            ats_score += 10
            
        # Headline Quality & Keyword Density (max 100)
        headline_score = 50
        headlines = extracted.get("headlines", [])
        if headlines:
            hl = headlines[0]
            # Check length: 50-120 is great
            if 50 <= len(hl) <= 120:
                headline_score += 25
            # Check keywords matching target role
            target_words = [w.lower() for w in target_role.split()]
            if any(tw in hl.lower() for tw in target_words):
                headline_score += 25
                
        recruiter_visibility_rule = 0.5 * skills_coverage_score + 0.5 * headline_score

        # ── 2. LLM EVALUATION (40%) ──
        model_client = get_model_client()
        provider = ModelProvider.OPENAI if model_client.is_available(ModelProvider.OPENAI) else ModelProvider.STUB
        
        llm_eval = {
            "storytelling": 70,
            "positioning": 65,
            "career_alignment": 60,
            "professional_branding": 70,
            "market_fit": 65,
            "feedback": "Upload resume/LinkedIn files to get full AI recommendations.",
            "missing_keywords": target_profile.get("required", [])[:3],
            "missing_proof": ["Production project in target technology"],
            "linkedin_headline_options": [
                f"{current_role} | Transitioning to {target_role} | Building scalable applications",
                f"{target_role} | Specializing in {', '.join(required_skills[:3])}",
                f"{current_role} & Aspiring {target_role} | Passionate about innovation",
                f"{target_role} | Engineering products using {', '.join(preferred_skills[:2])}",
                f"Software Engineer specializing in {target_role} frameworks"
            ],
            "linkedin_about_professional": "Experienced software developer transition to AI applications...",
            "linkedin_about_story": "From building traditional backend systems to designing agent architectures...",
            "linkedin_about_recruiter": "Full Stack developer with expertise in python, langchain...",
            "resume_summary": "ATS-optimized summary focused on bridging transition gaps...",
            "naukri_headline": f"Specialist in {target_role} | python, fastapi",
            "naukri_summary": f"Strong experience in database systems and {', '.join(required_skills[:2])}"
        }

        if provider != ModelProvider.STUB:
            prompt = (
                f"Analyze this candidate profile for transition from '{current_role}' to '{target_role}'.\n\n"
                f"Candidate Structured Data:\n{json.dumps(extracted, indent=2)}\n\n"
                f"Target Profile Details:\n{json.dumps(target_profile, indent=2)}\n\n"
                "Evaluate the transition gap, branding, storytelling, positioning, and market fit. "
                "Output standard gap items, priority roadmaps, and rewritten profiles.\n"
                "Return output STRICTLY in JSON format with this exact schema:\n"
                "{\n"
                "  \"storytelling_score\": 1-100,\n"
                "  \"positioning_score\": 1-100,\n"
                "  \"career_alignment_score\": 1-100,\n"
                "  \"professional_branding_score\": 1-100,\n"
                "  \"market_fit_score\": 1-100,\n"
                "  \"storytelling_feedback\": \"feedback here\",\n"
                "  \"positioning_feedback\": \"feedback here\",\n"
                "  \"career_alignment_feedback\": \"feedback here\",\n"
                "  \"professional_branding_feedback\": \"feedback here\",\n"
                "  \"market_fit_feedback\": \"feedback here\",\n"
                "  \"missing_keywords\": [\"keyword1\", \"keyword2\"],\n"
                "  \"missing_proof\": [\"missing proof item 1\", \"missing proof item 2\"],\n"
                "  \"roadmap_high\": [\"item 1\", \"item 2\"],\n"
                "  \"roadmap_medium\": [\"item 1\", \"item 2\"],\n"
                "  \"roadmap_low\": [\"item 1\", \"item 2\"],\n"
                "  \"linkedin_headline_options\": [\"opt 1\", \"opt 2\", \"opt 3\", \"opt 4\", \"opt 5\"],\n"
                "  \"linkedin_about_professional\": \"about text\",\n"
                "  \"linkedin_about_story\": \"about text\",\n"
                "  \"linkedin_about_recruiter\": \"about text\",\n"
                "  \"resume_summary\": \"resume summary text\",\n"
                "  \"naukri_headline\": \"naukri headline text\",\n"
                "  \"naukri_summary\": \"naukri summary text\"\n"
                "}"
            )
            
            try:
                raw = await model_client.complete(
                    provider=provider,
                    prompt=prompt,
                    context="You are a professional Senior Tech Recruiter and AI Career Transition Coach.",
                    json_mode=True,
                    max_tokens=3000,
                    temperature=0.3
                )
                res = json.loads(raw)
                llm_eval = {
                    "storytelling": res.get("storytelling_score", 75),
                    "positioning": res.get("positioning_score", 70),
                    "career_alignment": res.get("career_alignment_score", 65),
                    "professional_branding": res.get("professional_branding_score", 75),
                    "market_fit": res.get("market_fit_score", 70),
                    "feedback": (
                        f"Storytelling: {res.get('storytelling_feedback', '')}\n\n"
                        f"Branding: {res.get('professional_branding_feedback', '')}"
                    ),
                    "missing_keywords": res.get("missing_keywords", []),
                    "missing_proof": res.get("missing_proof", []),
                    "roadmap_high": res.get("roadmap_high", []),
                    "roadmap_medium": res.get("roadmap_medium", []),
                    "roadmap_low": res.get("roadmap_low", []),
                    "linkedin_headline_options": res.get("linkedin_headline_options", []),
                    "linkedin_about_professional": res.get("linkedin_about_professional", ""),
                    "linkedin_about_story": res.get("linkedin_about_story", ""),
                    "linkedin_about_recruiter": res.get("linkedin_about_recruiter", ""),
                    "resume_summary": res.get("resume_summary", ""),
                    "naukri_headline": res.get("naukri_headline", ""),
                    "naukri_summary": res.get("naukri_summary", "")
                }
            except Exception as e:
                logger.error("LLM career optimization evaluation failed: %s", e)

        # ── 3. COMBINE SCORES (60% Rule + 40% LLM) ──
        career_score = 0.6 * completeness_score + 0.4 * llm_eval["storytelling"]
        role_alignment_score = 0.6 * skills_coverage_score + 0.4 * llm_eval["career_alignment"]
        market_readiness_score = 0.6 * ats_score + 0.4 * llm_eval["market_fit"]
        recruiter_visibility_score = 0.6 * recruiter_visibility_rule + 0.4 * llm_eval["professional_branding"]

        # Default roadmaps if not generated
        roadmap_high = llm_eval.get("roadmap_high") or [
            f"Rewrite LinkedIn headline to target '{target_role}' directly",
            f"Add target required skills ({', '.join(required_skills[:3])}) to your profile",
            "Build a production proof project demonstrating experience in key technologies"
        ]
        roadmap_medium = llm_eval.get("roadmap_medium") or [
            f"Write an AI-focused LinkedIn About section highlighting transition intent",
            "Optimize resume summary with transition metrics"
        ]
        roadmap_low = llm_eval.get("roadmap_low") or [
            "Improve LinkedIn/Naukri profile banners and headlines",
            "Earn a basic certification in target domain technologies"
        ]

        # Already present skills
        already_present = []
        for s in (required_skills + preferred_skills):
            if any(s.lower() in us or us in s.lower() for us in user_skills_lower):
                already_present.append(s)
                
        missing_skills = [s for s in required_skills if s not in already_present]
        recommended_skills = [s for s in preferred_skills if s not in already_present]

        return {
            "scores": {
                "career_score": round(career_score, 1),
                "role_alignment_score": round(role_alignment_score, 1),
                "market_readiness_score": round(market_readiness_score, 1),
                "recruiter_visibility_score": round(recruiter_visibility_score, 1),
            },
            "gap_analysis": {
                "missing_skills": missing_skills,
                "missing_keywords": llm_eval.get("missing_keywords", []),
                "weak_positioning": [
                    f"Candidate lacks direct professional titles using '{target_role}'",
                    "Resume bullet points focus on generic developer activities rather than specialized target role outcomes"
                ],
                "missing_projects": [f"Missing projects explicitly built with {', '.join(required_skills[:2])}"],
                "missing_certifications": ["Relevant professional credentials in target role concepts"],
                "missing_proof": llm_eval.get("missing_proof", []),
                "weak_headlines": [
                    "Headline lists only past roles instead of future-oriented specialization"
                ],
                "weak_summaries": [
                    "Summaries focus heavily on history rather than core transition competencies"
                ]
            },
            "roadmap": {
                "high": roadmap_high,
                "medium": roadmap_medium,
                "low": roadmap_low
            },
            "generated_content": {
                "linkedin_headlines": llm_eval.get("linkedin_headline_options", [])[:5],
                "linkedin_about": {
                    "professional": llm_eval.get("linkedin_about_professional"),
                    "story": llm_eval.get("linkedin_about_story"),
                    "recruiter": llm_eval.get("linkedin_about_recruiter")
                },
                "resume_summary": llm_eval.get("resume_summary"),
                "naukri_headline": llm_eval.get("naukri_headline"),
                "naukri_summary": llm_eval.get("naukri_summary"),
                "skills_suggestions": {
                    "already_present": already_present,
                    "missing_skills": missing_skills,
                    "recommended_skills": recommended_skills
                }
            }
        }
