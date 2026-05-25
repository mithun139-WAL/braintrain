from typing import Dict, Any, Optional
from app.ai.voice.evaluation.evaluation_types import EvaluationDimension

class RubricEngine:
    def __init__(self):
        # Default rubric schema mapped strictly to dimension requirements
        self.rubrics = {
            EvaluationDimension.TECHNICAL: {
                "weight": 0.35,
                "criteria": "Correctness, depth, and tradeoff/scalability awareness.",
                "levels": {
                    1: {"name": "Shallow", "desc": "Lacks conceptual clarity or simple correctness."},
                    2: {"name": "Moderate", "desc": "Explains basics but misses depth or edge cases."},
                    3: {"name": "Strong", "desc": "Thorough understanding of mechanics and basic tradeoffs."},
                    4: {"name": "Advanced", "desc": "Applies deep tradeoff reasoning under constraints (e.g. CAP)."},
                    5: {"name": "Expert", "desc": "Designs complex high-performance systems with math models."}
                }
            },
            EvaluationDimension.COMMUNICATION: {
                "weight": 0.20,
                "criteria": "Clarity, answer structure (STAR method), and verbosity control.",
                "levels": {
                    1: {"name": "Disorganized", "desc": "Answers drift, lack structure, or contain high filler density."},
                    2: {"name": "Understandable", "desc": "Coherent response but verbose or lacks clear summary."},
                    3: {"name": "Structured", "desc": "Follows a logical flow (e.g. context -> resolution)."},
                    4: {"name": "Precise", "desc": "Highly concise, uses correct nomenclature, explain abstractions easily."},
                    5: {"name": "Eloquent", "desc": "Impeccable sequencing, engages panelists perfectly, zero noise."}
                }
            },
            EvaluationDimension.BEHAVIORAL: {
                "weight": 0.20,
                "criteria": "Confidence levels, hesitation recovery, and adaptability to hints.",
                "levels": {
                    1: {"name": "Fragile", "desc": "Frequent long pauses (>3s), drops in confidence, collapses under pressure."},
                    2: {"name": "Hesitant", "desc": "Occasional long silence pauses but recovers with assistance."},
                    3: {"name": "Steady", "desc": "Stable delivery pacing, handles interruptions cleanly."},
                    4: {"name": "Adaptable", "desc": "Incorporates interviewer prompts/hints and recalibrates on-the-fly."},
                    5: {"name": "Resilient", "desc": "Maintains absolute composure under high-stress questions or conflict."}
                }
            },
            EvaluationDimension.SYSTEM_DESIGN: {
                "weight": 0.25,
                "criteria": "Scalability, bottleneck isolation, reliability, and caching design.",
                "levels": {
                    1: {"name": "Naive", "desc": "Suggests scaling up or standard database updates for all limits."},
                    2: {"name": "Familiar", "desc": "Mentions horizontal scaling and caches but cannot explain partitioning."},
                    3: {"name": "Systems Aware", "desc": "Designs proper load balanced, partitioned, and cached tiers."},
                    4: {"name": "Resilient Design", "desc": "Accounts for failures, queues, replication lag, and backpressure."},
                    5: {"name": "Production Master", "desc": "Formulates fully redundant distributed architectures with clear bottleneck mitigation."}
                }
            }
        }

    def get_rubric(self, dimension: EvaluationDimension) -> Dict[str, Any]:
        return self.rubrics.get(dimension, {})

    def get_level_info(self, dimension: EvaluationDimension, score: float) -> Dict[str, str]:
        """
        Maps a float score (1.0 to 5.0) to its nearest discrete rubric level details.
        """
        rubric = self.get_rubric(dimension)
        if not rubric:
            return {"name": "Unknown", "desc": "No rubric defined."}
        
        level_idx = max(1, min(5, round(score)))
        return rubric["levels"].get(level_idx, {"name": "Unknown", "desc": "No level definition found."})
