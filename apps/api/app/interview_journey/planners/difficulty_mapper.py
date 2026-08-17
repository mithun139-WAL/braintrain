"""
Difficulty Mapper — maps round difficulty based on candidate and role signals.

Key reads from company_signals:
    "company_style" — set by company_signal_extractor.py (BIG_TECH / STARTUP /
                      ENTERPRISE / STANDARD).
    NOTE: "culture_style" is a separate key set only by jd_analyzer.py and is
    NOT read here. Keep the two concepts distinct.
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

    if candidate < role:
        # underqualified: scale up toward role's bar, capped at STAFF
        gap = role - candidate
        return min(role + min(gap, 1), 5)  # cap the boost at +1 regardless of gap size
    else:
        # at or above role level: calibrate to the role's actual bar
        return role


def _adjust_for_company(base: int, company_signals: dict) -> int:
    # Reads "company_style" from company_signal_extractor.py output.
    style = company_signals.get("company_style", "STANDARD")
    if style == "BIG_TECH":
        return base + 1
    if style == "STARTUP":
        # STARTUPs typically run leaner, more practical interviews.
        # Intentionally no adjustment: difficulty is purely role/candidate-driven.
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
