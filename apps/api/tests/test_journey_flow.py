import pytest
from app.interview_journey.planners.round_generator import generate_rounds
from app.interview_journey.orchestrator import generate_pipeline_stages

def test_generate_rounds_five_stages():
    resume_analysis = {
        "candidate_level": "MID",
        "estimated_years": 4.0,
        "verified_technologies": ["React", "TypeScript", "JavaScript"],
        "strengths": ["Clean React state management"],
        "weaknesses": [],
    }
    
    jd_analysis = {
        "role_level": "MID",
        "role_category": "FRONTEND",
        "must_have_skills": ["React", "TypeScript", "CSS"],
        "preferred_skills": ["Next.js"],
        "likely_interview_focus": ["frontend"],
        "hidden_expectations": [],
    }
    
    company_signals = {
        "company_style": "STARTUP",
        "culture_style": "STARTUP",
    }
    
    rounds = generate_rounds(resume_analysis, jd_analysis, company_signals)
    
    # Verify exactly 5 rounds are generated
    assert len(rounds) == 5
    
    # Verify the sequence of rounds and their types matches the flow from the image
    assert rounds[0]["name"] == "Technical Screen"
    assert rounds[0]["round_type"] == "RECRUITER_SCREEN"
    assert rounds[0]["estimated_duration_minutes"] == 30
    
    assert rounds[1]["name"] == "Coding"
    assert rounds[1]["round_type"] == "CODING"
    assert rounds[1]["estimated_duration_minutes"] == 60
    
    assert rounds[2]["name"] == "System Design"
    assert rounds[2]["round_type"] == "SYSTEM_DESIGN"
    assert rounds[2]["estimated_duration_minutes"] == 60
    
    assert rounds[3]["name"] == "Behavioral"
    assert rounds[3]["round_type"] == "BEHAVIORAL"
    assert rounds[3]["estimated_duration_minutes"] == 45
    
    assert rounds[4]["name"] == "AI Fluency"
    assert rounds[4]["round_type"] == "AI_FLUENCY"
    assert rounds[4]["estimated_duration_minutes"] == 30


@pytest.mark.asyncio
async def test_generate_pipeline_stages_integration():
    resume_analysis = {
        "candidate_level": "MID",
        "verified_technologies": ["Python", "FastAPI"],
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
    
    company_signals = {
        "company_style": "STANDARD",
    }
    
    rounds, process = await generate_pipeline_stages(
        resume_analysis, jd_analysis, company_signals,
        company_name="Acme Corp", role_title="Backend Engineer"
    )
    
    assert len(rounds) == 5
    assert rounds[0]["name"] == "Technical Screen"
    assert rounds[4]["name"] == "AI Fluency"
    assert process["source"] == "archetype_fallback"
