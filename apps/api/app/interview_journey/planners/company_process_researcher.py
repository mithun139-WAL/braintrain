"""
Company Process Researcher — maps company signals to a likely interview stage sequence.

Returns a structured process dict with source/confidence/stages so callers can tell
the user whether they're seeing real company data or a pattern-based guess.

Web search path:
# ponytail: _search_company_interview_process is a stub — wire SEARCH_API_KEY
# (Serper, Tavily, or Brave) when available. The archetype fallback is the real
# path until then; it covers ~90% of cases where no Glassdoor/Blind data exists.

Confidence contract:
  "high"   — real named-company data from search results
  "medium" — archetype matched from strong company-style signals
  "low"    — generic fallback, company_name unknown or style unresolvable
"""

# ── Archetype templates ───────────────────────────────────────────────────────
# Indexed by the key returned from _resolve_archetype_key().
# Stages are tokens; orchestrator maps each to a round builder.

_ARCHETYPES: dict[str, dict] = {
    "BIG_TECH": {
        "stages": ["RECRUITER_SCREEN", "TECHNICAL_1", "TECHNICAL_2", "TECHNICAL_3", "HM_SCREEN"],
        "notes": "Typical big-tech loop: recruiter screen, 3 technical rounds, hiring manager close.",
    },
    "STARTUP_EARLY": {
        "stages": ["RECRUITER_SCREEN", "TECHNICAL_1", "FOUNDER_SCREEN"],
        "notes": "Early-stage startup: recruiter screen, one technical round, founder/CEO screen.",
    },
    "STARTUP_GROWTH": {
        "stages": ["RECRUITER_SCREEN", "TECHNICAL_1", "TECHNICAL_2", "HM_SCREEN"],
        "notes": "Growth-stage startup: recruiter screen, two technical rounds, hiring manager screen.",
    },
    "ENTERPRISE": {
        "stages": ["RECRUITER_SCREEN", "TECHNICAL_1", "TECHNICAL_2", "PANEL_ROUND", "HM_SCREEN"],
        "notes": "Enterprise process: recruiter screen, technical rounds, panel, HR/hiring manager close.",
    },
    "STANDARD": {
        "stages": ["RECRUITER_SCREEN", "TECHNICAL_1", "TECHNICAL_2", "HM_SCREEN"],
        "notes": "Standard 4-stage loop: recruiter screen, two technical rounds, hiring manager screen.",
    },
}


async def research_company_process(
    company_name: str | None,
    role_title: str,
    company_signals: dict,
) -> dict:
    """
    Returns:
        {
            "source":     "web_search" | "archetype_fallback",
            "confidence": "high" | "medium" | "low",
            "stages":     ["RECRUITER_SCREEN", "TECHNICAL_1", ...],
            "notes":      str,   # surfaced to user so they know what they're getting
        }

    Web search is stubbed (no SEARCH_API_KEY configured). Always falls through
    to _archetype_fallback(). When search is wired, it runs first and only falls
    back when confidence is low (< 2 corroborating sources).
    """
    # ponytail: web search stub — replace this block with real search call
    # when SEARCH_API_KEY is configured. Good query patterns:
    #   f'"{company_name}" "phone screen" "onsite" interview site:glassdoor.com'
    #   f'"{company_name}" software engineer interview rounds experience'
    # Extract structured stages only when ≥ 2 sources agree, else fall through.
    return _archetype_fallback(company_name, company_signals)


def _archetype_fallback(company_name: str | None, company_signals: dict) -> dict:
    key = _resolve_archetype_key(company_signals)
    archetype = _ARCHETYPES[key]
    confidence = "medium" if company_name else "low"
    return {
        "source": "archetype_fallback",
        "confidence": confidence,
        "stages": archetype["stages"],
        "notes": archetype["notes"],
    }


def _resolve_archetype_key(company_signals: dict) -> str:
    style = company_signals.get("company_style", "STANDARD")
    if style == "BIG_TECH":
        return "BIG_TECH"
    if style == "ENTERPRISE":
        return "ENTERPRISE"
    if style == "STARTUP":
        stage = company_signals.get("startup_stage", "GROWTH")
        return "STARTUP_EARLY" if stage == "EARLY" else "STARTUP_GROWTH"
    return "STANDARD"


if __name__ == "__main__":
    import asyncio

    async def _test():
        cases = [
            ({"company_style": "BIG_TECH"}, ["RECRUITER_SCREEN", "TECHNICAL_1", "TECHNICAL_2", "TECHNICAL_3", "HM_SCREEN"]),
            ({"company_style": "STARTUP", "startup_stage": "EARLY"}, ["RECRUITER_SCREEN", "TECHNICAL_1", "FOUNDER_SCREEN"]),
            ({"company_style": "STARTUP", "startup_stage": "GROWTH"}, ["RECRUITER_SCREEN", "TECHNICAL_1", "TECHNICAL_2", "HM_SCREEN"]),
            ({"company_style": "ENTERPRISE"}, ["RECRUITER_SCREEN", "TECHNICAL_1", "TECHNICAL_2", "PANEL_ROUND", "HM_SCREEN"]),
            ({"company_style": "STANDARD"}, ["RECRUITER_SCREEN", "TECHNICAL_1", "TECHNICAL_2", "HM_SCREEN"]),
        ]
        for signals, expected_stages in cases:
            result = await research_company_process("Acme", "Software Engineer", signals)
            assert result["stages"] == expected_stages, f"FAIL {signals}: got {result['stages']}"
            assert result["source"] == "archetype_fallback"
            assert result["confidence"] in ("high", "medium", "low")
        print("All archetype cases OK")

        # No company name → low confidence
        r = await research_company_process(None, "Engineer", {"company_style": "STANDARD"})
        assert r["confidence"] == "low"
        print("Confidence fallback OK")

    asyncio.run(_test())
