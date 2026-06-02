"""
Verified Candidate Profile — the single source of truth about the candidate.

This profile is injected into every interview session.
The interviewer must NEVER invent experience beyond what is in this profile.
"""


def build_verified_profile(
    resume_analysis: dict,
    jd_analysis: dict,
    company_signals: dict,
) -> dict:
    verified_skills = resume_analysis.get("verified_technologies", [])
    verified_experiences = resume_analysis.get("verified_experiences", [])
    verified_projects = resume_analysis.get("verified_projects", [])
    verified_education = resume_analysis.get("verified_education", [])

    must_have = set(s.lower() for s in jd_analysis.get("must_have_skills", []))
    has_skills = set(s.lower() for s in verified_skills)

    matched = has_skills & must_have
    missing = must_have - has_skills

    return {
        "verified_skills": verified_skills,
        "verified_experiences": verified_experiences,
        "verified_projects": verified_projects,
        "verified_education": verified_education,
        "verified_domains": resume_analysis.get("likely_focus_areas", []),
        "candidate_level": resume_analysis.get("candidate_level", "MID"),
        "role_alignment": {
            "matched_requirements": sorted(matched),
            "missing_requirements": sorted(missing),
            "overlap_ratio": round(len(matched) / max(len(must_have), 1), 2),
        },
        "quantified_achievements": resume_analysis.get("quantified_achievements", []),
        "leadership_signals": resume_analysis.get("leadership_signals", []),
        "ownership_signals": resume_analysis.get("ownership_signals", []),
        "technical_depth_signals": resume_analysis.get("technical_depth_signals", []),
        "communication_signals": resume_analysis.get("communication_signals", []),
        "unknowns": [
            f"Skill not verified: {s}" for s in list(missing)
        ],
        "company_context": company_signals,
    }
