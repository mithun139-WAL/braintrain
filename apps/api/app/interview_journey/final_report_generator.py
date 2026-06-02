"""
Final Report Generator — produces recruiter-style hiring report from journey data.
"""

from app.db.models.interview_journey import InterviewJourney
from app.interview_journey.evaluation import evaluate_round_responses
from app.interview_journey.journey_memory_manager import get_journey_memory


def generate_final_report(journey: InterviewJourney) -> dict:
    plan = journey.generated_plan or {}
    rounds = plan.get("rounds", [])
    signals = journey.extracted_signals or {}
    resume_analysis = signals.get("resume_analysis", {})
    jd_analysis = signals.get("jd_analysis", {})

    round_reports = _generate_round_reports(journey, rounds)
    strengths, weaknesses = _aggregate_assessments(round_reports)
    strongest, weakest = _find_best_worst_rounds(round_reports)
    risk_areas = _identify_risks(round_reports, resume_analysis, jd_analysis)
    company_fit = _assess_company_fit(resume_analysis, jd_analysis)
    comm_summary, tech_summary = _summarize(round_reports)
    recommendation = _generate_recommendation(round_reports, risk_areas)

    return {
        "journey_id": str(journey.id),
        "role_title": journey.role_title,
        "company_name": journey.company_name,
        "candidate_level": journey.candidate_level or resume_analysis.get("candidate_level", "MID"),
        "hire_recommendation": recommendation["decision"],
        "overall_hiring_signal": recommendation["signal"],
        "strongest_round": strongest,
        "weakest_round": weakest,
        "hiring_risk_areas": risk_areas,
        "company_fit": company_fit,
        "communication_summary": comm_summary,
        "technical_summary": tech_summary,
        "recruiter_notes": recommendation["recruiter_notes"],
        "round_reports": round_reports,
    }


def _generate_round_reports(journey: InterviewJourney, rounds: list[dict]) -> list[dict]:
    reports = []
    memory = get_journey_memory(str(journey.id))

    for i, round_data in enumerate(rounds):
        round_name = round_data.get("name", f"Round {i + 1}")
        focus = round_data.get("focus", {})

        responses = _get_round_responses(journey, round_name)

        if responses:
            evaluation = evaluate_round_responses(responses, round_data)
            strengths = evaluation.get("strengths", [])
            weaknesses = evaluation.get("weaknesses", [])
            missed = evaluation.get("missed_opportunities", [])
            comm_notes = evaluation.get("communication_notes", {})
            tech_gaps = evaluation.get("technical_gaps", [])
        else:
            strengths = []
            weaknesses = ["Round not completed — no response data"]
            missed = []
            comm_notes = {}
            tech_gaps = ["No data available"]

        reports.append({
            "round_name": round_name,
            "round_type": round_data.get("round_type", ""),
            "difficulty": round_data.get("difficulty", "MEDIUM"),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "missed_opportunities": missed,
            "communication_quality": comm_notes.get("communication_quality", "unknown"),
            "technical_gaps": tech_gaps,
        })

        signals = {
            "weaknesses": weaknesses,
            "strengths": strengths,
            "unresolved_topics": missed,
            "confidence_drops": [],
            "recurring_mistakes": tech_gaps,
            "strong_signals": strengths,
            "topic_coverage": {a: "weak" if a in tech_gaps else "strong" for a in focus.get("areas", [])},
            "interviewer_notes": f"Completed round: {round_name}",
        }
        memory.record_round(round_name, signals)

    return reports


def _get_round_responses(journey: InterviewJourney, round_name: str) -> list[dict]:
    # Placeholder — in production, fetch responses from InterviewSession linked via journey_session.session_id
    return []


def _aggregate_assessments(reports: list[dict]) -> tuple[list[str], list[str]]:
    all_strengths = []
    all_weaknesses = []
    for r in reports:
        all_strengths.extend(r.get("strengths", []))
        all_weaknesses.extend(r.get("weaknesses", []))
    return list(set(all_strengths)), list(set(all_weaknesses))


def _find_best_worst_rounds(reports: list[dict]) -> tuple[str | None, str | None]:
    if not reports:
        return None, None
    scored = []
    for r in reports:
        score = len(r.get("strengths", [])) - len(r.get("weaknesses", [])) - len(r.get("technical_gaps", []))
        scored.append((r["round_name"], score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0], scored[-1][0]


def _identify_risks(
    reports: list[dict],
    resume_analysis: dict,
    jd_analysis: dict,
) -> list[str]:
    risks = []
    all_weaknesses = []
    all_gaps = []
    for r in reports:
        all_weaknesses.extend(r.get("weaknesses", []))
        all_gaps.extend(r.get("technical_gaps", []))

    if all_gaps:
        risks.append("Technical depth concerns: " + "; ".join(all_gaps[:3]))
    if all_weaknesses:
        risks.append("Communication structure: " + "; ".join(all_weaknesses[:2]))

    missing = resume_analysis.get("role_alignment", {}).get("missing_requirements", [])
    if missing:
        risks.append(f"Missing required skills: {', '.join(missing[:3])}")

    return risks


def _assess_company_fit(resume_analysis: dict, jd_analysis: dict) -> str:
    candidate_level = resume_analysis.get("candidate_level", "MID")
    role_level = jd_analysis.get("role_level", "MID")
    role_category = jd_analysis.get("role_category", "GENERAL")
    domains = resume_analysis.get("verified_domains", [])

    level_map = {"ENTRY": 1, "JUNIOR": 2, "MID": 3, "SENIOR": 4, "STAFF": 5}
    level_gap = level_map.get(role_level, 3) - level_map.get(candidate_level, 3)

    if abs(level_gap) <= 1 and role_category.lower() in [d.lower() for d in domains]:
        return "Good alignment — candidate experience matches role requirements"
    elif level_gap > 1:
        return "Possible stretch — role requires more seniority than candidate demonstrates"
    elif level_gap < -1:
        return "Candidate may be overqualified for this role"
    else:
        return "Partial alignment — some domain experience but gaps exist"


def _summarize(reports: list[dict]) -> tuple[str, str]:
    comm_qualities = [r.get("communication_quality", "") for r in reports if r.get("communication_quality")]
    comm_summary = (
        f"Candidate communication was generally {comm_qualities[0] if comm_qualities else 'adequate'}. "
        f"Completed {len(reports)} interview rounds."
    )

    tech_summary_parts = []
    for r in reports:
        strengths = r.get("strengths", [])
        gaps = r.get("technical_gaps", [])
        if strengths:
            tech_summary_parts.append(f"In {r['round_name']}: demonstrated {'; '.join(strengths[:2])}")
        if gaps:
            tech_summary_parts.append(f"Areas to develop: {'; '.join(gaps[:2])}")

    tech_summary = " | ".join(tech_summary_parts) if tech_summary_parts else "Technical assessment requires more data."

    return comm_summary, tech_summary


def _generate_recommendation(reports: list[dict], risk_areas: list[str]) -> dict:
    if not reports:
        return {
            "decision": "INCONCLUSIVE",
            "signal": "WEAK",
            "recruiter_notes": "No interview rounds completed. Insufficient data for evaluation.",
        }

    total_strengths = sum(len(r.get("strengths", [])) for r in reports)
    total_weaknesses = sum(len(r.get("weaknesses", [])) for r in reports)
    total_gaps = sum(len(r.get("technical_gaps", [])) for r in reports)
    completed = len([r for r in reports if r.get("strengths") or r.get("weaknesses")])
    ratio = total_strengths / max(total_strengths + total_weaknesses + total_gaps, 1)

    if ratio >= 0.6 and completed >= 2 and not risk_areas:
        decision = "STRONG_HIRE"
        signal = "STRONG"
        notes = "Candidate demonstrated consistent strength across rounds. Recommend advancing."
    elif ratio >= 0.4 and completed >= 1:
        decision = "HIRE"
        signal = "MODERATE"
        notes = "Candidate shows potential with some areas to develop. Conditional recommendation."
    elif ratio >= 0.2:
        decision = "NO_HIRE"
        signal = "WEAK"
        notes = "Candidate did not meet the bar for this role. Significant gaps identified."
    else:
        decision = "STRONG_NO_HIRE"
        signal = "NEGATIVE"
        notes = "Candidate substantially underperformed expectations across multiple dimensions."

    if risk_areas:
        notes += f"\nKey risks: {'; '.join(risk_areas[:3])}"

    return {
        "decision": decision,
        "signal": signal,
        "recruiter_notes": notes,
    }
