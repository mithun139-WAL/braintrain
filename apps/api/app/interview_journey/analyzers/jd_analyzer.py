"""
JD Analyzer — extracts structured requirements and expectations from job descriptions.
"""
import re


def analyze_jd(text: str) -> dict:
    must_have = _extract_must_have_skills(text)
    preferred = _extract_preferred_skills(text)
    hidden = _detect_hidden_expectations(text)
    system_complexity = _assess_system_complexity(text)
    communication = _assess_communication_expectations(text)
    collaboration = _assess_collaboration_expectations(text)
    architecture = _detect_architecture_signals(text)
    ownership = _detect_ownership_expectations(text)
    role_level = _determine_role_level(text)
    role_category = _determine_role_category(text)
    culture = _determine_culture_style(text)
    hiring_bar = _determine_hiring_bar(text)

    return {
        "role_level": role_level,
        "role_category": role_category,
        "must_have_skills": must_have,
        "preferred_skills": preferred,
        "hidden_expectations": hidden,
        "system_complexity_signals": system_complexity,
        "communication_expectations": communication,
        "collaboration_expectations": collaboration,
        "architecture_signals": architecture,
        "ownership_expectations": ownership,
        "culture_style": culture,
        "hiring_bar_signals": hiring_bar,
        "likely_interview_focus": _determine_interview_focus(
            must_have, preferred, architecture, system_complexity
        ),
    }


def _extract_must_have_skills(text: str) -> list[str]:
    skills = []
    sections = re.split(r"\n\s*\n", text)
    for section in sections:
        lower = section.lower()
        if any(p in lower for p in ["requirement", "must have", "qualification", "about you", "what you need"]):
            lines = section.split("\n")
            for line in lines:
                line = line.strip().lstrip("•-*1234567890.) ")
                if line and len(line) > 5:
                    skills.append(line)
    if not skills:
        tech_skills = re.findall(
            r"\b(React|Angular|Vue|Python|TypeScript|JavaScript|Go|Rust|Java|Kotlin|Swift|"
            r"Node\.?js|Express|FastAPI|Django|Flask|Spring|PostgreSQL|MySQL|MongoDB|Redis|"
            r"Docker|Kubernetes|AWS|GCP|Azure|GraphQL|REST|gRPC)\b",
            text,
        )
        skills = list(set(tech_skills))
    return skills


def _extract_preferred_skills(text: str) -> list[str]:
    skills = []
    sections = re.split(r"\n\s*\n", text)
    for section in sections:
        lower = section.lower()
        if any(p in lower for p in ["nice to have", "preferred", "bonus", "plus"]):
            lines = section.split("\n")
            for line in lines:
                line = line.strip().lstrip("•-*1234567890.) ")
                if line and len(line) > 5:
                    skills.append(line)
    return skills


def _detect_hidden_expectations(text: str) -> list[str]:
    hidden = []
    lower = text.lower()
    indicators = {
        "startup experience": ["startup", "fast-paced", "wear many hats"],
        "on-call availability": ["on-call", "pager duty", "incident response"],
        "legacy system maintenance": ["legacy", "migration", "modernization"],
        "international collaboration": ["global", "distributed team", "multiple timezone"],
        "client-facing": ["client-facing", "customer-facing", "stakeholder management"],
        "fast delivery": ["move fast", "ship quickly", "rapid iteration"],
    }
    for expectation, keywords in indicators.items():
        if any(k in lower for k in keywords):
            hidden.append(expectation)
    return hidden


def _assess_system_complexity(text: str) -> list[str]:
    signals = []
    lower = text.lower()
    patterns = {
        "high-scale": ["millions of users", "high traffic", "scalability", "large-scale", "billions"],
        "distributed systems": ["distributed system", "microservice", "event-driven", "message queue"],
        "data-intensive": ["data pipeline", "big data", "real-time processing", "streaming"],
        "high-reliability": ["reliability", "uptime", "sla", "fault tolerance", "resilience"],
        "security-sensitive": ["security", "compliance", "audit", "soc2", "gdpr", "hipaa"],
    }
    for signal, keywords in patterns.items():
        if any(k in lower for k in keywords):
            signals.append(signal)
    return signals


def _assess_communication_expectations(text: str) -> list[str]:
    signals = []
    lower = text.lower()
    if any(w in lower for w in ["communication", "articulate", "presentation", "written"]):
        signals.append("strong written and verbal communication")
    if "documentation" in lower:
        signals.append("documentation-driven")
    if "technical writing" in lower:
        signals.append("technical writing expected")
    return signals


def _assess_collaboration_expectations(text: str) -> list[str]:
    signals = []
    lower = text.lower()
    if any(w in lower for w in ["cross-functional", "cross functional", "team", "collaborate"]):
        signals.append("cross-functional collaboration")
    if "mentor" in lower or "mentorship" in lower:
        signals.append("mentorship expected")
    if "code review" in lower:
        signals.append("code review culture")
    return signals


def _detect_architecture_signals(text: str) -> list[str]:
    signals = []
    lower = text.lower()
    arch_keywords = [
        "architecture", "architect", "system design", "design system",
        "technical decision", "trade-off", "technical roadmap",
    ]
    for kw in arch_keywords:
        if kw in lower:
            signals.append(kw)
    return signals


def _detect_ownership_expectations(text: str) -> list[str]:
    signals = []
    lower = text.lower()
    if any(w in lower for w in ["own", "ownership", "end-to-end", "from scratch"]):
        signals.append("full ownership expected")
    if "independent" in lower or "self-directed" in lower:
        signals.append("independence expected")
    if "drive" in lower:
        signals.append("initiative-driven")
    return signals


def _determine_role_level(text: str) -> str:
    lower = text.lower()
    level_map = {
        "ENTRY": ["intern", "entry-level", "junior i", "graduate"],
        "JUNIOR": ["junior", "junior ii", "early career"],
        "MID": ["mid-level", "mid level", "software engineer ii", "software engineer iii"],
        "SENIOR": ["senior", "staff", "lead", "senior ii"],
        "STAFF": ["staff", "principal", "distinguished", "fellow"],
    }
    for level, keywords in level_map.items():
        if any(k in lower for k in keywords):
            return level
    return "MID"


def _determine_role_category(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ["frontend", "front-end", "front end", "ui", "web"]):
        return "FRONTEND"
    if any(w in lower for w in ["backend", "back-end", "back end", "server"]):
        return "BACKEND"
    if any(w in lower for w in ["full stack", "fullstack", "full-stack"]):
        return "FULLSTACK"
    if any(w in lower for w in ["data", "ml", "machine learning", "data science"]):
        return "DATA"
    if any(w in lower for w in ["mobile", "ios", "android"]):
        return "MOBILE"
    if any(w in lower for w in ["devops", "platform", "infrastructure", "sre"]):
        return "DEVOPS"
    return "GENERAL"


def _determine_culture_style(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ["startup", "fast-paced", "scale-up"]):
        return "STARTUP"
    if any(w in lower for w in ["corporate", "fortune 500", "enterprise"]):
        return "ENTERPRISE"
    if any(w in lower for w in ["remote-first", "remote", "distributed"]):
        return "REMOTE_FIRST"
    if any(w in lower for w in ["collaborative", "team-first", "culture"]):
        return "COLLABORATIVE"
    return "STANDARD"


def _determine_hiring_bar(text: str) -> list[str]:
    signals = []
    lower = text.lower()
    if any(w in lower for w in ["top-tier", "best in class", "elite", "high bar"]):
        signals.append("high bar")
    if any(w in lower for w in ["growth mindset", "learning", "potential"]):
        signals.append("growth potential valued")
    if "passion" in lower:
        signals.append("passion-signal seeking")
    if any(w in lower for w in ["results-oriented", "impact", "outcome"]):
        signals.append("impact-driven evaluation")
    return signals


def _determine_interview_focus(
    must_have: list[str],
    preferred: list[str],
    architecture_signals: list[str],
    system_complexity: list[str],
) -> list[str]:
    focus = set()
    all_skills = [s.lower() for s in must_have + preferred]
    tech_map = {
        "frontend": ["react", "angular", "vue", "css", "html", "javascript", "typescript"],
        "backend": ["python", "go", "java", "node", "api", "rest", "graphql"],
        "system_design": ["distributed", "scalability", "architecture", "design"],
        "data": ["database", "sql", "nosql", "data", "analytics"],
        "infrastructure": ["docker", "kubernetes", "ci/cd", "deployment", "cloud"],
    }
    for focus_area, keywords in tech_map.items():
        if any(k in " ".join(all_skills) for k in keywords):
            focus.add(focus_area)
    if architecture_signals:
        focus.add("system_design")
    if system_complexity:
        focus.add("scalability")
    return sorted(focus)
