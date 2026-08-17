import os
import re

def patch_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # 1. Update MAX_OUTPUT_TOKENS
    content = re.sub(r'MAX_OUTPUT_TOKENS = \d+', 'MAX_OUTPUT_TOKENS = 1024', content)

    # 2. Update LLM_REQUIRED_FIELDS
    old_fields = '''LLM_REQUIRED_FIELDS = [
    "clarityScore",
    "structureScore",
    "depthScore",
    "confidenceScore",
    "communicationScore",
]'''
    new_fields = '''LLM_REQUIRED_FIELDS = [
    "clarityScore",
    "clarityEvidence",
    "structureScore",
    "structureEvidence",
    "depthScore",
    "depthEvidence",
    "confidenceScore",
    "confidenceEvidence",
    "communicationScore",
    "communicationEvidence",
]'''
    content = content.replace(old_fields, new_fields)

    # 3. Update PerformanceSignal instantiation
    old_perf = '''        return PerformanceSignal(
            clarity_score=scores["clarityScore"],
            structure_score=scores["structureScore"],
            depth_score=scores["depthScore"],
            confidence_score=scores["confidenceScore"],
            communication_score=scores["communicationScore"],
            hesitation_score=0.0,
            technical_score=scores.get("technicalScore"),
            pressure_score=pressure_score,
            thinking_depth_score=thinking_depth_score,
            overall_score=overall_score,
            evaluation_explanation="",
            cost_meta=meta,
        )'''
    new_perf = '''        return PerformanceSignal(
            clarity_score=scores["clarityScore"],
            clarity_evidence=scores["clarityEvidence"],
            structure_score=scores["structureScore"],
            structure_evidence=scores["structureEvidence"],
            depth_score=scores["depthScore"],
            depth_evidence=scores["depthEvidence"],
            confidence_score=scores["confidenceScore"],
            confidence_evidence=scores["confidenceEvidence"],
            communication_score=scores["communicationScore"],
            communication_evidence=scores["communicationEvidence"],
            hesitation_score=0.0,
            technical_score=scores.get("technicalScore"),
            technical_evidence=scores.get("technicalEvidence"),
            pressure_score=pressure_score,
            thinking_depth_score=thinking_depth_score,
            overall_score=overall_score,
            evaluation_explanation="",
            cost_meta=meta,
        )'''
    content = content.replace(old_perf, new_perf)

    # 4. Update _parse_and_validate
    old_parse = '''        for field in LLM_REQUIRED_FIELDS:
            value = parsed.get(field)
            if not isinstance(value, (int, float)) or math.isnan(value):
                logger.warning(f"{provider_name} validation failed: {field} = {value}")
                return None

        tech = parsed.get("technicalScore")
        if tech is not None and not isinstance(tech, (int, float)):
            return None

        boost = DIFFICULTY_BOOST.get(difficulty.upper(), 0)
        return {
            "clarityScore":       _clamp(parsed["clarityScore"] + boost),
            "structureScore":     _clamp(parsed["structureScore"] + boost),
            "depthScore":         _clamp(parsed["depthScore"] + boost),
            "confidenceScore":    _clamp(parsed["confidenceScore"]),
            "communicationScore": _clamp(parsed["communicationScore"]),
            "technicalScore":     _clamp(tech + boost) if tech is not None else None,
        }'''
    
    new_parse = '''        score_fields = [f for f in LLM_REQUIRED_FIELDS if f.endswith("Score")]
        evidence_fields = [f for f in LLM_REQUIRED_FIELDS if f.endswith("Evidence")]

        for field in score_fields:
            value = parsed.get(field)
            if not isinstance(value, (int, float)) or math.isnan(value):
                logger.warning(f"{provider_name} validation failed: {field} = {value}")
                return None

        for field in evidence_fields:
            value = parsed.get(field)
            if not isinstance(value, str):
                logger.warning(f"{provider_name} validation failed (evidence): {field} = {value}")
                return None

        tech = parsed.get("technicalScore")
        if tech is not None and not isinstance(tech, (int, float)):
            return None
        tech_ev = parsed.get("technicalEvidence")

        boost = DIFFICULTY_BOOST.get(difficulty.upper(), 0)
        return {
            "clarityScore":       _clamp(parsed["clarityScore"] + boost),
            "clarityEvidence":    parsed["clarityEvidence"],
            "structureScore":     _clamp(parsed["structureScore"] + boost),
            "structureEvidence":  parsed["structureEvidence"],
            "depthScore":         _clamp(parsed["depthScore"] + boost),
            "depthEvidence":      parsed["depthEvidence"],
            "confidenceScore":    _clamp(parsed["confidenceScore"]),
            "confidenceEvidence": parsed["confidenceEvidence"],
            "communicationScore": _clamp(parsed["communicationScore"]),
            "communicationEvidence": parsed["communicationEvidence"],
            "technicalScore":     _clamp(tech + boost) if tech is not None else None,
            "technicalEvidence":  tech_ev if tech is not None else None,
        }'''
        
    # The actual loggers are slightly different, so use regex
    
    content = re.sub(
        r'        for field in LLM_REQUIRED_FIELDS:\n\s+value = parsed.get\(field\)\n\s+if not isinstance\(value, \(int, float\)\) or math.isnan\(value\):\n\s+logger.warning\(".*?", field, value\)\n\s+return None\n\n\s+tech = parsed.get\("technicalScore"\)\n\s+if tech is not None and not isinstance\(tech, \(int, float\)\):\n\s+return None\n\n\s+boost = DIFFICULTY_BOOST.get\(difficulty.upper\(\), 0\)\n\s+return \{\n\s+"clarityScore":       _clamp\(parsed\["clarityScore"\] \+ boost\),\n\s+"structureScore":     _clamp\(parsed\["structureScore"\] \+ boost\),\n\s+"depthScore":         _clamp\(parsed\["depthScore"\] \+ boost\),\n\s+"confidenceScore":    _clamp\(parsed\["confidenceScore"\]\),\n\s+"communicationScore": _clamp\(parsed\["communicationScore"\]\),\n\s+"technicalScore":     _clamp\(tech \+ boost\) if tech is not None else None,\n\s+\}',
        lambda m: m.group(0).replace('        for field in LLM_REQUIRED_FIELDS:', '        score_fields = [f for f in LLM_REQUIRED_FIELDS if f.endswith("Score")]\n        evidence_fields = [f for f in LLM_REQUIRED_FIELDS if f.endswith("Evidence")]\n\n        for field in score_fields:').replace(
            'return None\n\n        tech = parsed.get("technicalScore")',
            'return None\n\n        for field in evidence_fields:\n            value = parsed.get(field)\n            if not isinstance(value, str):\n                logger.warning("Validation failed (evidence): %s = %s", field, value)\n                return None\n\n        tech = parsed.get("technicalScore")'
        ).replace(
            'return None\n\n        boost',
            'return None\n        tech_ev = parsed.get("technicalEvidence")\n\n        boost'
        ).replace(
            '"clarityScore":       _clamp(parsed["clarityScore"] + boost),',
            '"clarityScore":       _clamp(parsed["clarityScore"] + boost),\n            "clarityEvidence":    parsed["clarityEvidence"],'
        ).replace(
            '"structureScore":     _clamp(parsed["structureScore"] + boost),',
            '"structureScore":     _clamp(parsed["structureScore"] + boost),\n            "structureEvidence":  parsed["structureEvidence"],'
        ).replace(
            '"depthScore":         _clamp(parsed["depthScore"] + boost),',
            '"depthScore":         _clamp(parsed["depthScore"] + boost),\n            "depthEvidence":      parsed["depthEvidence"],'
        ).replace(
            '"confidenceScore":    _clamp(parsed["confidenceScore"]),',
            '"confidenceScore":    _clamp(parsed["confidenceScore"]),\n            "confidenceEvidence": parsed["confidenceEvidence"],'
        ).replace(
            '"communicationScore": _clamp(parsed["communicationScore"]),',
            '"communicationScore": _clamp(parsed["communicationScore"]),\n            "communicationEvidence": parsed["communicationEvidence"],'
        ).replace(
            '"technicalScore":     _clamp(tech + boost) if tech is not None else None,',
            '"technicalScore":     _clamp(tech + boost) if tech is not None else None,\n            "technicalEvidence":  tech_ev if tech is not None else None,'
        ),
        content
    )

    with open(filepath, 'w') as f:
        f.write(content)

patch_file('apps/api/app/ai/providers/nim_evaluation.py')
patch_file('apps/api/app/ai/providers/openai_evaluation.py')
