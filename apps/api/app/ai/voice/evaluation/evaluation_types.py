import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class EvaluationDimension(str, Enum):
    TECHNICAL = "TECHNICAL"
    COMMUNICATION = "COMMUNICATION"
    BEHAVIORAL = "BEHAVIORAL"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    FRONTEND_FUNDAMENTALS = "FRONTEND_FUNDAMENTALS"
    FRONTEND_ARCHITECTURE = "FRONTEND_ARCHITECTURE"
    PERFORMANCE = "PERFORMANCE"
    SYSTEMS_AND_ARCHITECTURE = "SYSTEMS_AND_ARCHITECTURE"
    DATA_AND_STORAGE = "DATA_AND_STORAGE"
    RELIABILITY = "RELIABILITY"
    PROBLEM_SOLVING = "PROBLEM_SOLVING"

@dataclass
class EvaluatorOutput:
    evaluator_name: str
    dimension: EvaluationDimension
    score: float  # Scale of 1.0 to 5.0 (rubric matched)
    confidence_score: float  # 0.0 to 1.0 (evidence quality indicator)
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TurnEvaluation:
    turn: int
    strength: Optional[str] = None
    issue: Optional[str] = None
    hesitation_score: float = 0.0
    confidence_score: float = 50.0
    verbosity_score: float = 50.0
    drift_score: float = 0.0
    question_text: str = ""
    answer_text: str = ""

@dataclass
class DimensionBreakdown:
    dimension: str
    score: float
    weight: float
    rubric_level: str
    rubric_description: str
    evidence: List[str] = field(default_factory=list)

@dataclass
class EvaluationReport:
    session_id: uuid.UUID
    candidate_id: uuid.UUID
    scores: Dict[EvaluationDimension, float]
    confidence_interval: tuple[float, float]
    evaluator_runs: List[EvaluatorOutput]
    feedback: Dict[str, Any]
    recommendations: List[str]
    trajectory: List[Dict[str, Any]] = field(default_factory=list)
    turn_timeline: List[TurnEvaluation] = field(default_factory=list)
    dimension_breakdowns: List[DimensionBreakdown] = field(default_factory=list)
    behavioral_metrics: Dict[str, Any] = field(default_factory=dict)
    communication_metrics: Dict[str, Any] = field(default_factory=dict)
    technical_metrics: Dict[str, Any] = field(default_factory=dict)
