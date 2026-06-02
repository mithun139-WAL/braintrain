"""
Company Signal Extractor — infers company context from the job description and company name.
"""


def extract_company_signals(company_name: str | None, jd_text: str) -> dict:
    lower = jd_text.lower()
    signals = {
        "company_style": _detect_company_style(company_name, lower),
        "speed_expectation": _detect_speed_expectation(lower),
        "collaboration_style": _detect_collaboration_style(lower),
        "system_scale": _detect_system_scale(lower),
        "engineering_maturity": _detect_engineering_maturity(lower),
    }
    return signals


def _detect_company_style(company_name: str | None, lower: str) -> str:
    startup_signals = ["startup", "series", "funded", "venture", "seed", "growth-stage", "scale-up"]
    enterprise_signals = ["enterprise", "fortune", "global", "corporate", "institution", "banking"]

    if any(s in lower for s in startup_signals):
        return "STARTUP"
    if any(s in lower for s in enterprise_signals):
        return "ENTERPRISE"
    if any(w in lower for w in ["faang", "big tech", "top tech", "unicorn"]):
        return "BIG_TECH"
    return "STANDARD"


def _detect_speed_expectation(lower: str) -> str:
    if any(w in lower for w in ["move fast", "fast-paced", "rapid", "quickly", "velocity"]):
        return "FAST"
    if any(w in lower for w in ["thoughtful", "deliberate", "careful", "thorough"]):
        return "DELIBERATE"
    return "BALANCED"


def _detect_collaboration_style(lower: str) -> str:
    if any(w in lower for w in ["cross-functional", "paired", "pair programming", "mob"]):
        return "HIGHLY_COLLABORATIVE"
    if any(w in lower for w in ["independent", "autonomous", "ownership", "self-directed"]):
        return "AUTONOMOUS"
    return "TEAM_BASED"


def _detect_system_scale(lower: str) -> str:
    if any(w in lower for w in ["millions", "billions", "high-scale", "global scale"]):
        return "LARGE"
    if any(w in lower for w in ["thousands", "growing", "moderate scale"]):
        return "MEDIUM"
    return "SMALL"


def _detect_engineering_maturity(lower: str) -> str:
    signals = []
    if any(w in lower for w in ["ci/cd", "continuous integration", "automated testing"]):
        signals.append("automated delivery")
    if any(w in lower for w in ["code review", "pull request", "pair programming"]):
        signals.append("code review culture")
    if any(w in lower for w in ["documentation", "spec", "adr", "architecture decision"]):
        signals.append("documentation culture")
    if any(w in lower for w in ["incident", "post-mortem", "blameless", "retro"]):
        signals.append("incident management")
    if not signals:
        signals.append("undefined")
    return signals
