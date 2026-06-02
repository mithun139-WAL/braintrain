"""
Interview Orchestrator - Central controller for interview lifecycle.

This is the primary orchestrator that manages interview phases, rounds,
transitions, pacing, and overall interview flow.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

from pydantic import BaseModel

from app.ai.orchestrators.contracts.interview_contracts import (
    InterviewPhase,
    InterviewDomain,
    ChallengeLevel,
    InterviewerMood,
    InterviewConfig,
    PhaseTransition,
    RoundCompletion,
    InterviewConstraints
)
from app.ai.orchestrators.state.interview_runtime_state import (
    InterviewRuntimeState,
    CandidateRuntimeState,
    PhaseState
)

logger = logging.getLogger(__name__)


class InterviewOrchestrator:
    """
    Central orchestrator for interview lifecycle management.
    
    Responsibilities:
    - Phase transitions
    - Round management
    - Challenge level adjustment
    - Interviewer strategy selection
    - Pacing control
    - Completion detection
    """
    
    def __init__(self, config: InterviewConfig):
        self.config = config
        self.state: Optional[InterviewRuntimeState] = None
        self.phase_states: Dict[InterviewPhase, PhaseState] = {}
        
        # Phase configuration
        self.phase_config = self._build_phase_config()
        
        logger.info(f"Initialized InterviewOrchestrator with domain={config.domain}")
    
    def _build_phase_config(self) -> Dict[InterviewPhase, Dict[str, Any]]:
        """Build configuration for each phase."""
        return {
            InterviewPhase.INTRODUCTION: {
                "duration_minutes": 3,
                "min_questions": 1,
                "topics": ["introduction", "background"],
                "challenge_level": ChallengeLevel.EASY,
                "can_skip": False
            },
            InterviewPhase.RESUME_DISCUSSION: {
                "duration_minutes": 10,
                "min_questions": 3,
                "topics": ["experience", "projects", "technologies"],
                "challenge_level": ChallengeLevel.MODERATE,
                "can_skip": False
            },
            InterviewPhase.TECHNICAL_ROUND_1: {
                "duration_minutes": 15,
                "min_questions": 4,
                "topics": self._get_domain_topics(),
                "challenge_level": ChallengeLevel.MODERATE,
                "can_skip": False
            },
            InterviewPhase.TECHNICAL_ROUND_2: {
                "duration_minutes": 15,
                "min_questions": 4,
                "topics": self._get_domain_topics(),
                "challenge_level": ChallengeLevel.CHALLENGING,
                "can_skip": True
            },
            InterviewPhase.BEHAVIORAL: {
                "duration_minutes": 10,
                "min_questions": 2,
                "topics": ["teamwork", "conflict", "leadership", "failure"],
                "challenge_level": ChallengeLevel.MODERATE,
                "can_skip": True
            },
            InterviewPhase.WRAP_UP: {
                "duration_minutes": 2,
                "min_questions": 1,
                "topics": ["questions", "next_steps"],
                "challenge_level": ChallengeLevel.EASY,
                "can_skip": False
            }
        }
    
    def _get_domain_topics(self) -> List[str]:
        """Get topics based on interview domain."""
        domain_topics = {
            InterviewDomain.FRONTEND: [
                "react", "javascript", "css", "state_management",
                "component_design", "performance", "accessibility"
            ],
            InterviewDomain.BACKEND: [
                "apis", "databases", "authentication", "caching",
                "scalability", "services", "async_processing"
            ],
            InterviewDomain.SYSTEM_DESIGN: [
                "architecture", "scalability", "distributed_systems",
                "data_modeling", "tradeoffs", "consistency"
            ],
            InterviewDomain.BEHAVIORAL: [
                "teamwork", "conflict_resolution", "leadership",
                "ownership", "decision_making", "failure_handling"
            ]
        }
        return domain_topics.get(self.config.domain, [])
    
    async def start_interview(
        self,
        session_id: str,
        candidate_id: str,
        journey_id: Optional[str] = None
    ) -> InterviewRuntimeState:
        """Start a new interview session."""
        
        logger.info(f"Starting interview session={session_id} candidate={candidate_id}")
        
        # Initialize state
        self.state = InterviewRuntimeState(
            session_id=session_id,
            candidate_id=candidate_id,
            journey_id=journey_id,
            current_phase=InterviewPhase.INTRODUCTION,
            domain=self.config.domain,
            current_challenge_level=ChallengeLevel.MODERATE,
            interviewer_mood=InterviewerMood.NEUTRAL
        )
        
        # Initialize first phase
        await self._enter_phase(InterviewPhase.INTRODUCTION)
        
        return self.state
    
    async def _enter_phase(self, phase: InterviewPhase) -> None:
        """Enter a new phase."""
        if not self.state:
            raise ValueError("Interview state not initialized")
        
        phase_cfg = self.phase_config.get(phase, {})
        
        # Create phase state
        phase_state = PhaseState(
            phase=phase,
            session_id=self.state.session_id,
            target_duration_minutes=phase_cfg.get("duration_minutes", 15),
            min_questions_required=phase_cfg.get("min_questions", 3),
            topics_to_cover=phase_cfg.get("topics", [])
        )
        
        self.phase_states[phase] = phase_state
        
        # Update interview state
        self.state.current_phase = phase
        self.state.phase_start_time = datetime.utcnow()
        self.state.phase_history.append(phase.value)
        self.state.current_challenge_level = phase_cfg.get("challenge_level", ChallengeLevel.MODERATE)
        
        logger.info(f"Entered phase {phase.value} session={self.state.session_id}")
    
    async def transition_to_phase(
        self,
        target_phase: InterviewPhase,
        reason: str
    ) -> PhaseTransition:
        """Transition to a new phase."""
        if not self.state:
            raise ValueError("Interview state not initialized")
        
        current_phase = self.state.current_phase
        
        # Validate transition
        if not self._is_valid_transition(current_phase, target_phase):
            logger.warning(
                f"Invalid phase transition: {current_phase.value} -> {target_phase.value}"
            )
            raise ValueError(f"Invalid phase transition to {target_phase.value}")
        
        # Complete current phase
        current_phase_state = self.phase_states.get(current_phase)
        if current_phase_state:
            current_phase_state.is_complete = True
            current_phase_state.completion_reason = reason
        
        # Create transition record
        transition = PhaseTransition(
            from_phase=current_phase,
            to_phase=target_phase,
            reason=reason,
            confidence=0.9
        )
        
        # Enter new phase
        await self._enter_phase(target_phase)
        
        logger.info(
            f"Phase transition: {current_phase.value} -> {target_phase.value} "
            f"reason='{reason}' session={self.state.session_id}"
        )
        
        return transition
    
    def _is_valid_transition(self, from_phase: InterviewPhase, to_phase: InterviewPhase) -> bool:
        """Check if phase transition is valid."""
        # Define valid transitions
        valid_transitions = {
            InterviewPhase.INTRODUCTION: [
                InterviewPhase.RESUME_DISCUSSION,
                InterviewPhase.TECHNICAL_ROUND_1
            ],
            InterviewPhase.RESUME_DISCUSSION: [
                InterviewPhase.TECHNICAL_ROUND_1,
                InterviewPhase.BEHAVIORAL,
                InterviewPhase.WRAP_UP
            ],
            InterviewPhase.TECHNICAL_ROUND_1: [
                InterviewPhase.TECHNICAL_ROUND_2,
                InterviewPhase.BEHAVIORAL,
                InterviewPhase.WRAP_UP
            ],
            InterviewPhase.TECHNICAL_ROUND_2: [
                InterviewPhase.BEHAVIORAL,
                InterviewPhase.SYSTEM_DESIGN,
                InterviewPhase.WRAP_UP
            ],
            InterviewPhase.SYSTEM_DESIGN: [
                InterviewPhase.BEHAVIORAL,
                InterviewPhase.WRAP_UP
            ],
            InterviewPhase.BEHAVIORAL: [
                InterviewPhase.TECHNICAL_ROUND_2,
                InterviewPhase.WRAP_UP
            ],
            InterviewPhase.WRAP_UP: [
                InterviewPhase.COMPLETE
            ]
        }
        
        allowed = valid_transitions.get(from_phase, [])
        return to_phase in allowed
    
    async def should_end_phase(self) -> tuple[bool, str]:
        """
        Determine if current phase should end.
        
        Returns:
            (should_end, reason)
        """
        if not self.state:
            return False, "No state"
        
        current_phase = self.state.current_phase
        phase_state = self.phase_states.get(current_phase)
        
        if not phase_state:
            return False, "No phase state"
        
        # Calculate elapsed time
        elapsed_seconds = (datetime.utcnow() - phase_state.started_at).total_seconds()
        phase_state.elapsed_seconds = int(elapsed_seconds)
        
        target_duration_seconds = phase_state.target_duration_minutes * 60
        
        # Reason 1: Time limit reached
        if elapsed_seconds >= target_duration_seconds:
            return True, "time_limit_reached"
        
        # Reason 2: Minimum questions asked and topics covered
        if phase_state.questions_asked_in_phase >= phase_state.min_questions_required:
            coverage = len(phase_state.topics_covered) / max(len(phase_state.topics_to_cover), 1)
            if coverage >= 0.7:  # 70% topic coverage
                return True, "objectives_met"
        
        # Reason 3: Candidate struggling severely (move to easier phase or wrap up)
        if len(phase_state.phase_scores) >= 3:
            avg_score = sum(phase_state.phase_scores) / len(phase_state.phase_scores)
            if avg_score < 30 and phase_state.questions_asked_in_phase >= 2:
                return True, "candidate_struggling"
        
        # Reason 4: Candidate excelling (move to harder phase)
        if len(phase_state.phase_scores) >= 3:
            avg_score = sum(phase_state.phase_scores) / len(phase_state.phase_scores)
            if avg_score > 85 and phase_state.questions_asked_in_phase >= phase_state.min_questions_required:
                return True, "candidate_excelling"
        
        return False, ""
    
    async def compute_next_phase(self, completion_reason: str) -> InterviewPhase:
        """
        Compute the next appropriate phase.
        
        Deterministic logic based on:
        - current phase
        - completion reason
        - candidate performance
        - time remaining
        - domain constraints
        """
        if not self.state:
            raise ValueError("No state")
        
        current_phase = self.state.current_phase
        phase_state = self.phase_states.get(current_phase)
        
        # Calculate time remaining
        elapsed_total = (datetime.utcnow() - self.state.started_at).total_seconds() / 60
        time_remaining = self.config.target_duration_minutes - elapsed_total
        
        # Decision logic
        if completion_reason == "candidate_struggling":
            # Struggling: simplify or wrap up
            if current_phase == InterviewPhase.TECHNICAL_ROUND_1:
                return InterviewPhase.BEHAVIORAL if time_remaining > 10 else InterviewPhase.WRAP_UP
            elif current_phase == InterviewPhase.TECHNICAL_ROUND_2:
                return InterviewPhase.BEHAVIORAL if time_remaining > 10 else InterviewPhase.WRAP_UP
            else:
                return InterviewPhase.WRAP_UP
        
        elif completion_reason == "candidate_excelling":
            # Excelling: increase challenge
            if current_phase == InterviewPhase.TECHNICAL_ROUND_1 and time_remaining > 15:
                return InterviewPhase.TECHNICAL_ROUND_2
            elif current_phase == InterviewPhase.TECHNICAL_ROUND_2 and time_remaining > 10:
                return InterviewPhase.SYSTEM_DESIGN if self.config.domain in [
                    InterviewDomain.BACKEND, InterviewDomain.FULLSTACK
                ] else InterviewPhase.BEHAVIORAL
            else:
                return InterviewPhase.BEHAVIORAL if time_remaining > 10 else InterviewPhase.WRAP_UP
        
        else:
            # Standard progression
            progression = {
                InterviewPhase.INTRODUCTION: InterviewPhase.RESUME_DISCUSSION,
                InterviewPhase.RESUME_DISCUSSION: InterviewPhase.TECHNICAL_ROUND_1,
                InterviewPhase.TECHNICAL_ROUND_1: (
                    InterviewPhase.TECHNICAL_ROUND_2 if time_remaining > 15
                    else (InterviewPhase.BEHAVIORAL if time_remaining > 10 else InterviewPhase.WRAP_UP)
                ),
                InterviewPhase.TECHNICAL_ROUND_2: (
                    InterviewPhase.BEHAVIORAL if time_remaining > 10
                    else InterviewPhase.WRAP_UP
                ),
                InterviewPhase.SYSTEM_DESIGN: (
                    InterviewPhase.BEHAVIORAL if time_remaining > 10
                    else InterviewPhase.WRAP_UP
                ),
                InterviewPhase.BEHAVIORAL: InterviewPhase.WRAP_UP,
                InterviewPhase.WRAP_UP: InterviewPhase.COMPLETE
            }
            
            return progression.get(current_phase, InterviewPhase.WRAP_UP)
    
    async def determine_challenge_level(
        self,
        candidate_state: CandidateRuntimeState
    ) -> ChallengeLevel:
        """
        Determine appropriate challenge level based on candidate performance.
        
        Deterministic logic:
        - High performers get harder questions
        - Struggling candidates get easier questions
        - Stable performance maintains level
        """
        performance = candidate_state.current_performance_score
        trend = candidate_state.performance_trend
        
        # Performance-based challenge adjustment
        if performance >= 80:
            if trend == "improving":
                return ChallengeLevel.EXTREME
            else:
                return ChallengeLevel.DIFFICULT
        elif performance >= 65:
            if trend == "improving":
                return ChallengeLevel.DIFFICULT
            else:
                return ChallengeLevel.CHALLENGING
        elif performance >= 50:
            return ChallengeLevel.MODERATE
        elif performance >= 35:
            return ChallengeLevel.EASY
        else:
            # Candidate struggling significantly
            return ChallengeLevel.EASY
    
    async def determine_interviewer_strategy(
        self,
        candidate_state: CandidateRuntimeState
    ) -> tuple[InterviewerMood, str]:
        """
        Determine interviewer mood and strategy.
        
        Returns:
            (mood, strategy_name)
        """
        performance = candidate_state.current_performance_score
        confidence = candidate_state.current_confidence_score
        frustration = candidate_state.frustration_level
        
        # Candidate struggling and frustrated: be supportive
        if performance < 40 and frustration > 0.6:
            return InterviewerMood.SUPPORTIVE, "supportive_recovery"
        
        # Candidate struggling but composed: be encouraging
        elif performance < 50 and confidence < 0.5:
            return InterviewerMood.SUPPORTIVE, "encouraging"
        
        # Candidate doing well: be probing
        elif performance > 75:
            if self.config.company_name and self.config.company_name.lower() in ["amazon", "meta", "netflix"]:
                return InterviewerMood.SKEPTICAL, "deep_probing"
            else:
                return InterviewerMood.INQUISITIVE, "standard_probing"
        
        # Candidate performing excellently: be impressed but challenging
        elif performance > 85:
            return InterviewerMood.IMPRESSED, "challenge_excellence"
        
        # Standard performance: neutral
        else:
            return InterviewerMood.NEUTRAL, "standard"
    
    async def get_interview_constraints(self) -> InterviewConstraints:
        """
        Get domain-specific interview constraints.
        
        Critical for preventing topic drift and hallucinations.
        """
        domain_constraints = {
            InterviewDomain.FRONTEND: InterviewConstraints(
                allowed_topics=[
                    "react", "vue", "angular", "javascript", "typescript",
                    "css", "html", "state_management", "components", "hooks",
                    "performance", "accessibility", "responsive_design"
                ],
                forbidden_topics=[
                    "distributed_systems", "database_sharding", "consensus",
                    "load_balancing", "microservices_architecture", "message_queues"
                ],
                enforce_star_method=False
            ),
            InterviewDomain.BACKEND: InterviewConstraints(
                allowed_topics=[
                    "apis", "rest", "graphql", "databases", "sql", "nosql",
                    "caching", "authentication", "authorization", "services",
                    "async_processing", "queues", "workers"
                ],
                forbidden_topics=[
                    "react_components", "css_styling", "dom_manipulation",
                    "browser_events", "responsive_design"
                ],
                enforce_star_method=False
            ),
            InterviewDomain.BEHAVIORAL: InterviewConstraints(
                allowed_topics=[
                    "teamwork", "conflict", "leadership", "ownership",
                    "decision_making", "failure", "success", "communication",
                    "prioritization", "stakeholder_management"
                ],
                forbidden_topics=[
                    "coding", "algorithms", "system_design", "technical_implementation"
                ],
                enforce_star_method=True
            )
        }
        
        return domain_constraints.get(
            self.config.domain,
            InterviewConstraints()
        )
    
    async def update_progress(self) -> float:
        """
        Update and return interview progress percentage.
        
        Based on:
        - time elapsed
        - phases completed
        - questions asked
        """
        if not self.state:
            return 0.0
        
        # Time-based progress (40% weight)
        elapsed_minutes = (datetime.utcnow() - self.state.started_at).total_seconds() / 60
        time_progress = min(100.0, (elapsed_minutes / self.config.target_duration_minutes) * 100)
        
        # Phase-based progress (30% weight)
        phase_order = [
            InterviewPhase.INTRODUCTION,
            InterviewPhase.RESUME_DISCUSSION,
            InterviewPhase.TECHNICAL_ROUND_1,
            InterviewPhase.TECHNICAL_ROUND_2,
            InterviewPhase.BEHAVIORAL,
            InterviewPhase.WRAP_UP,
            InterviewPhase.COMPLETE
        ]
        current_phase_index = phase_order.index(self.state.current_phase)
        phase_progress = (current_phase_index / len(phase_order)) * 100
        
        # Question-based progress (30% weight)
        questions_progress = min(
            100.0,
            (self.state.questions_asked / self.config.max_questions_per_round / 3) * 100
        )
        
        # Weighted combination
        total_progress = (
            time_progress * 0.4 +
            phase_progress * 0.3 +
            questions_progress * 0.3
        )
        
        self.state.interview_progress_percent = min(100.0, total_progress)
        return self.state.interview_progress_percent
    
    async def should_stop_followups(self) -> tuple[bool, str]:
        """
        Determine if follow-up questions should stop.
        
        Prevents infinite follow-up loops.
        """
        if not self.state:
            return True, "no_state"
        
        # Max depth reached
        if self.state.consecutive_followups >= self.config.max_followup_depth:
            return True, "max_depth_reached"
        
        # Total follow-ups limit
        if self.state.followups_asked >= self.config.max_questions_per_round * 2:
            return True, "total_followup_limit"
        
        # Time running out
        elapsed_minutes = (datetime.utcnow() - self.state.started_at).total_seconds() / 60
        time_remaining = self.config.target_duration_minutes - elapsed_minutes
        if time_remaining < 5:
            return True, "time_running_out"
        
        return False, ""
