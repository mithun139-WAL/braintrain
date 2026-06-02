"""
Difficulty Mapper — maps round difficulty based on candidate and role signals.
"""


def map_difficulty(
    candidate_level: str,
    role_level: str,
    round_type: str,
    company_signals: dict,
) -> str:
    base = _base_difficulty(candidate_level, role_level)
    adjusted = _adjust_for_company(base, company_signals)
    adjusted = _adjust_for_round_type(adjusted, round_type)
    return _clamp_difficulty(adjusted)


def _base_difficulty(candidate_level: str, role_level: str) -> int:
    level_map = {
        "ENTRY": 1, "JUNIOR": 2, "MID": 3, "SENIOR": 4, "STAFF": 5,
    }
    candidate = level_map.get(candidate_level, 3)
    role = level_map.get(role_level, 3)

    diff = role - candidate
    if diff > 0:
        return role + 1
    elif diff < -1:
        return role
    return candidate


def _adjust_for_company(base: int, company_signals: dict) -> int:
    style = company_signals.get("company_style", "STANDARD")
    if style == "BIG_TECH":
        return base + 1
    if style == "STARTUP":
        return base
    return base


def _adjust_for_round_type(base: int, round_type: str) -> int:
    hard_types = {"SYSTEM_DESIGN", "ARCHITECTURE", "HIRING_BAR"}
    if round_type in hard_types:
        return base + 1
    return base


def _clamp_difficulty(level: int) -> str:
    if level <= 2:
        return "EASY"
    elif level <= 4:
        return "MEDIUM"
    else:
        return "HARD"
