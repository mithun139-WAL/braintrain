import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

logger = logging.getLogger("llm_evaluator")

@dataclass
class LLMEvaluationScope:
    conceptual_depth: bool = True
    technical_correctness: bool = True
    reasoning_quality: bool = True
    tradeoff_analysis: bool = True
    nuance_assessment: bool = True

LLM_EVALUATION_PROMPT = """You are an objective interview evaluation analyst. Your role is LIMITED to evaluating:

1. CONCEPTUAL DEPTH: How deeply does the candidate understand the concepts they discussed?
2. TECHNICAL CORRECTNESS: Are their technical claims accurate?
3. REASONING QUALITY: How well do they reason through problems?
4. TRADEOFF ANALYSIS: Do they articulate tradeoffs between different approaches?
5. NUANCE: Do they acknowledge complexity and edge cases?

You must NOT evaluate:
- Confidence (determined by language analysis)
- Hesitation (determined by speech analysis)
- Pacing (determined by timing analysis)
- Structure (determined by STAR detection)
- Communication style (determined by behavioral metrics)

For each dimension, provide:
- score (1-5)
- evidence (specific quotes or observations from the candidate's responses)
- reasoning (why this score)

Respond in JSON format with keys: conceptual_depth, technical_correctness, reasoning_quality, tradeoff_analysis, nuance.
Each value should be an object with: score, evidence (list), reasoning.
"""

class LLMRestrictedEvaluator:
    def __init__(self):
        self.scope = LLMEvaluationScope()

    def build_prompt(self, conversation_context: str) -> str:
        return f"{LLM_EVALUATION_PROMPT}\n\nCONVERSATION:\n{conversation_context}"

    def parse_llm_output(self, raw: str) -> Dict[str, Any]:
        import json
        import re

        try:
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except (json.JSONDecodeError, AttributeError):
            logger.warning("llm_evaluator | failed to parse LLM output")
            return {}
