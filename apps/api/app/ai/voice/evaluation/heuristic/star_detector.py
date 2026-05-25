import re
from typing import List, Dict, Any
from app.ai.voice.evaluation.heuristic.base_heuristic import HeuristicEvaluator

STAR_SIGNALS = {
    "situation": [
        r"\bsituation\b", r"\bcontext\b", r"\bscenario\b", r"\bcircumstances\b",
        r"\bwas working (as|on|in)\b", r"\bwas part of\b", r"\bthe project\b",
        r"\bthe team\b", r"\bthe company\b", r"\bthe product\b",
    ],
    "task": [
        r"\btask\b", r"\bgoal\b", r"\bobjective\b", r"\bresponsibility\b",
        r"\bneeded to\b", r"\bhad to\b", r"\bwas supposed to\b", r"\bwas asked to\b",
        r"\bwas tasked with\b", r"\byour goal\b", r"\bthe requirement\b",
    ],
    "action": [
        r"\bI\s+(designed|built|created|implemented|developed|architected)\b",
        r"\bI\s+(led|managed|coordinated|drove|initiated)\b",
        r"\bwe\s+(designed|built|created|implemented|developed|migrated)\b",
        r"\bI\s+(wrote|configured|deployed|set up|refactored|optimized)\b",
        r"\bmy approach\b", r"\bthe solution\b", r"\bwe decided to\b",
    ],
    "result": [
        r"\bas a result\b", r"\bresulted in\b", r"\boutcome\b", r"\bimpact\b",
        r"\bleading to\b", r"\bwhich led to\b", r"\bimproved\b", r"\breduced\b",
        r"\bincreased\b", r"\bsaved\b", r"\bachieved\b", r"\bdelivered\b",
        r"\bended up\b", r"\beventually\b",
    ],
}

class STARDetector(HeuristicEvaluator):
    @property
    def name(self) -> str:
        return "star_detector"

    def analyze(self, question: str, answer: str, **kwargs) -> Dict[str, Any]:
        answer_lower = answer.lower()
        components = {}
        for component, patterns in STAR_SIGNALS.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, answer_lower)
                if found:
                    matches.extend(found)
            components[component] = {
                "detected": len(matches) > 0,
                "count": len(matches),
                "matches": matches[:3],
            }

        detected = sum(1 for c in components.values() if c["detected"])
        completeness = detected / 4.0

        return {
            "star_detected": detected >= 2,
            "completeness_score": round(completeness * 100, 1),
            "components_detected": detected,
            "components": components,
        }

    def evidence(self, result: Dict[str, Any]) -> List[str]:
        evidence = []
        comps = result["components"]
        if comps["situation"]["detected"]:
            evidence.append("STAR: Situation component detected")
        if comps["task"]["detected"]:
            evidence.append("STAR: Task component detected")
        if comps["action"]["detected"]:
            evidence.append("STAR: Action component detected")
        if comps["result"]["detected"]:
            evidence.append("STAR: Result component detected")
        if result["star_detected"]:
            evidence.append(f"STAR structure detected with {result['components_detected']}/4 components")
        else:
            evidence.append(f"STAR structure not fully formed: {result['components_detected']}/4 components")
        return evidence
