"""
Interview Strategy Generator — determines interview behavior parameters
based on role, candidate, and company context.
"""


def generate_strategy(
    candidate_level: str,
    role_level: str,
    company_signals: dict,
    round_type: str,
) -> dict:
    pressure_level = _compute_pressure(candidate_level, role_level, company_signals)
    followup_intensity = _compute_followup_intensity(round_type, company_signals)
    interruption_likelihood = _compute_interruption_likelihood(
        company_signals, pressure_level
    )
    recovery_allowance = _compute_recovery_allowance(pressure_level, company_signals)

    return {
        "pressure_level": pressure_level,
        "followup_intensity": followup_intensity,
        "interruption_likelihood": interruption_likelihood,
        "recovery_allowance": recovery_allowance,
        "encouragement_frequency": _compute_encouragement(pressure_level, company_signals),
        "adaptation_speed": _compute_adaptation(company_signals),
    }


def _compute_pressure(
    candidate_level: str,
    role_level: str,
    company_signals: dict,
) -> str:
    level_map = {"ENTRY": 1, "JUNIOR": 2, "MID": 3, "SENIOR": 4, "STAFF": 5}
    cl = level_map.get(candidate_level, 3)
    rl = level_map.get(role_level, 3)

    delta = rl - cl
    if delta > 1:
        base = 4
    elif delta > 0:
        base = 3
    else:
        base = 2

    style = company_signals.get("company_style", "STANDARD")
    if style == "BIG_TECH":
        base += 1
    # STARTUP: no pressure adjustment — role/candidate delta drives it.

    if base >= 4:
        return "HIGH"
    elif base >= 3:
        return "MEDIUM"
    return "LOW"


def _compute_followup_intensity(round_type: str, company_signals: dict) -> str:
    high_followup = {"SYSTEM_DESIGN", "ARCHITECTURE", "HIRING_BAR"}
    if round_type in high_followup:
        return "HIGH"
    if round_type == "BEHAVIORAL":
        return "MEDIUM"
    style = company_signals.get("company_style", "STANDARD")
    if style == "BIG_TECH":
        return "HIGH"
    return "MEDIUM"


def _compute_interruption_likelihood(
    company_signals: dict, pressure_level: str,
) -> str:
    style = company_signals.get("company_style", "STANDARD")
    if style == "BIG_TECH" and pressure_level == "HIGH":
        return "HIGH"
    if pressure_level == "HIGH":
        return "MEDIUM"
    return "LOW"


def _compute_recovery_allowance(pressure_level: str, company_signals: dict) -> str:
    if pressure_level == "HIGH":
        return "LOW"
    # Reads company_style (company_signal_extractor). ENTERPRISE tends to have
    # more structured, forgiving processes; STARTUP is leaner.
    style = company_signals.get("company_style", "STANDARD")
    if style == "ENTERPRISE":
        return "HIGH"
    return "MEDIUM"


def _compute_encouragement(pressure_level: str, company_signals: dict) -> str:
    if pressure_level == "HIGH":
        return "LOW"
    # Reads company_style (company_signal_extractor).
    style = company_signals.get("company_style", "STANDARD")
    if style in ("ENTERPRISE", "STANDARD"):
        return "HIGH"
    return "MEDIUM"


def _compute_adaptation(company_signals: dict) -> str:
    speed = company_signals.get("speed_expectation", "BALANCED")
    if speed == "FAST":
        return "HIGH"
    return "MEDIUM"
