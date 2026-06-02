import pytest
from app.interview_journey.planners.prerequisites_generator import (
    generate_prerequisites_fallback,
    generate_prerequisites,
)


def test_prerequisites_fallback_generation():
    resume_analysis = {
        "candidate_level": "JUNIOR",
        "estimated_years": 1.5,
        "verified_technologies": ["HTML", "CSS", "JavaScript"],
        "strengths": ["Clear frontend layout code"],
        "weaknesses": ["No backend databases experience", "No production deployment experience"],
    }
    
    jd_analysis = {
        "role_level": "SENIOR",
        "role_category": "BACKEND",
        "must_have_skills": ["Node.js", "PostgreSQL", "Docker"],
        "preferred_skills": ["Kubernetes", "AWS"],
        "likely_interview_focus": ["backend", "data"],
        "hidden_expectations": ["on-call availability"],
    }
    
    company_signals = {
        "company_style": "BIG_TECH",
        "culture_style": "STARTUP",
    }
    
    result = generate_prerequisites_fallback(resume_analysis, jd_analysis, company_signals)
    
    assert "topics" in result
    assert "issues" in result
    assert "minimum_criteria" in result
    
    # Check that topics include categories or must haves
    assert len(result["topics"]) > 0
    
    # Check that experience gap or missing stack is highlighted in issues
    assert any("experience" in issue.lower() or "junior" in issue.lower() or "level" in issue.lower() for issue in result["issues"])
    assert any("stack" in issue.lower() or "missing" in issue.lower() or "technologies" in issue.lower() for issue in result["issues"])
    
    # Check that minimum criteria includes expected level
    assert any("SENIOR" in mc.upper() for mc in result["minimum_criteria"])


@pytest.mark.asyncio
async def test_generate_prerequisites_uses_fallback_when_ai_disabled():
    resume_analysis = {
        "candidate_level": "MID",
        "estimated_years": 4.0,
        "verified_technologies": ["Python", "Django"],
        "strengths": [],
        "weaknesses": [],
    }
    
    jd_analysis = {
        "role_level": "MID",
        "role_category": "BACKEND",
        "must_have_skills": ["Python", "FastAPI"],
        "preferred_skills": [],
        "likely_interview_focus": ["backend"],
        "hidden_expectations": [],
    }
    
    company_signals = {}
    
    result = await generate_prerequisites(resume_analysis, jd_analysis, company_signals)
    
    assert isinstance(result, dict)
    assert len(result["topics"]) > 0
    assert len(result["minimum_criteria"]) > 0
