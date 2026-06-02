"""
Prerequisites Generator — analyzes candidate resume against JD and company signals
to produce a checklist of what the candidate should master, watch out for (issues),
and meet (minimum criteria) before launching practice sessions.
"""
import json
import logging
import re

logger = logging.getLogger(__name__)

PREREQUISITES_SYSTEM_PROMPT = """You are an expert technical and behavioral hiring planner.
Given a candidate's resume analysis, a job description analysis, and company signals, generate a checklist of prerequisites showing what the candidate must know before entering practice sessions.

This checklist must be formatted as a JSON object with exactly these three keys:
1. "topics": A list of 4-6 specific technical or behavioral topics the candidate MUST be ready to discuss or demonstrate, based on the job requirements.
2. "issues": A list of 3-5 potential gaps, risks, or weak areas in their profile compared to the job description that they need to address or prepare answers for.
3. "minimum_criteria": A list of 3-5 hard minimum baseline criteria (experience level, specific core technologies, or ownership expectations) the role demands that they must meet.

Return ONLY a valid JSON object matching this schema. Do not output any markdown code blocks, explanations, or leading/trailing text."""


def build_prerequisites_prompt(
    resume_analysis: dict,
    jd_analysis: dict,
    company_signals: dict,
) -> str:
    return f"""## Candidate Resume Analysis
Level: {resume_analysis.get("candidate_level")}
Estimated Years of Experience: {resume_analysis.get("estimated_years")}
Technologies: {", ".join(resume_analysis.get("verified_technologies", []))}
Strengths: {", ".join(resume_analysis.get("strengths", []))}
Weaknesses: {", ".join(resume_analysis.get("weaknesses", []))}

## Job Description Analysis
Expected Level: {jd_analysis.get("role_level")}
Category: {jd_analysis.get("role_category")}
Must-Have Skills: {", ".join(jd_analysis.get("must_have_skills", []))}
Preferred Skills: {", ".join(jd_analysis.get("preferred_skills", []))}
Likely Interview Focus: {", ".join(jd_analysis.get("likely_interview_focus", []))}
Hidden Expectations: {", ".join(jd_analysis.get("hidden_expectations", []))}

## Company Context
Company Style: {company_signals.get("company_style", "STANDARD")}
Culture Style: {company_signals.get("culture_style", "STANDARD")}
"""


def generate_prerequisites_fallback(
    resume_analysis: dict,
    jd_analysis: dict,
    company_signals: dict,
) -> dict:
    """
    Deterministic rule-based generator for prerequisites in case no LLM is configured.
    """
    topics = []
    must_haves = jd_analysis.get("must_have_skills", [])
    
    # 1. Topics
    for mh in must_haves[:3]:
        topics.append(mh)
        
    role_cat = jd_analysis.get("role_category", "GENERAL")
    if role_cat == "FRONTEND":
        topics.append("Frontend Performance & Rendering Optimization")
        topics.append("State Management & Component Architecture")
    elif role_cat == "BACKEND":
        topics.append("API Design & REST/GraphQL Standards")
        topics.append("Database Modeling, Normalization, & Query Optimization")
    elif role_cat == "FULLSTACK":
        topics.append("End-to-End System Flow & Integration Patterns")
        topics.append("Frontend State & Component Design")
        topics.append("Database & Server-Side Security")
    elif role_cat == "DATA":
        topics.append("Data Warehousing & ETL Pipeline Design")
        topics.append("Big Data Query Tuning & Schema Modeling")
    elif role_cat == "DEVOPS":
        topics.append("Infrastructure as Code (IaC) & Cloud Resource Management")
        topics.append("CI/CD Automation & Security Compliance")
    else:
        topics.append("Algorithmic Complexity & Problem Solving")
        topics.append("Software Engineering Best Practices & Code Maintainability")

    culture = company_signals.get("culture_style", "STANDARD")
    if culture == "STARTUP":
        topics.append("Rapid Prototyping & Dealing with Ambiguity")
    elif culture == "COLLABORATIVE":
        topics.append("Cross-Functional Coordination & Effective Mentorship")
    elif culture == "REMOTE_FIRST":
        topics.append("Asynchronous Written Communication & Independent Problem Solving")

    topics = list(dict.fromkeys([t.strip() for t in topics if t.strip()]))[:6]

    # 2. Issues / Profile Gaps
    issues = []
    must_have_lower = [mh.lower() for mh in must_haves]
    candidate_tech = [t.lower() for t in resume_analysis.get("verified_technologies", [])]
    
    tech_keywords = [
        "react", "angular", "vue", "typescript", "javascript", "go", "python",
        "rust", "java", "kotlin", "swift", "nodejs", "postgresql", "mysql",
        "mongodb", "redis", "docker", "kubernetes", "aws", "gcp", "azure"
    ]
    
    missing_tech = []
    for tech in tech_keywords:
        in_jd = any(tech in mh for mh in must_have_lower)
        in_resume = any(tech in ct for ct in candidate_tech)
        if in_jd and not in_resume:
            missing_tech.append(tech.title())
            
    if missing_tech:
        issues.append(f"Missing explicit experience with required stack: {', '.join(missing_tech)}")
        
    weaknesses = resume_analysis.get("weaknesses", [])
    for w in weaknesses[:2]:
        issues.append(w)
        
    level_map = {"ENTRY": 1, "JUNIOR": 2, "MID": 3, "SENIOR": 4, "STAFF": 5}
    cl = level_map.get(resume_analysis.get("candidate_level", "MID"), 3)
    rl = level_map.get(jd_analysis.get("role_level", "MID"), 3)
    if cl < rl:
        issues.append(
            f"Experience gap: Candidate has {resume_analysis.get('candidate_level')} level, "
            f"but the role expects {jd_analysis.get('role_level')} level."
        )

    if not issues:
        issues.append("Structuring technical answers with clear trade-offs and decisions")
        issues.append("Articulating impact and metrics for key accomplishments")
        
    issues = list(dict.fromkeys(issues))[:5]

    # 3. Minimum Criteria
    minimum_criteria = []
    expected_lvl = jd_analysis.get("role_level", "MID")
    
    minimum_criteria.append(f"Familiarity with core role expectations for a {expected_lvl}-level position")
    
    if role_cat != "GENERAL":
        minimum_criteria.append(f"Fundamental knowledge of {role_cat.title()} engineering principles")
        
    core_techs = [mh for mh in must_haves if any(tk in mh.lower() for tk in tech_keywords)]
    if core_techs:
        minimum_criteria.append(f"Practical knowledge of: {core_techs[0]}")
    else:
        minimum_criteria.append("Familiarity with modern software development lifecycle methodologies")
        
    minimum_criteria.append("Ability to communicate technical decisions and architectural trade-offs clearly")
    
    minimum_criteria = list(dict.fromkeys(minimum_criteria))[:4]

    return {
        "topics": topics,
        "issues": issues,
        "minimum_criteria": minimum_criteria,
    }


async def generate_prerequisites(
    resume_analysis: dict,
    jd_analysis: dict,
    company_signals: dict,
) -> dict:
    """
    Generate prerequisites list using active LLM (GitHub Models > NIM > OpenAI)
    or fall back to deterministic generator.
    """
    from app.core.config import get_settings
    settings = get_settings()

    if not settings.ai_enabled:
        return generate_prerequisites_fallback(resume_analysis, jd_analysis, company_signals)

    api_key = ""
    base_url = ""
    model = ""
    
    if settings.github_models_enabled:
        api_key = settings.github_token
        base_url = settings.github_models_base_url
        model = settings.github_model
    elif settings.nim_enabled:
        api_key = settings.nvidia_api_key
        base_url = settings.nvidia_base_url
        model = settings.nvidia_model
    elif settings.openai_enabled:
        api_key = settings.openai_api_key
        base_url = "https://api.openai.com/v1"
        model = "gpt-4o-mini"

    try:
        from openai import AsyncOpenAI
        
        if "api.openai.com" in base_url or not base_url:
            client = AsyncOpenAI(api_key=api_key)
        else:
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            
        user_prompt = build_prerequisites_prompt(resume_analysis, jd_analysis, company_signals)
        
        completion = await client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            temperature=0.3,
            messages=[
                {"role": "system", "content": PREREQUISITES_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        raw = completion.choices[0].message.content or ""
        if "```" in raw:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
            if match:
                raw = match.group(1).strip()
                
        parsed = json.loads(raw)
        
        topics = [t for t in parsed.get("topics", []) if isinstance(t, str)]
        issues = [i for i in parsed.get("issues", []) if isinstance(i, str)]
        minimum_criteria = [mc for mc in parsed.get("minimum_criteria", []) if isinstance(mc, str)]
        
        if topics and issues and minimum_criteria:
            return {
                "topics": topics,
                "issues": issues,
                "minimum_criteria": minimum_criteria,
            }
            
        raise ValueError("Prerequisites JSON did not contain required keys or lists")
        
    except Exception as exc:
        logger.error(
            "AI prerequisites generation failed: %s — falling back to deterministic planner",
            exc,
        )
        return generate_prerequisites_fallback(resume_analysis, jd_analysis, company_signals)
