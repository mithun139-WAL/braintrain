"""
Evaluation Engine — hybrid rule-based + LLM evaluation for interview journeys.

RULE-BASED LAYER (primary):
- filler count, pacing, hesitation, STAR structure
- response length, contradiction detection, topic drift
- confidence phrase frequency, technical keyword density
- ownership language, quantified impact

LLM LAYER (augments):
- semantic correctness, nuance, reasoning depth, communication quality
"""
import re
import statistics


def evaluate_round_responses(responses: list[dict], round_focus: dict) -> dict:
    rule_scores = _compute_rule_based_scores(responses)
    metrics = _compute_enhanced_metrics(responses)

    strengths, weaknesses = _generate_assessment(responses, rule_scores, metrics, round_focus)

    return {
        "rule_based_scores": rule_scores,
        "enhanced_metrics": metrics,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "missed_opportunities": _detect_missed_opportunities(responses, round_focus),
        "communication_notes": _analyze_communication(responses),
        "technical_gaps": _detect_technical_gaps(responses, round_focus),
    }


def _compute_rule_based_scores(responses: list[dict]) -> dict:
    if not responses:
        return {}

    filler_counts = []
    pace_scores = []
    hesitation_scores = []
    star_scores = []
    response_lengths = []
    contradiction_scores = []
    topic_drift_scores = []
    confidence_scores = []
    tech_density_scores = []
    ownership_scores = []
    impact_scores = []

    for resp in responses:
        text = resp.get("answer_text", "") or ""
        lower = text.lower()

        filler_counts.append(_count_fillers(text))
        pace_scores.append(_assess_pace(text, resp.get("response_time_ms", 0)))
        hesitation_scores.append(_assess_hesitation(text))
        star_scores.append(_detect_star_structure(text))
        response_lengths.append(len(text.split()))
        contradiction_scores.append(_detect_contradictions(text))
        topic_drift_scores.append(_assess_topic_drift(text, resp.get("question_text", "")))
        confidence_scores.append(_assess_confidence(text))
        tech_density_scores.append(_compute_tech_density(text))
        ownership_scores.append(_detect_ownership_language(text))
        impact_scores.append(_detect_quantified_impact(text))

    return {
        "avg_filler_count": round(statistics.mean(filler_counts), 1) if filler_counts else 0,
        "avg_pace_score": round(statistics.mean(pace_scores), 1) if pace_scores else 0,
        "avg_hesitation_score": round(statistics.mean(hesitation_scores), 1) if hesitation_scores else 0,
        "avg_star_score": round(statistics.mean(star_scores), 1) if star_scores else 0,
        "avg_response_length_words": round(statistics.mean(response_lengths), 0) if response_lengths else 0,
        "avg_contradiction_score": round(statistics.mean(contradiction_scores), 1) if contradiction_scores else 0,
        "avg_topic_drift_score": round(statistics.mean(topic_drift_scores), 1) if topic_drift_scores else 0,
        "avg_confidence_score": round(statistics.mean(confidence_scores), 1) if confidence_scores else 0,
        "avg_tech_density_score": round(statistics.mean(tech_density_scores), 1) if tech_density_scores else 0,
        "avg_ownership_score": round(statistics.mean(ownership_scores), 1) if ownership_scores else 0,
        "avg_impact_score": round(statistics.mean(impact_scores), 1) if impact_scores else 0,
    }


def _compute_enhanced_metrics(responses: list[dict]) -> dict:
    if not responses:
        return {}

    conf_recovery = _compute_confidence_recovery(responses)
    bluff_scores = []
    thinking_scores = []
    stability_scores = []
    tradeoff_scores = []
    problem_solving = []
    realism_scores = []

    for resp in responses:
        text = resp.get("answer_text", "") or ""
        lower = text.lower()

        bluff_scores.append(_detect_bluffing(text))
        tradeoff_scores.append(1.0 if re.search(r"trade.?off|compromise|pros?.*cons?", lower) else 0.0)
        problem_solving.append(_assess_problem_solving(text))
        realism_scores.append(_assess_realism(text))

    return {
        "confidence_recovery_score": conf_recovery,
        "avg_bluff_detection_score": round(statistics.mean(bluff_scores), 2) if bluff_scores else 0,
        "avg_tradeoff_thinking_score": round(statistics.mean(tradeoff_scores), 2) if tradeoff_scores else 0,
        "avg_problem_solving_score": round(statistics.mean(problem_solving), 1) if problem_solving else 0,
        "avg_realism_consistency_score": round(statistics.mean(realism_scores), 1) if realism_scores else 0,
        "avg_ownership_score": round(statistics.mean(
            [_detect_ownership_language(r.get("answer_text", ""))
             for r in responses]
        ), 1) if responses else 0,
    }


def _count_fillers(text: str) -> float:
    fillers = ["um", "uh", "like", "you know", "sort of", "kind of", "basically", "actually", "literally"]
    count = sum(len(re.findall(rf"\b{f}\b", text.lower())) for f in fillers)
    words = len(text.split())
    return (count / max(words, 1)) * 100


def _assess_pace(text: str, response_time_ms: int) -> float:
    words = len(text.split())
    if response_time_ms <= 0 or words <= 0:
        return 0.5
    wpm = (words / max(response_time_ms, 1)) * 60000
    if 120 <= wpm <= 180:
        return 1.0
    elif 90 <= wpm <= 210:
        return 0.7
    elif 60 <= wpm <= 240:
        return 0.4
    return 0.2


def _assess_hesitation(text: str) -> float:
    hesitation_patterns = [
        r"\.\.\.", r"\-\-", r"i'?m not sure", r"i don'?t know",
        r"i think", r"maybe", r"perhaps", r"i guess",
    ]
    count = sum(len(re.findall(p, text.lower())) for p in hesitation_patterns)
    words = len(text.split())
    ratio = count / max(words, 1)
    return max(0, 1.0 - ratio * 10)


def _detect_star_structure(text: str) -> float:
    lower = text.lower()
    has_situation = any(w in lower for w in ["situation", "context", "background", "scenario", "project"])
    has_task = any(w in lower for w in ["task", "goal", "objective", "required", "needed to"])
    has_action = any(w in lower for w in ["did", "built", "created", "implemented", "designed", "led", "developed"])
    has_result = any(w in lower for w in ["result", "outcome", "achieved", "improved", "reduced", "increased"])
    score = sum([has_situation, has_task, has_action, has_result])
    return score / 4.0


def _detect_contradictions(text: str) -> float:
    contradiction_pairs = [
        (r"\bI\s+(?:built|created|designed)\b", r"\bwe\s+(?:built|created|designed)\b"),
        (r"\bdefinitely\b", r"\bnot\s+sure\b"),
        (r"\bexpert\b", r"\bbasic\b"),
    ]
    contradictions = 0
    for p1, p2 in contradiction_pairs:
        if re.search(p1, text.lower()) and re.search(p2, text.lower()):
            contradictions += 1
    return max(0, 1.0 - contradictions * 0.5)


def _assess_topic_drift(answer: str, question: str) -> float:
    if not question:
        return 1.0
    q_keywords = set(re.findall(r"\b[a-zA-Z]{4,}\b", question.lower()))
    a_keywords = set(re.findall(r"\b[a-zA-Z]{4,}\b", answer.lower()))
    if not q_keywords:
        return 1.0
    overlap = len(q_keywords & a_keywords) / len(q_keywords)
    return overlap


def _assess_confidence(text: str) -> float:
    high_confidence = [
        r"\bI\s+(?:built|designed|created|led|delivered|architected|implemented)\b",
        r"\b(definitely|certainly|absolutely|confident)\b",
        r"\b(specifically|precisely|exactly)\b",
    ]
    low_confidence = [
        r"\b(I'?m\s+)?not\s+sure\b",
        r"\bmaybe\b", r"\bperhaps\b", r"\bpossibly\b",
        r"\bi\s+think\b(?!\s+that\s+(?:it|this)\s+(?:works|is))",
        r"\bkind\s+of\b", r"\bsort\s+of\b",
    ]
    high = sum(len(re.findall(p, text.lower())) for p in high_confidence)
    low = sum(len(re.findall(p, text.lower())) for p in low_confidence)
    total = high + low
    if total == 0:
        return 0.5
    return high / total


def _compute_tech_density(text: str) -> float:
    tech_terms = [
        "react", "angular", "vue", "typescript", "javascript", "python", "go", "rust",
        "docker", "kubernetes", "api", "graphql", "rest", "database", "sql", "nosql",
        "algorithm", "data structure", "performance", "optimization", "scalability",
        "architecture", "component", "state management", "cache", "async",
        "concurrency", "distributed", "microservice", "ci/cd", "deployment",
    ]
    text_lower = text.lower()
    term_count = sum(1 for t in tech_terms if t in text_lower)
    total_words = len(text.split())
    return (term_count / max(total_words, 1)) * 100


def _detect_ownership_language(text: str) -> float:
    ownership_patterns = [
        r"\bI\s+(?:led|built|designed|created|owned|drove|initiated|architected|delivered)\b",
        r"\b(my\s+team|my\s+project|my\s+responsibility|my\s+decision)\b",
        r"\b(I\s+was\s+responsible|I\s+owned|I\s+drove|I\s+initiated)\b",
        r"\b(end-to-end|from\s+scratch|solely|independently)\b",
    ]
    count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in ownership_patterns)
    return min(count / 2.0, 1.0)


def _detect_quantified_impact(text: str) -> float:
    impact_patterns = [
        r"(?:improved|increased|reduced|decreased|boosted|cut|grew)\s+[\w\s]+?\s+(?:by\s+)?\d+[%]?",
        r"\d+[%\s]+\w+(?:performance|speed|efficiency|cost|time)",
        r"(?:led|managed)\s+(?:a\s+)?(?:team\s+of\s+)?\d+",
        r"(?:serving|used by|for)\s+\d+[\d,]*\s+(?:users|customers)",
    ]
    count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in impact_patterns)
    return min(count, 3.0) / 3.0


def _detect_bluffing(text: str) -> float:
    score = 0.0
    lower = text.lower()

    buzzwords = ["synergy", "leveraging", "paradigm", "holistic", "robust", "innovative", "ecosystem"]
    buzzword_count = sum(1 for b in buzzwords if b in lower)
    if buzzword_count >= 3:
        score += 0.4

    abstraction = ["in theory", "conceptually", "abstractly", "generally speaking", "at a high level"]
    abstraction_count = sum(1 for a in abstraction if a in lower)
    if abstraction_count >= 2:
        score += 0.3

    if not re.search(r"\b(?:built|created|implemented|wrote|coded|developed)\b", lower):
        score += 0.3

    return min(score, 1.0)


def _assess_problem_solving(text: str) -> float:
    score = 0.0
    lower = text.lower()

    if re.search(r"(?:first|second|third|step|phase|iteration)", lower):
        score += 0.3
    if re.search(r"(?:approach|solution|method|strategy)", lower):
        score += 0.3
    if re.search(r"(?:trade.?off|alternative|compared|versus|vs\.)", lower):
        score += 0.2
    if re.search(r"(?:result|outcome|learned|improved)", lower):
        score += 0.2
    return score


def _assess_realism(text: str) -> float:
    score = 1.0
    lower = text.lower()

    unrealistic = [
        r"perfect", r"flawless", r"never failed", r"always worked",
        r"zero bugs", r"100%", r"everyone loved",
    ]
    for p in unrealistic:
        if re.search(p, lower):
            score -= 0.2

    concrete = re.findall(r"\b\d+\b", text)
    if len(concrete) < 2:
        score -= 0.1

    return max(0.0, score)


def _compute_confidence_recovery(responses: list[dict]) -> float:
    if len(responses) < 3:
        return 0.5

    conf_scores = []
    for resp in responses:
        text = resp.get("answer_text", "") or ""
        conf_scores.append(_assess_confidence(text))

    drops = 0
    recoveries = 0
    for i in range(1, len(conf_scores)):
        if conf_scores[i] < conf_scores[i - 1] - 0.2:
            drops += 1
        elif drops > 0 and conf_scores[i] > conf_scores[i - 1] + 0.1:
            recoveries += 1
            drops = 0

    if drops == 0:
        return 1.0
    return min(recoveries / max(drops, 1), 1.0)


def _generate_assessment(
    responses: list[dict],
    rule_scores: dict,
    metrics: dict,
    round_focus: dict,
) -> tuple[list[str], list[str]]:
    strengths = []
    weaknesses = []

    if rule_scores.get("avg_star_score", 0) >= 0.7:
        strengths.append("Strong STAR structure in responses")
    elif rule_scores.get("avg_star_score", 0) < 0.3:
        weaknesses.append("Responses lack structured STAR format")

    if rule_scores.get("avg_confidence_score", 0) >= 0.7:
        strengths.append("Confident and decisive communication")
    elif rule_scores.get("avg_confidence_score", 0) < 0.4:
        weaknesses.append("Hesitant language undermines confidence")

    if rule_scores.get("avg_tech_density_score", 0) >= 5:
        strengths.append("Good technical vocabulary density")
    elif rule_scores.get("avg_tech_density_score", 0) < 2:
        weaknesses.append("Low technical specificity in responses")

    if rule_scores.get("avg_ownership_score", 0) >= 0.5:
        strengths.append("Clear ownership language")
    elif rule_scores.get("avg_ownership_score", 0) < 0.2:
        weaknesses.append("Limited ownership language — uses passive voice")

    if rule_scores.get("avg_impact_score", 0) >= 0.5:
        strengths.append("Quantified impact demonstrated")
    elif rule_scores.get("avg_impact_score", 0) < 0.2:
        weaknesses.append("No quantified results shared")

    if metrics.get("avg_bluff_detection_score", 0) > 0.5:
        weaknesses.append("Potential bluffing detected — high abstraction without specifics")

    if rule_scores.get("avg_filler_count", 0) > 5:
        weaknesses.append("High filler word usage reduces clarity")

    if metrics.get("avg_tradeoff_thinking_score", 0) >= 0.5:
        strengths.append("Demonstrates trade-off thinking")
    else:
        weaknesses.append("Does not articulate trade-offs or alternatives")

    if metrics.get("confidence_recovery_score", 0) >= 0.7:
        strengths.append("Good confidence recovery after challenging questions")

    return strengths, weaknesses


def _detect_missed_opportunities(responses: list[dict], round_focus: dict) -> list[str]:
    opportunities = []
    focus = round_focus.get("focus", {})
    areas = focus.get("areas", [])

    for area in areas:
        area_lower = area.lower()
        mentioned = False
        for resp in responses:
            text = resp.get("answer_text", "") or ""
            if area_lower in text.lower():
                mentioned = True
                break
        if not mentioned:
            opportunities.append(f"Did not address {area}")

    return opportunities[:5]


def _analyze_communication(responses: list[dict]) -> dict:
    if not responses:
        return {}
    total_words = sum(len(r.get("answer_text", "").split()) for r in responses)
    avg_words = total_words / len(responses)

    return {
        "average_response_length_words": round(avg_words, 0),
        "total_responses": len(responses),
        "communication_quality": "concise" if avg_words < 50 else "detailed" if avg_words > 150 else "balanced",
    }


def _detect_technical_gaps(responses: list[dict], round_focus: dict) -> list[str]:
    gaps = []
    focus = round_focus.get("focus", {})
    areas = focus.get("areas", [])

    for area in areas:
        area_lower = area.lower()
        shallow = True
        for resp in responses:
            text = resp.get("answer_text", "") or ""
            lower = text.lower()
            if area_lower in lower:
                has_depth = bool(
                    re.search(r"(?:implemented|built|designed|architected|optimized)", lower)
                    or re.search(r"\d+", text)
                )
                if has_depth:
                    shallow = False
                    break
        if shallow:
            gaps.append(f"Shallow coverage of {area}")

    return gaps[:5]
