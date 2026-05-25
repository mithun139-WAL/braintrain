"""
Resume Analyzer — extracts verified facts from parsed resume text.

Only extracts what is explicitly stated.
Never infers experience not present in the text.
"""
import re

from app.interview_journey.analyzers.resume_parser import (
    extract_education,
    extract_leadership_signals,
    extract_projects,
    extract_quantified_achievements,
    extract_technologies,
    extract_work_experience,
)


def analyze_resume(text: str) -> dict:
    experiences = extract_work_experience(text)
    technologies = extract_technologies(text)
    projects = extract_projects(text)
    education = extract_education(text)
    achievements = extract_quantified_achievements(text)
    leadership = extract_leadership_signals(text)

    years_of_exp = _estimate_years(experiences, text)
    candidate_level = _determine_candidate_level(years_of_exp, experiences, text)
    strengths, weaknesses = _analyze_strengths_weaknesses(
        technologies, experiences, achievements, leadership
    )
    focus_areas = _determine_focus_areas(technologies, experiences)
    ownership = _detect_ownership_signals(experiences, text)
    leadership_signals = _compile_leadership(leadership, experiences)
    tech_depth = _assess_technical_depth(technologies, experiences)
    communication = _assess_communication_signals(text)

    return {
        "candidate_level": candidate_level,
        "estimated_years": years_of_exp,
        "verified_technologies": technologies,
        "verified_experiences": [
            {
                "title": e.get("title", ""),
                "company": e.get("company", ""),
                "details": e.get("details", []),
            }
            for e in experiences
        ],
        "verified_projects": projects,
        "verified_education": education,
        "quantified_achievements": achievements,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "likely_focus_areas": focus_areas,
        "leadership_signals": leadership_signals,
        "ownership_signals": ownership,
        "technical_depth_signals": tech_depth,
        "communication_signals": communication,
    }


def _estimate_years(experiences: list[dict], text: str) -> float:
    year_pattern = re.findall(r"(?:19|20)\d{2}", text)
    if len(year_pattern) >= 2:
        years_only = sorted(set(int(y) for y in year_pattern if 2000 <= int(y) <= 2030))
        if len(years_only) >= 2:
            return float(years_only[-1] - years_only[0])
    total_years = 0
    for exp in experiences:
        details = " ".join(exp.get("details", []))
        yr_range = re.findall(r"(?:19|20)\d{2}", details + " " + exp.get("title", ""))
        if len(yr_range) >= 2:
            yrs = sorted(int(y) for y in yr_range if 2000 <= int(y) <= 2030)
            if len(yrs) >= 2:
                total_years += yrs[-1] - yrs[0]
    return total_years if total_years > 0 else 0


def _determine_candidate_level(
    years: float, experiences: list[dict], text: str
) -> str:
    titles = [e.get("title", "").lower() for e in experiences]
    senior_titles = [
        "senior", "staff", "principal", "lead", "architect", "head", "director",
        "vp", "vice president", "cto", "manager", "team lead",
    ]
    for t in titles:
        for st in senior_titles:
            if st in t:
                years = max(years, 5)
    if years >= 10:
        return "STAFF"
    elif years >= 6:
        return "SENIOR"
    elif years >= 3:
        return "MID"
    elif years >= 1:
        return "JUNIOR"
    else:
        return "ENTRY"


def _analyze_strengths_weaknesses(
    technologies: list[str],
    experiences: list[dict],
    achievements: list[str],
    leadership: list[str],
) -> tuple[list[str], list[str]]:
    strengths = []
    weaknesses = []

    if len(technologies) >= 8:
        strengths.append("Broad technology stack")
    elif len(technologies) <= 3:
        weaknesses.append("Limited technology breadth")

    if len(experiences) >= 3:
        strengths.append("Multiple role progression")
    elif len(experiences) <= 1:
        weaknesses.append("Limited work history depth")

    if achievements:
        strengths.append("Quantified impact demonstrated")
    else:
        weaknesses.append("No quantified achievements found")

    if leadership:
        strengths.append("Leadership signal present")
    else:
        weaknesses.append("No explicit leadership signal")

    return strengths, weaknesses


def _determine_focus_areas(technologies: list[str], experiences: list[dict]) -> list[str]:
    areas = set()
    frontend = {"react", "angular", "vue", "svelte", "next.js", "typescript", "css", "html"}
    backend = {"python", "go", "rust", "java", "node.js", "fastapi", "django", "flask", "spring", "postgresql", "redis"}
    infra = {"docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ci/cd"}
    mobile = {"swift", "kotlin", "react native", "flutter"}

    tech_lower = {t.lower() for t in technologies}
    if tech_lower & frontend:
        areas.add("frontend")
    if tech_lower & backend:
        areas.add("backend")
    if tech_lower & infra:
        areas.add("infrastructure")
    if tech_lower & mobile:
        areas.add("mobile")

    return sorted(areas)


def _detect_ownership_signals(experiences: list[dict], text: str) -> list[str]:
    signals = []
    ownership_phrases = [
        "owned", "ownership", "responsible for", "solely", "independently",
        "from scratch", "greenfield", "architected", "designed and built",
    ]
    for phrase in ownership_phrases:
        matches = re.finditer(rf"[^.]*\b{phrase}\b[^.]*\.", text, re.IGNORECASE)
        for match in matches:
            signals.append(match.group(0).strip())
    return signals


def _compile_leadership(
    leadership_signals: list[str], experiences: list[dict]
) -> list[str]:
    signals = list(leadership_signals)
    for exp in experiences:
        title = exp.get("title", "").lower()
        if any(t in title for t in ["lead", "head", "principal", "staff", "manager", "director"]):
            signals.append(f"Role-based leadership: {exp.get('title')} at {exp.get('company')}")
    return signals


def _assess_technical_depth(technologies: list[str], experiences: list[dict]) -> list[str]:
    signals = []
    depth_indicators = [
        "performance", "optimization", "scalability", "architecture", "design pattern",
        "testing", "ci/cd", "monitoring", "observability", "security",
    ]
    for exp in experiences:
        details = " ".join(exp.get("details", [])).lower()
        for indicator in depth_indicators:
            if indicator in details:
                signals.append(f"{indicator} mentioned in {exp.get('title', 'role')}")
    return signals


def _assess_communication_signals(text: str) -> list[str]:
    signals = []
    clarity_patterns = [
        r"\b(wrote|documented|presented|communicated|explained|taught|mentored)\b",
        r"\b(cross-functional|stakeholder|collaborat|teamwork)\b",
    ]
    for pattern in clarity_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            signals.append(match.group(0))
    return list(set(signals))
