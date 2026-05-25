import math
from typing import List, Dict, Tuple
from app.ai.voice.evaluation.evaluation_types import EvaluatorOutput, EvaluationDimension

class ScoringEngine:
    @staticmethod
    def calculate_dimension_scores(
        outputs: List[EvaluatorOutput],
        consistency_multiplier: float = 1.0
    ) -> Tuple[Dict[EvaluationDimension, float], Tuple[float, float]]:
        """
        Aggregates outputs by dimension using confidence-weighted averaging.
        Applies a consistency multiplier to the overall score.
        Returns:
            (dimension_scores, (confidence_interval_low, confidence_interval_high))
        """
        grouped: Dict[EvaluationDimension, List[EvaluatorOutput]] = {}
        for out in outputs:
            grouped.setdefault(out.dimension, []).append(out)

        scores: Dict[EvaluationDimension, float] = {}
        total_confidence = 0.0
        weighted_sum_all = 0.0
        
        # Calculate dimension-specific scores
        for dim, run_list in grouped.items():
            dim_weighted_sum = 0.0
            dim_confidence_sum = 0.0
            
            for run in run_list:
                # Weighted by evaluator's self-assessed confidence
                weight = max(0.1, run.confidence_score)
                dim_weighted_sum += run.score * weight
                dim_confidence_sum += weight

            dim_score = dim_weighted_sum / dim_confidence_sum if dim_confidence_sum > 0 else 3.0
            # Apply consistency penalty to technical scores
            if dim == EvaluationDimension.TECHNICAL or dim == EvaluationDimension.SYSTEM_DESIGN:
                dim_score = max(1.0, min(5.0, dim_score * consistency_multiplier))

            scores[dim] = round(dim_score, 2)
            
            total_confidence += dim_confidence_sum
            weighted_sum_all += dim_weighted_sum

        # Calculate confidence interval bounds
        overall_avg = (weighted_sum_all / total_confidence) if total_confidence > 0 else 3.0
        overall_avg = max(1.0, min(5.0, overall_avg * consistency_multiplier))
        
        # Simple standard error of the mean for confidence bounds
        variance = 0.0
        count = len(outputs)
        if count > 1:
            variance = sum((o.score - overall_avg) ** 2 for o in outputs) / (count - 1)
        
        std_error = math.sqrt(variance / count) if count > 0 else 0.5
        ci_low = max(1.0, round(overall_avg - 1.96 * std_error, 2))
        ci_high = min(5.0, round(overall_avg + 1.96 * std_error, 2))

        return scores, (ci_low, ci_high)
