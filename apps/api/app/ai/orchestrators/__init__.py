"""
AI Orchestrators - Deterministic orchestration for interview system.

This package contains the core orchestrators that implement deterministic,
rule-based interview flow with LLM assistance (not LLM control).

Key Principle:
- Intelligence lives in SYSTEM ARCHITECTURE, not in LLM prompts
- LLMs provide observations, orchestrators make decisions
- Deterministic routing prevents hallucinations and ensures predictability

Orchestrators:
- InterviewOrchestrator: Phase transitions, round management, pacing
- TurnOrchestrator: Turn-by-turn action decisions based on answer quality
- ContextOrchestrator: Context assembly with hallucination prevention
- EvaluationOrchestrator: Combined rule-based (60%) + LLM (40%) evaluation
- ModelOrchestrator: Model routing, fallbacks, latency tracking
- RealtimeOrchestrator: Realtime flow with <700ms latency optimization

Policies:
- RoutingPolicy: Task-to-model routing with fallback chains
- FallbackPolicy: Production resilience with degraded modes
- EscalationPolicy: Handling edge cases and candidate struggles
- EvaluationPolicy: Score combination and weighting logic
"""

from app.ai.orchestrators.interview_orchestrator import InterviewOrchestrator
from app.ai.orchestrators.turn_orchestrator import TurnOrchestrator
from app.ai.orchestrators.context_orchestrator import ContextOrchestrator
from app.ai.orchestrators.evaluation_orchestrator import EvaluationOrchestrator
from app.ai.orchestrators.model_orchestrator import ModelOrchestrator
from app.ai.orchestrators.realtime_orchestrator import RealtimeOrchestrator

from app.ai.orchestrators.policies.routing_policy import RoutingPolicy
from app.ai.orchestrators.policies.fallback_policy import FallbackPolicy
from app.ai.orchestrators.policies.escalation_policy import EscalationPolicy
from app.ai.orchestrators.policies.evaluation_policy import EvaluationPolicy

from app.ai.orchestrators.integration import (
    OrchestratorHub,
    create_orchestrator_hub,
    attach_orchestrators_to_agent,
)

__all__ = [
    # Orchestrators
    "InterviewOrchestrator",
    "TurnOrchestrator",
    "ContextOrchestrator",
    "EvaluationOrchestrator",
    "ModelOrchestrator",
    "RealtimeOrchestrator",
    
    # Policies
    "RoutingPolicy",
    "FallbackPolicy",
    "EscalationPolicy",
    "EvaluationPolicy",
    
    # Integration
    "OrchestratorHub",
    "create_orchestrator_hub",
    "attach_orchestrators_to_agent",
]


# Version info
__version__ = "1.0.0"
__author__ = "BrainTrain Team"
__description__ = "Deterministic AI Orchestration for Interview System"
