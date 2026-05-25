# BrainTrain Confidence Coaching System Architecture

**Version:** 2.0  
**Status:** Implementation in Progress  
**Last Updated:** 2026-05-25

---

## 1. Executive Summary

This document describes the architectural transformation of BrainTrain from an AI interview evaluator into a **Human Performance Transformation System** focused on:

- Increasing candidate confidence
- Improving communication clarity
- Reducing interview panic
- Building strategic thinking
- Improving pressure handling
- Developing structured expression under stress

### Core Principle

**BrainTrain should feel like: "A system helping humans become stronger communicators under pressure."**

**NOT: "A machine judging humans."**

---

## 2. System Architecture Overview

### 2.1 Three Core Pillars

```
┌─────────────────────────────────────────────────────────────┐
│                    BRAINTRAIN 2.0                           │
│            Human Performance Transformation System           │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PILLAR 1    │    │  PILLAR 2    │    │  PILLAR 3    │
│              │    │              │    │              │
│ Mind State   │    │ Confidence   │    │  Pressure    │
│   System     │    │   Engine     │    │ Conditioning │
│              │    │              │    │              │
│ Psychological│    │  Adaptive    │    │  Resilience  │
│   Modeling   │    │   Coaching   │    │   Training   │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 2.2 Integration with Existing Architecture

The new systems integrate with existing BrainTrain infrastructure:

- **Deterministic Orchestrators** - Enhanced with psychological awareness
- **Realtime Pipeline** - Extended with confidence signals
- **Evaluation Pipeline** - Augmented with mind state context
- **RAG System** - Enhanced with recovery content
- **Event Bus** - New psychological events
- **OrchestratorHub** - Coordination layer for new engines

---

## 3. PILLAR 1: Candidate Mind State System

### 3.1 Overview

Creates a persistent, evolving psychological-performance model for every candidate that serves as the **central intelligence layer** for adaptive interviewing.

### 3.2 CandidateMindState Entity

**Database Model:** `candidate_mind_states`

#### Core Psychological Metrics (0-100 normalized)

| Metric | Description | Signals |
|--------|-------------|---------|
| `confidence_level` | Overall confidence in interview situations | Speaking continuity, answer completion, ownership language |
| `stress_tolerance` | Ability to handle pressure without performance degradation | Pause patterns, filler words, recovery speed |
| `communication_clarity` | Ability to express thoughts clearly and structurally | Answer structure, logical flow, conciseness |
| `memory_recall_strength` | Ability to recall experiences/knowledge under pressure | Detail richness, specificity, consistency |
| `strategic_thinking` | Ability to analyze tradeoffs and think systematically | Tradeoff mentions, alternatives considered, depth |
| `emotional_stability` | Consistency of performance across stress levels | Score variance, recovery patterns, panic detection |
| `hesitation_recovery` | Ability to recover after confusion/hesitation | Recovery after hints, improvement in retries |
| `storytelling_ability` | Ability to structure narratives (STAR, etc.) | Story structure, context-action-result flow |
| `technical_depth_confidence` | Confidence when discussing technical topics | Technical vocabulary, specificity, detail level |
| `pressure_handling` | Performance under interruptions/challenges | Response to interruptions, clarity under pressure |
| `behavioral_authenticity` | Authenticity in behavioral responses | Specificity, emotional consistency, detail richness |
| `response_structure` | Ability to structure answers logically | Introduction-body-conclusion, logical transitions |
| `filler_word_control` | Control over filler words (um, uh, like, you know) | Filler word density, improvement over time |
| `confidence_under_pressure` | Maintains composure when challenged | Response quality after challenges |
| `executive_presence` | Professional communication style | Ownership language, clarity, decisiveness |
| `recovery_speed` | Speed of recovery after mistakes/confusion | Time to stabilization, quality improvement |
| `freeze_response_risk` | Risk of cognitive freeze under stress | Pause duration, fragmentation, latency |
| `cognitive_load_tolerance` | Ability to handle complex multi-part questions | Performance on complex questions |
| `speaking_consistency` | Consistency of speaking patterns | Variance in speaking metrics |

#### Trend Tracking

```sql
-- Rolling averages (last N sessions)
rolling_average_scores JSONB

-- Improvement velocity (rate of change)
improvement_velocity JSONB

-- Trend directions
confidence_trend VARCHAR  -- improving, stable, declining
pressure_trend VARCHAR
communication_trend VARCHAR
```

#### Topic Performance

```sql
-- Topics where candidate struggles
weak_topics JSONB  -- [{topic: "system_design", score: 45, sessions: 3}]

-- Topics where candidate excels
strong_topics JSONB

-- Recurring failure patterns
recurring_failures JSONB  -- [{pattern: "rambling", frequency: 0.7}]

-- Recurring strengths
recurring_strengths JSONB  -- [{pattern: "clear_structure", frequency: 0.8}]
```

#### Metadata

```sql
candidate_id UUID (FK)
last_updated_at TIMESTAMP
created_at TIMESTAMP
session_count INTEGER
total_turns_analyzed INTEGER
```

### 3.3 MindStateEngine

**Location:** `/apps/api/app/ai/coaching/mind_state_engine.py`

#### Responsibilities

- Update candidate psychological state after every turn
- Detect growth patterns across sessions
- Detect panic/confidence collapse patterns
- Calculate improvement velocities
- Identify recovery abilities

#### Core Methods

```python
class MindStateEngine:
    async def update_from_turn(
        self,
        candidate_id: str,
        turn_data: TurnData,
        evaluation: UnifiedEvaluation,
        transcript: str,
        pauses: List[Pause],
        speaking_metrics: SpeakingMetrics
    ) -> CandidateMindState:
        """Update mind state from a single turn."""
        
    async def update_from_session(
        self,
        candidate_id: str,
        session_id: str
    ) -> CandidateMindState:
        """Aggregate session-level updates."""
        
    def calculate_confidence_delta(
        self,
        current_state: CandidateMindState,
        turn_signals: TurnSignals
    ) -> float:
        """Calculate confidence change from turn."""
        
    def calculate_pressure_delta(
        self,
        current_state: CandidateMindState,
        pressure_events: List[PressureEvent]
    ) -> float:
        """Calculate pressure tolerance change."""
        
    def calculate_growth_velocity(
        self,
        historical_states: List[CandidateMindState]
    ) -> Dict[str, float]:
        """Calculate improvement velocity for each metric."""
        
    def detect_freeze_response(
        self,
        pauses: List[Pause],
        fragmentation: float,
        latency: float
    ) -> FreezeDetection:
        """Detect cognitive freeze patterns."""
        
    def detect_recovery_pattern(
        self,
        turn_sequence: List[TurnData]
    ) -> RecoveryPattern:
        """Detect recovery after struggle."""
        
    def detect_confidence_spikes(
        self,
        state_history: List[CandidateMindState]
    ) -> List[ConfidenceSpike]:
        """Detect sudden confidence improvements."""
        
    def detect_confidence_collapse(
        self,
        state_history: List[CandidateMindState],
        recent_turns: List[TurnData]
    ) -> Optional[ConfidenceCollapse]:
        """Detect confidence collapse patterns."""
```

### 3.4 Signal Extraction Pipeline

**Location:** `/apps/api/app/ai/coaching/signal_extraction.py`

#### Behavioral Signals

**Confidence Signals**

```python
class ConfidenceSignalExtractor:
    def extract_from_transcript(self, transcript: str) -> ConfidenceSignals:
        # Ownership language: "I did", "I built", "I decided"
        # Hedge language: "kind of", "sort of", "maybe"
        # Definitive statements vs. uncertain language
        # First-person vs. passive voice
        
    def extract_from_pauses(self, pauses: List[Pause]) -> PauseSignals:
        # Pause duration distribution
        # Mid-sentence pauses (confusion)
        # Pause clustering (stress)
        # Pause reduction over time (improvement)
        
    def extract_from_speaking_metrics(
        self, 
        metrics: SpeakingMetrics
    ) -> SpeakingSignals:
        # Filler word density
        # Speaking rate consistency
        # Volume consistency
        # Vocal fry / upspeak patterns
```

**Stress Signals**

```python
class StressSignalExtractor:
    def detect_panic_markers(self, turn_data: TurnData) -> PanicMarkers:
        # Rapid speech acceleration
        # Filler word clustering
        # Fragmented answers
        # Abandoning sentence mid-thought
        # Repetitive restarts
        
    def detect_cognitive_overload(
        self,
        response_latency: float,
        answer_coherence: float,
        question_complexity: float
    ) -> CognitiveLoadSignal:
        # High latency + low coherence = overload
        # Simplification attempts
        # Requesting clarification
```

**Recovery Signals**

```python
class RecoverySignalExtractor:
    def detect_recovery_after_hint(
        self,
        before_hint: TurnData,
        after_hint: TurnData
    ) -> RecoverySignal:
        # Quality improvement
        # Structure improvement
        # Confidence return
        
    def detect_self_correction(
        self,
        transcript: str
    ) -> List[SelfCorrection]:
        # "Actually, let me clarify..."
        # "To correct that..."
        # "More accurately..."
```

#### Signal Aggregation

```python
class SignalAggregator:
    def aggregate_turn_signals(
        self,
        confidence_signals: ConfidenceSignals,
        stress_signals: StressSignals,
        recovery_signals: RecoverySignals,
        evaluation: UnifiedEvaluation
    ) -> AggregatedSignals:
        """Combine all signals into unified update."""
        
    def compute_metric_deltas(
        self,
        signals: AggregatedSignals,
        current_state: CandidateMindState
    ) -> Dict[str, float]:
        """Calculate deltas for each mind state metric."""
```

### 3.5 Confidence Score Engine

**Location:** `/apps/api/app/ai/coaching/confidence_scoring.py`

**CRITICAL:** Confidence must be computed **deterministically**, NOT from a single LLM score.

#### Scoring Components

```python
class ConfidenceScoreEngine:
    def compute_confidence_score(
        self,
        transcript: str,
        pauses: List[Pause],
        structure_score: float,
        filler_density: float,
        ownership_language_ratio: float,
        completion_ratio: float
    ) -> ConfidenceScore:
        """
        Confidence = weighted combination:
        - Filler reduction (20%)
        - Speaking continuity (20%)
        - Structure stability (15%)
        - Ownership language (15%)
        - Answer completion (15%)
        - Recovery speed (10%)
        - Pause control (5%)
        """
        
    def compute_pressure_score(
        self,
        performance_under_interruptions: float,
        recovery_after_challenges: float,
        composure_stability: float
    ) -> PressureScore:
        """
        Pressure handling = weighted combination:
        - Interruption recovery (40%)
        - Challenge handling (30%)
        - Composure stability (30%)
        """
        
    def compute_clarity_score(
        self,
        structure_score: float,
        logical_flow_score: float,
        conciseness_score: float,
        vocabulary_precision: float
    ) -> ClarityScore:
        """Communication clarity composite."""
        
    def compute_resilience_score(
        self,
        recovery_speed: float,
        improvement_after_failure: float,
        emotional_consistency: float
    ) -> ResilienceScore:
        """Resilience composite."""
```

### 3.6 Longitudinal Memory

**Database Model:** `mind_state_history`

Stores snapshots of mind state over time for trend analysis.

```sql
CREATE TABLE mind_state_history (
    id UUID PRIMARY KEY,
    candidate_id UUID REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    snapshot_timestamp TIMESTAMP,
    
    -- Full mind state snapshot (JSONB for flexibility)
    mind_state_snapshot JSONB,
    
    -- Session context
    session_type VARCHAR,  -- practice, mock, real
    interview_domain VARCHAR,
    difficulty_level VARCHAR,
    
    -- Performance summary
    session_confidence_avg FLOAT,
    session_pressure_avg FLOAT,
    session_clarity_avg FLOAT,
    
    created_at TIMESTAMP
);

CREATE INDEX idx_mind_state_history_candidate 
    ON mind_state_history(candidate_id, snapshot_timestamp DESC);
```

#### Growth Tracking

```python
class LongitudinalAnalyzer:
    async def get_candidate_evolution(
        self,
        candidate_id: str,
        metric: str,
        time_range: DateRange
    ) -> Evolution:
        """Get evolution of specific metric over time."""
        
    async def get_confidence_trend(
        self,
        candidate_id: str
    ) -> ConfidenceTrend:
        """Get long-term confidence trajectory."""
        
    async def get_pressure_adaptation_curve(
        self,
        candidate_id: str
    ) -> PressureAdaptationCurve:
        """How candidate adapts to pressure over time."""
        
    async def compare_sessions(
        self,
        candidate_id: str,
        session_ids: List[str]
    ) -> SessionComparison:
        """Compare performance across sessions."""
```

### 3.7 Event Integration

**New Events:**

```python
# Mind state events
MIND_STATE_UPDATED = "mind_state.updated"
CONFIDENCE_SPIKE_DETECTED = "mind_state.confidence_spike"
CONFIDENCE_COLLAPSE_DETECTED = "mind_state.confidence_collapse"
FREEZE_RESPONSE_DETECTED = "mind_state.freeze_response"
RECOVERY_DETECTED = "mind_state.recovery"
GROWTH_MILESTONE_REACHED = "mind_state.growth_milestone"

# Event payloads
@dataclass
class MindStateUpdatedEvent:
    candidate_id: str
    session_id: str
    turn_id: str
    previous_state: CandidateMindState
    new_state: CandidateMindState
    deltas: Dict[str, float]
    timestamp: datetime
```

---

## 4. PILLAR 2: Confidence Engine

### 4.1 Overview

Transforms the interview system from **evaluator** into **adaptive confidence-building coach**.

**Core Principle:** Challenge candidates, but NEVER psychologically crush them.

### 4.2 ConfidenceEngine

**Location:** `/apps/api/app/ai/coaching/confidence_engine.py`

#### Responsibilities

- Maintain psychological safety
- Dynamically adjust interviewer tone
- Trigger recovery loops
- Prevent confidence collapse
- Reinforce progress
- Adapt pressure safely

#### Core Methods

```python
class ConfidenceEngine:
    def __init__(
        self,
        mind_state_engine: MindStateEngine,
        pressure_engine: PressureConditioningEngine
    ):
        self.mind_state_engine = mind_state_engine
        self.pressure_engine = pressure_engine
        self.safety_policy = PressureSafetyPolicy()
        
    async def analyze_candidate_state(
        self,
        candidate_id: str,
        session_id: str,
        recent_turns: List[TurnData]
    ) -> CandidateStateAnalysis:
        """
        Analyze current psychological state.
        Returns: confidence level, stress level, support needs
        """
        
    async def determine_support_level(
        self,
        state_analysis: CandidateStateAnalysis,
        answer_quality: AnswerQuality
    ) -> SupportLevel:
        """
        Determine how much support candidate needs.
        
        Levels:
        - MINIMAL: High confidence, strong performance
        - STANDARD: Normal support
        - ELEVATED: Some struggle, needs encouragement
        - HIGH: Significant struggle, needs active help
        - CRITICAL: Confidence collapse, immediate intervention
        """
        
    async def determine_recovery_mode(
        self,
        support_level: SupportLevel,
        failure_type: FailureType,
        attempt_count: int
    ) -> RecoveryMode:
        """
        Determine recovery strategy.
        
        Modes:
        - HINT: Give directional hint
        - BREAKDOWN: Break question into parts
        - REFRAME: Rephrase question differently
        - STEP_BY_STEP: Guide through reasoning
        - ENCOURAGEMENT: Acknowledge effort, encourage
        - SIMPLIFIED_VERSION: Offer simpler variant
        - PARTIAL_CREDIT_RECOVERY: Build on what's correct
        """
        
    def should_reduce_pressure(
        self,
        state_analysis: CandidateStateAnalysis,
        current_pressure: PressureLevel
    ) -> bool:
        """Check if pressure should be reduced."""
        
    def should_increase_encouragement(
        self,
        state_analysis: CandidateStateAnalysis,
        recent_performance: List[float]
    ) -> bool:
        """Check if encouragement should increase."""
        
    def should_trigger_hint(
        self,
        answer_quality: AnswerQuality,
        struggle_duration: float,
        previous_hints: int
    ) -> bool:
        """Check if hint should be given."""
        
    def should_trigger_retry(
        self,
        answer_quality: AnswerQuality,
        candidate_state: CandidateMindState,
        recovery_potential: float
    ) -> bool:
        """Check if retry opportunity should be offered."""
        
    def should_trigger_reframing(
        self,
        confusion_signals: ConfusionSignals,
        question_clarity: float
    ) -> bool:
        """Check if question should be reframed."""
```

### 4.3 Recovery Loop System

**Location:** `/apps/api/app/ai/coaching/recovery_loops.py`

#### Recovery Modes

```python
class RecoveryMode(str, Enum):
    HINT = "hint"
    BREAKDOWN = "breakdown"
    REFRAME = "reframe"
    STEP_BY_STEP = "step_by_step"
    ENCOURAGEMENT = "encouragement"
    SIMPLIFIED_VERSION = "simplified_version"
    PARTIAL_CREDIT_RECOVERY = "partial_credit_recovery"

class RecoveryLoopOrchestrator:
    async def execute_recovery_loop(
        self,
        mode: RecoveryMode,
        original_question: str,
        candidate_answer: str,
        context: RecoveryContext
    ) -> RecoveryResponse:
        """Execute recovery strategy."""
```

#### Recovery Strategies

**HINT Mode**

```python
async def generate_hint(
    self,
    question: str,
    partial_answer: str,
    missing_concepts: List[str]
) -> Hint:
    """
    Generate directional hint without giving away answer.
    
    Example:
    "Think about how the data structure affects lookup time."
    "Consider what happens when the cache is full."
    """
```

**BREAKDOWN Mode**

```python
async def breakdown_question(
    self,
    complex_question: str
) -> List[SubQuestion]:
    """
    Break complex question into manageable parts.
    
    Example:
    Original: "Design a distributed cache with TTL and LRU eviction"
    
    Breakdown:
    1. "Let's start with basic cache operations. What operations do you need?"
    2. "How would you implement TTL for entries?"
    3. "How would LRU eviction work?"
    """
```

**REFRAME Mode**

```python
async def reframe_question(
    self,
    original_question: str,
    confusion_type: ConfusionType
) -> ReframedQuestion:
    """
    Rephrase question for clarity.
    
    Example:
    Original: "What's your approach to technical debt?"
    Reframe: "Tell me about a time you decided to refactor code 
              vs. shipping a feature quickly."
    """
```

**STEP_BY_STEP Mode**

```python
async def guide_reasoning(
    self,
    question: str,
    current_answer: str
) -> GuidedReasoning:
    """
    Guide through reasoning process.
    
    Example:
    "Let's think through this step by step.
    First, what are the performance requirements?
    ... [candidate responds]
    Good. Now, what data structures give you that performance?"
    """
```

**ENCOURAGEMENT Mode**

```python
async def generate_encouragement(
    self,
    effort_indicators: EffortIndicators,
    partial_correctness: float
) -> Encouragement:
    """
    Genuine encouragement based on actual progress.
    
    Examples:
    - "Good recovery after the hint."
    - "Your structure improved there."
    - "That explanation was much clearer."
    - "You identified the key tradeoff."
    
    Avoid:
    - Generic positivity
    - Fake motivation
    - Cringe coaching language
    """
```

**SIMPLIFIED_VERSION Mode**

```python
async def create_simplified_version(
    self,
    original_question: str,
    complexity_level: float
) -> SimplifiedQuestion:
    """
    Create easier variant of question.
    
    Example:
    Original: "Design a distributed rate limiter with geo-replication"
    Simplified: "Design a rate limiter for a single server"
    """
```

**PARTIAL_CREDIT_RECOVERY Mode**

```python
async def build_on_correct_parts(
    self,
    answer: str,
    correct_parts: List[str],
    missing_parts: List[str]
) -> PartialCreditResponse:
    """
    Acknowledge correct parts, guide toward missing parts.
    
    Example:
    "You correctly identified that we need a hash map.
    Now, what about handling collisions?"
    """
```

### 4.4 Adaptive Interviewer Support

**Location:** `/apps/api/app/ai/coaching/adaptive_support.py`

#### Support Adaptation

```python
class AdaptiveSupportSystem:
    async def adapt_interviewer_behavior(
        self,
        candidate_state: CandidateMindState,
        support_level: SupportLevel,
        current_phase: InterviewPhase
    ) -> InterviewerBehavior:
        """
        Adapt interviewer behavior to candidate state.
        
        Returns: tone, pacing, acknowledgment style, followup depth
        """
        
    def get_tone_for_state(
        self,
        confidence_level: float,
        stress_level: float
    ) -> InterviewerTone:
        """
        Low confidence:
        - Warmer tone
        - More acknowledgments
        - Supportive language
        
        High confidence:
        - Professional tone
        - Direct questions
        - Deeper probing
        """
        
    def get_pacing_for_state(
        self,
        cognitive_load: float,
        pressure_tolerance: float
    ) -> PacingStrategy:
        """
        High cognitive load:
        - Slower pacing
        - Longer pauses
        - Simpler followups
        
        Low cognitive load:
        - Normal pacing
        - Complex followups
        - Multiple threads
        """
        
    def get_acknowledgment_style(
        self,
        support_level: SupportLevel
    ) -> AcknowledgmentStyle:
        """
        High support:
        - More frequent acknowledgments
        - Specific positive feedback
        - Progress reinforcement
        
        Low support:
        - Standard acknowledgments
        - Focus on content
        - Professional feedback
        """
```

### 4.5 Confidence-Aware Turn Routing

**Integration:** Modify existing `TurnOrchestrator`

**Location:** `/apps/api/app/ai/orchestrators/turn_orchestrator.py`

#### Enhanced Routing Logic

```python
# BEFORE: Simple routing
if answer_quality == AnswerQuality.POOR:
    return TurnAction.MOVE_TO_NEXT

# AFTER: Confidence-aware routing
routing_context = ConfidenceRoutingContext(
    answer_quality=answer_quality,
    candidate_state=mind_state,
    support_level=support_level,
    attempt_count=attempt_count,
    recovery_potential=recovery_potential
)

action = await self.confidence_aware_router.route(routing_context)
```

#### Routing Examples

**Example 1: Same Score, Different States**

```python
# Candidate A: Score 55, High confidence, recovering
# Action: Gentle followup, acknowledge improvement

# Candidate B: Score 55, Low confidence, panicking
# Action: Recovery loop, reduce pressure, offer hint
```

**Example 2: Poor Answer, High Recovery Potential**

```python
# Traditional: MOVE_TO_NEXT (give up)
# Confidence-aware: TRIGGER_RECOVERY (help them succeed)
```

**Example 3: Good Answer, Confidence Spike**

```python
# Traditional: FOLLOWUP_DEEPER (standard)
# Confidence-aware: REINFORCE_THEN_CHALLENGE (acknowledge + increase difficulty)
```

### 4.6 Micro-Reinforcement System

**Location:** `/apps/api/app/ai/coaching/micro_reinforcement.py`

#### Reinforcement Triggers

```python
class MicroReinforcementEngine:
    def detect_reinforcement_opportunities(
        self,
        turn_data: TurnData,
        previous_turn: TurnData
    ) -> List[ReinforcementOpportunity]:
        """
        Detect moments worthy of reinforcement.
        
        Triggers:
        - Structure improvement
        - Recovery after hint
        - Tradeoff analysis
        - Clarification attempt
        - Self-correction
        - Calm reasoning under pressure
        - Completing thought despite interruption
        """
        
    def generate_micro_reinforcement(
        self,
        opportunity: ReinforcementOpportunity
    ) -> MicroReinforcement:
        """
        Generate specific, genuine reinforcement.
        
        Good:
        - "Good recovery after the hint."
        - "Your structure improved there."
        - "You corrected the tradeoff analysis well."
        - "That explanation was much clearer."
        - "You identified the key bottleneck."
        
        Bad (avoid):
        - "Great job!"
        - "You're doing amazing!"
        - "That's perfect!"
        - Generic positivity
        """
```

### 4.7 Pressure Safety Boundaries

**Location:** `/apps/api/app/ai/coaching/pressure_safety.py`

#### Safety Policy

```python
class PressureSafetyPolicy:
    def __init__(self):
        self.max_consecutive_failures = 3
        self.max_interruptions_per_minute = 2
        self.min_confidence_threshold = 30  # 0-100 scale
        self.max_pressure_duration_seconds = 300
        
    def check_safety_boundaries(
        self,
        candidate_state: CandidateMindState,
        session_metrics: SessionMetrics,
        pressure_level: PressureLevel
    ) -> SafetyCheck:
        """
        Check if pressure is within safe boundaries.
        
        Violations:
        - Confidence too low
        - Too many consecutive failures
        - Too many interruptions
        - Prolonged high pressure
        - Panic markers detected
        """
        
    def get_safety_intervention(
        self,
        violation: SafetyViolation
    ) -> SafetyIntervention:
        """
        Determine intervention to restore safety.
        
        Interventions:
        - Reduce pressure immediately
        - Inject recovery opportunity
        - Soften tone
        - Simplify questions
        - Reset pacing
        - Offer break (if applicable)
        """
```

### 4.8 Post-Failure Recovery

**Location:** `/apps/api/app/ai/coaching/post_failure_recovery.py`

#### Learning Reconstruction

```python
class PostFailureRecovery:
    async def reconstruct_answer(
        self,
        question: str,
        candidate_answer: str,
        correct_approach: str
    ) -> AnswerReconstruction:
        """
        Show candidate what a strong answer would include.
        
        Structure:
        1. Acknowledge what was correct
        2. Explain missing reasoning
        3. Demonstrate ideal structure
        4. Show improvement path
        """
        
    async def create_retry_opportunity(
        self,
        original_question: str,
        first_attempt: str,
        learning_points: List[str]
    ) -> RetryOpportunity:
        """
        Offer retry with learning context.
        
        Example:
        "Now that we've discussed [key concepts],
        would you like to take another approach to this question?"
        """
        
    async def generate_improvement_guidance(
        self,
        failure_analysis: FailureAnalysis
    ) -> ImprovementGuidance:
        """
        Specific, actionable improvement guidance.
        
        Example:
        "Focus on structuring your answer:
        1. State the approach clearly
        2. Explain the tradeoffs
        3. Justify your choice
        
        This will make your thinking much clearer."
        """
```

#### Emotional Closure

```python
async def create_positive_closure(
    self,
    session_summary: SessionSummary
) -> PositiveClosure:
    """
    End session on constructive note.
    
    Goal: Candidate leaves thinking:
    "I can improve this."
    
    NOT:
    "I am terrible."
    
    Structure:
    1. Acknowledge effort
    2. Highlight specific improvements
    3. Identify growth areas
    4. Provide clear next steps
    """
```

---

## 5. PILLAR 3: Adaptive Pressure Conditioning System

### 5.1 Overview

Gradually build interview resilience using controlled exposure to realistic pressure.

**Training Goals:**
- Composure under stress
- Clarity during interruptions
- Recovery ability
- Executive communication
- Fast thinking
- Emotional stability

### 5.2 PressureConditioningEngine

**Location:** `/apps/api/app/ai/coaching/pressure_conditioning_engine.py`

#### Responsibilities

- Manage pressure progression
- Control interviewer intensity
- Simulate realistic interviewer styles
- Increase resilience gradually
- Monitor adaptation

#### Pressure Levels

```python
class PressureLevel(str, Enum):
    SAFE = "safe"  # Supportive, slow-paced, no interruptions
    CALM = "calm"  # Professional, standard pacing
    STANDARD = "standard"  # Normal interview pressure
    FAST_PACED = "fast_paced"  # Quick followups, tight timing
    HIGH_PRESSURE = "high_pressure"  # Rapid questions, some challenges
    AGGRESSIVE_PANEL = "aggressive_panel"  # Interruptions, challenges
    EXECUTIVE_GRILLING = "executive_grilling"  # Maximum pressure simulation
```

#### Core Methods

```python
class PressureConditioningEngine:
    async def determine_pressure_level(
        self,
        candidate_state: CandidateMindState,
        session_goals: SessionGoals,
        training_phase: TrainingPhase
    ) -> PressureLevel:
        """
        Determine appropriate pressure level.
        
        Factors:
        - Current resilience score
        - Recovery ability
        - Communication stability
        - Training progression
        - Confidence level
        """
        
    async def adapt_pressure_realtime(
        self,
        current_pressure: PressureLevel,
        candidate_performance: PerformanceMetrics,
        safety_check: SafetyCheck
    ) -> PressureAdjustment:
        """
        Adjust pressure during session.
        
        Increase pressure if:
        - Candidate stabilizing
        - High confidence
        - Strong recovery
        
        Decrease pressure if:
        - Safety boundary violated
        - Confidence dropping
        - Panic markers
        """
        
    def should_escalate_pressure(
        self,
        stability_metrics: StabilityMetrics,
        adaptation_rate: float
    ) -> bool:
        """Check if ready for pressure increase."""
        
    def should_reduce_pressure(
        self,
        stress_signals: StressSignals,
        performance_degradation: float
    ) -> bool:
        """Check if pressure should decrease."""
```

### 5.3 Pressure Progression Model

**Location:** `/apps/api/app/ai/coaching/pressure_progression.py`

#### Progression Criteria

```python
class PressureProgressionModel:
    def can_progress_to_level(
        self,
        candidate_state: CandidateMindState,
        current_level: PressureLevel,
        target_level: PressureLevel
    ) -> ProgressionEligibility:
        """
        Check if candidate ready for next pressure level.
        
        Criteria (NOT based purely on technical correctness):
        - Confidence stability at current level
        - Recovery ability demonstrated
        - Communication clarity maintained
        - Resilience score threshold met
        - Emotional stability maintained
        """
        
    def get_progression_path(
        self,
        candidate_state: CandidateMindState,
        training_goal: TrainingGoal
    ) -> ProgressionPath:
        """
        Generate personalized pressure progression path.
        
        Example path:
        Week 1-2: SAFE -> CALM (build baseline)
        Week 3-4: CALM -> STANDARD (standard interview)
        Week 5-6: STANDARD -> FAST_PACED (increase pace)
        Week 7+: HIGH_PRESSURE training (advanced)
        """
```

### 5.4 Interviewer Persona System

**Location:** `/apps/api/app/ai/coaching/interviewer_personas.py`

#### Persona Archetypes

```python
class InterviewerPersona(BaseModel):
    name: str
    description: str
    pressure_level: PressureLevel
    
    # Behavioral traits
    interruption_tendency: float  # 0-1
    pacing_speed: float  # 0-1 (slow to fast)
    followup_depth: int  # 1-5
    acknowledgment_frequency: float  # 0-1
    challenge_intensity: float  # 0-1
    silence_tolerance: float  # seconds
    
    # Communication style
    speaking_style: str
    question_style: str
    feedback_style: str
    
    # Pressure behaviors
    uses_interruptions: bool
    uses_rapid_followups: bool
    uses_ambiguity: bool
    uses_silence_pressure: bool
    uses_challenge_questions: bool
```

#### Predefined Personas

```python
PERSONAS = {
    "supportive_recruiter": InterviewerPersona(
        name="Supportive Recruiter",
        description="Warm, encouraging, focused on candidate comfort",
        pressure_level=PressureLevel.SAFE,
        interruption_tendency=0.0,
        pacing_speed=0.3,
        followup_depth=2,
        acknowledgment_frequency=0.8,
        challenge_intensity=0.1,
        speaking_style="warm, encouraging, clear",
        uses_interruptions=False
    ),
    
    "calm_senior_engineer": InterviewerPersona(
        name="Calm Senior Engineer",
        description="Professional, thoughtful, gives space to think",
        pressure_level=PressureLevel.CALM,
        interruption_tendency=0.1,
        pacing_speed=0.5,
        followup_depth=3,
        acknowledgment_frequency=0.5,
        challenge_intensity=0.3,
        speaking_style="professional, clear, patient",
        uses_interruptions=False
    ),
    
    "analytical_faang_interviewer": InterviewerPersona(
        name="Analytical FAANG Interviewer",
        description="Detail-oriented, probing, expects clarity",
        pressure_level=PressureLevel.STANDARD,
        interruption_tendency=0.3,
        pacing_speed=0.6,
        followup_depth=4,
        acknowledgment_frequency=0.3,
        challenge_intensity=0.5,
        speaking_style="precise, analytical, challenging",
        uses_rapid_followups=True
    ),
    
    "time_constrained_manager": InterviewerPersona(
        name="Time-Constrained Manager",
        description="Fast-paced, expects conciseness",
        pressure_level=PressureLevel.FAST_PACED,
        interruption_tendency=0.5,
        pacing_speed=0.8,
        followup_depth=2,
        acknowledgment_frequency=0.2,
        challenge_intensity=0.4,
        speaking_style="direct, quick, impatient with rambling",
        uses_interruptions=True,
        uses_rapid_followups=True
    ),
    
    "high_pressure_panelist": InterviewerPersona(
        name="High-Pressure Panelist",
        description="Challenging, interrupts, tests composure",
        pressure_level=PressureLevel.HIGH_PRESSURE,
        interruption_tendency=0.7,
        pacing_speed=0.9,
        followup_depth=4,
        acknowledgment_frequency=0.1,
        challenge_intensity=0.8,
        speaking_style="direct, challenging, tests under pressure",
        uses_interruptions=True,
        uses_rapid_followups=True,
        uses_challenge_questions=True
    ),
    
    "executive_griller": InterviewerPersona(
        name="Executive Griller",
        description="Maximum pressure, rapid-fire, tests breaking point",
        pressure_level=PressureLevel.EXECUTIVE_GRILLING,
        interruption_tendency=0.9,
        pacing_speed=1.0,
        followup_depth=5,
        acknowledgment_frequency=0.05,
        challenge_intensity=1.0,
        speaking_style="intense, rapid, confrontational (controlled)",
        uses_interruptions=True,
        uses_rapid_followups=True,
        uses_ambiguity=True,
        uses_silence_pressure=True,
        uses_challenge_questions=True
    ),
    
    "behavioral_specialist": InterviewerPersona(
        name="Behavioral Specialist",
        description="Probes for authenticity, detail, emotions",
        pressure_level=PressureLevel.STANDARD,
        interruption_tendency=0.2,
        pacing_speed=0.4,
        followup_depth=5,
        acknowledgment_frequency=0.4,
        challenge_intensity=0.4,
        speaking_style="empathetic but probing, detail-focused",
        uses_rapid_followups=False
    ),
    
    "silent_observer": InterviewerPersona(
        name="Silent Observer",
        description="Minimal feedback, uses silence pressure",
        pressure_level=PressureLevel.STANDARD,
        interruption_tendency=0.0,
        pacing_speed=0.3,
        followup_depth=3,
        acknowledgment_frequency=0.1,
        challenge_intensity=0.3,
        silence_tolerance=10.0,  # Long silences
        speaking_style="minimal, observant, uses silence",
        uses_silence_pressure=True
    )
}
```

### 5.5 Pressure Events

**Location:** `/apps/api/app/ai/coaching/pressure_events.py`

#### Event Types

```python
class PressureEvent(BaseModel):
    event_type: PressureEventType
    timestamp: datetime
    intensity: float  # 0-1
    candidate_response: Optional[str]
    performance_impact: Optional[float]

class PressureEventType(str, Enum):
    INTERRUPTION = "interruption"
    RAPID_FOLLOWUP = "rapid_followup"
    AMBIGUOUS_QUESTION = "ambiguous_question"
    SILENCE_PRESSURE = "silence_pressure"
    CHALLENGE_ASSUMPTION = "challenge_assumption"
    TRADEOFF_CONFRONTATION = "tradeoff_confrontation"
    CLARIFICATION_DEMAND = "clarification_demand"
    MULTI_PART_QUESTION = "multi_part_question"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
```

#### Event Orchestration

```python
class PressureEventOrchestrator:
    def should_trigger_event(
        self,
        persona: InterviewerPersona,
        candidate_state: CandidateMindState,
        current_turn: TurnData,
        safety_policy: PressureSafetyPolicy
    ) -> Optional[PressureEventType]:
        """
        Determine if pressure event should trigger.
        
        Controlled, not random.
        Based on:
        - Persona configuration
        - Candidate readiness
        - Safety boundaries
        - Training goals
        """
        
    async def execute_pressure_event(
        self,
        event_type: PressureEventType,
        context: InterviewContext
    ) -> PressureEventExecution:
        """Execute pressure event in controlled manner."""
```

#### Example Events

**Interruption**

```python
async def execute_interruption(
    self,
    candidate_speaking: bool,
    interruption_point: float  # 0-1 through answer
) -> Interruption:
    """
    Interrupt candidate mid-answer.
    
    Realistic interruptions:
    - "Wait, before you continue..."
    - "Let me stop you there..."
    - "Hold on, can you clarify..."
    
    Measures:
    - How candidate handles interruption
    - Recovery quality
    - Composure maintenance
    """
```

**Silence Pressure**

```python
async def execute_silence_pressure(
    self,
    candidate_finished_speaking: bool,
    silence_duration: float
) -> SilencePressure:
    """
    Use silence to create pressure.
    
    Candidate finishes answer -> interviewer silent
    
    Measures:
    - Can candidate sit with silence?
    - Do they ramble to fill space?
    - Do they ask for feedback?
    """
```

**Challenge Assumption**

```python
async def execute_challenge(
    self,
    candidate_statement: str,
    challenge_type: ChallengeType
) -> Challenge:
    """
    Challenge candidate's reasoning.
    
    Examples:
    - "Why wouldn't approach X be better?"
    - "That assumption might not hold at scale..."
    - "What if latency isn't the bottleneck?"
    
    Measures:
    - Defense of reasoning
    - Openness to alternatives
    - Composure under challenge
    """
```

### 5.6 Pressure Recovery Detection

**Location:** `/apps/api/app/ai/coaching/pressure_recovery.py`

#### Recovery Tracking

```python
class PressureRecoveryDetector:
    def detect_recovery_after_interruption(
        self,
        before_interruption: TurnData,
        after_interruption: TurnData
    ) -> InterruptionRecovery:
        """
        Measure recovery after interruption.
        
        Metrics:
        - Returned to train of thought
        - Maintained clarity
        - Composure stable
        - Completed answer
        """
        
    def detect_recovery_after_challenge(
        self,
        challenge: Challenge,
        response: ChallengeResponse
    ) -> ChallengeRecovery:
        """
        Measure recovery after challenge.
        
        Metrics:
        - Defended reasoning calmly
        - Acknowledged valid points
        - Adjusted thinking
        - Maintained composure
        """
        
    def detect_recovery_after_confusion(
        self,
        confusion_signals: ConfusionSignals,
        clarification_provided: bool,
        post_clarification_performance: float
    ) -> ConfusionRecovery:
        """
        Measure recovery after confusion.
        
        Metrics:
        - Asked for clarification
        - Improved after clarification
        - Regained clarity
        - Reduced hesitation
        """
```

### 5.7 Resilience Scoring

**Location:** `/apps/api/app/ai/coaching/resilience_scoring.py`

#### Resilience Components

```python
class ResilienceScoreEngine:
    def compute_resilience_score(
        self,
        candidate_state: CandidateMindState,
        pressure_events: List[PressureEvent],
        recovery_records: List[RecoveryRecord]
    ) -> ResilienceScore:
        """
        Composite resilience score.
        
        Components:
        - Composure stability (30%)
        - Recovery speed (25%)
        - Performance under pressure (20%)
        - Emotional consistency (15%)
        - Communication clarity under stress (10%)
        """
        
    def compute_composure_stability(
        self,
        confidence_variance: float,
        stress_tolerance: float,
        pressure_events: List[PressureEvent]
    ) -> float:
        """
        Measure composure stability.
        
        Low variance + high stress tolerance = high stability
        """
        
    def compute_recovery_speed(
        self,
        recovery_records: List[RecoveryRecord]
    ) -> float:
        """
        Measure recovery speed.
        
        Average time to return to baseline performance
        """
        
    def compute_performance_under_pressure(
        self,
        baseline_performance: float,
        pressure_performance: float
    ) -> float:
        """
        Measure performance degradation under pressure.
        
        Small degradation = high resilience
        """
```

### 5.8 Pressure Training Journeys

**Location:** `/apps/api/app/ai/coaching/training_journeys.py`

#### Journey Definitions

```python
class TrainingJourney(BaseModel):
    journey_id: str
    name: str
    description: str
    target_audience: str
    duration_weeks: int
    
    # Progression
    phases: List[TrainingPhase]
    pressure_progression: List[PressureLevel]
    persona_progression: List[str]
    
    # Goals
    confidence_goal: float
    resilience_goal: float
    communication_goal: float

class TrainingPhase(BaseModel):
    phase_number: int
    name: str
    duration_sessions: int
    pressure_level: PressureLevel
    persona: str
    focus_areas: List[str]
    success_criteria: Dict[str, float]
```

#### Predefined Journeys

```python
JOURNEYS = {
    "first_interview_anxiety": TrainingJourney(
        journey_id="first_interview_anxiety",
        name="First Interview Confidence Builder",
        description="Build confidence for your first technical interview",
        target_audience="Students, career changers, first-time interviewees",
        duration_weeks=4,
        phases=[
            TrainingPhase(
                phase_number=1,
                name="Build Foundation",
                duration_sessions=3,
                pressure_level=PressureLevel.SAFE,
                persona="supportive_recruiter",
                focus_areas=["basic_communication", "answer_structure"],
                success_criteria={"confidence": 60, "clarity": 65}
            ),
            TrainingPhase(
                phase_number=2,
                name="Standard Interview",
                duration_sessions=4,
                pressure_level=PressureLevel.CALM,
                persona="calm_senior_engineer",
                focus_areas=["technical_clarity", "followup_handling"],
                success_criteria={"confidence": 70, "resilience": 60}
            ),
            TrainingPhase(
                phase_number=3,
                name="Real Conditions",
                duration_sessions=4,
                pressure_level=PressureLevel.STANDARD,
                persona="analytical_faang_interviewer",
                focus_areas=["pressure_handling", "recovery"],
                success_criteria={"confidence": 75, "resilience": 70}
            )
        ]
    ),
    
    "faang_pressure_simulation": TrainingJourney(
        journey_id="faang_pressure_simulation",
        name="FAANG Interview Pressure Training",
        description="Prepare for high-pressure FAANG interviews",
        target_audience="Experienced engineers targeting FAANG",
        duration_weeks=6,
        phases=[
            TrainingPhase(
                phase_number=1,
                name="Baseline Assessment",
                duration_sessions=2,
                pressure_level=PressureLevel.STANDARD,
                persona="analytical_faang_interviewer",
                focus_areas=["baseline_measurement"],
                success_criteria={"confidence": 75, "technical_depth": 80}
            ),
            TrainingPhase(
                phase_number=2,
                name="Fast-Paced Conditioning",
                duration_sessions=4,
                pressure_level=PressureLevel.FAST_PACED,
                persona="time_constrained_manager",
                focus_areas=["concise_communication", "rapid_thinking"],
                success_criteria={"clarity": 80, "resilience": 75}
            ),
            TrainingPhase(
                phase_number=3,
                name="High Pressure Simulation",
                duration_sessions=4,
                pressure_level=PressureLevel.HIGH_PRESSURE,
                persona="high_pressure_panelist",
                focus_areas=["interruption_recovery", "challenge_handling"],
                success_criteria={"resilience": 80, "composure": 85}
            ),
            TrainingPhase(
                phase_number=4,
                name="Executive Round",
                duration_sessions=2,
                pressure_level=PressureLevel.EXECUTIVE_GRILLING,
                persona="executive_griller",
                focus_areas=["maximum_pressure_resilience"],
                success_criteria={"resilience": 85, "confidence_under_pressure": 80}
            )
        ]
    ),
    
    "executive_communication": TrainingJourney(
        journey_id="executive_communication",
        name="Executive Communication Mastery",
        description="Develop executive presence and communication",
        target_audience="Senior engineers, engineering managers",
        duration_weeks=4,
        phases=[
            TrainingPhase(
                phase_number=1,
                name="Clarity & Conciseness",
                duration_sessions=3,
                pressure_level=PressureLevel.STANDARD,
                persona="calm_senior_engineer",
                focus_areas=["executive_presence", "concise_communication"],
                success_criteria={"clarity": 85, "conciseness": 80}
            ),
            TrainingPhase(
                phase_number=2,
                name="High-Stakes Communication",
                duration_sessions=4,
                pressure_level=PressureLevel.HIGH_PRESSURE,
                persona="executive_griller",
                focus_areas=["composure", "strategic_thinking"],
                success_criteria={"executive_presence": 85, "strategic_thinking": 80}
            )
        ]
    )
}
```

### 5.9 Session Adaptation

**Location:** `/apps/api/app/ai/coaching/session_adaptation.py`

#### Realtime Pressure Adjustment

```python
class SessionAdaptationEngine:
    async def adapt_session_realtime(
        self,
        session_id: str,
        candidate_state: CandidateMindState,
        current_pressure: PressureLevel,
        recent_turns: List[TurnData]
    ) -> SessionAdaptation:
        """
        Adapt session pressure in realtime.
        
        Increase pressure if:
        - Candidate stabilizing
        - High confidence maintained
        - Strong recovery demonstrated
        - Goals suggest challenge
        
        Decrease pressure if:
        - Safety boundary violated
        - Confidence dropping rapidly
        - Panic markers detected
        - Performance severely degraded
        - Recovery failing
        
        Inject recovery if:
        - Struggling but salvageable
        - High recovery potential
        - Learning opportunity
        """
        
    async def determine_pressure_adjustment(
        self,
        stability_trend: Trend,
        safety_status: SafetyStatus,
        training_goals: TrainingGoals
    ) -> PressureAdjustment:
        """Calculate pressure adjustment."""
        
    async def inject_recovery_opportunity(
        self,
        candidate_state: CandidateMindState,
        failure_context: FailureContext
    ) -> RecoveryOpportunityInjection:
        """Dynamically inject recovery opportunity."""
```

---

## 6. Database Schema

### 6.1 New Tables

```sql
-- ============================================
-- Candidate Mind State
-- ============================================

CREATE TABLE candidate_mind_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES users(id),
    
    -- Core Psychological Metrics (0-100 normalized)
    confidence_level FLOAT DEFAULT 50.0,
    stress_tolerance FLOAT DEFAULT 50.0,
    communication_clarity FLOAT DEFAULT 50.0,
    memory_recall_strength FLOAT DEFAULT 50.0,
    strategic_thinking FLOAT DEFAULT 50.0,
    emotional_stability FLOAT DEFAULT 50.0,
    hesitation_recovery FLOAT DEFAULT 50.0,
    storytelling_ability FLOAT DEFAULT 50.0,
    technical_depth_confidence FLOAT DEFAULT 50.0,
    pressure_handling FLOAT DEFAULT 50.0,
    behavioral_authenticity FLOAT DEFAULT 50.0,
    response_structure FLOAT DEFAULT 50.0,
    filler_word_control FLOAT DEFAULT 50.0,
    confidence_under_pressure FLOAT DEFAULT 50.0,
    executive_presence FLOAT DEFAULT 50.0,
    recovery_speed FLOAT DEFAULT 50.0,
    freeze_response_risk FLOAT DEFAULT 50.0,
    cognitive_load_tolerance FLOAT DEFAULT 50.0,
    speaking_consistency FLOAT DEFAULT 50.0,
    
    -- Trend Tracking
    rolling_average_scores JSONB DEFAULT '{}',
    improvement_velocity JSONB DEFAULT '{}',
    confidence_trend VARCHAR DEFAULT 'stable',  -- improving, stable, declining
    pressure_trend VARCHAR DEFAULT 'stable',
    communication_trend VARCHAR DEFAULT 'stable',
    
    -- Topic Performance
    weak_topics JSONB DEFAULT '[]',
    strong_topics JSONB DEFAULT '[]',
    recurring_failures JSONB DEFAULT '[]',
    recurring_strengths JSONB DEFAULT '[]',
    
    -- Metadata
    last_updated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    session_count INTEGER DEFAULT 0,
    total_turns_analyzed INTEGER DEFAULT 0,
    
    CONSTRAINT candidate_mind_states_candidate_unique UNIQUE(candidate_id)
);

CREATE INDEX idx_mind_states_candidate ON candidate_mind_states(candidate_id);
CREATE INDEX idx_mind_states_updated ON candidate_mind_states(last_updated_at DESC);


-- ============================================
-- Mind State History (Longitudinal Tracking)
-- ============================================

CREATE TABLE mind_state_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    snapshot_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Full snapshot
    mind_state_snapshot JSONB NOT NULL,
    
    -- Session context
    session_type VARCHAR,  -- practice, mock, real
    interview_domain VARCHAR,
    difficulty_level VARCHAR,
    pressure_level VARCHAR,
    
    -- Performance summary
    session_confidence_avg FLOAT,
    session_pressure_avg FLOAT,
    session_clarity_avg FLOAT,
    session_resilience_avg FLOAT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mind_state_history_candidate ON mind_state_history(candidate_id, snapshot_timestamp DESC);
CREATE INDEX idx_mind_state_history_session ON mind_state_history(session_id);


-- ============================================
-- Pressure Events
-- ============================================

CREATE TABLE pressure_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id),
    turn_id UUID REFERENCES turns(id),
    candidate_id UUID NOT NULL REFERENCES users(id),
    
    -- Event details
    event_type VARCHAR NOT NULL,  -- interruption, challenge, silence, etc.
    intensity FLOAT,  -- 0-1
    timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Context
    interviewer_persona VARCHAR,
    pressure_level VARCHAR,
    
    -- Candidate response
    candidate_response TEXT,
    response_quality FLOAT,
    recovery_time_seconds FLOAT,
    composure_maintained BOOLEAN,
    
    -- Performance impact
    performance_before FLOAT,
    performance_after FLOAT,
    performance_delta FLOAT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pressure_events_session ON pressure_events(session_id);
CREATE INDEX idx_pressure_events_candidate ON pressure_events(candidate_id, timestamp DESC);


-- ============================================
-- Recovery Records
-- ============================================

CREATE TABLE recovery_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id),
    turn_id UUID REFERENCES turns(id),
    candidate_id UUID NOT NULL REFERENCES users(id),
    
    -- Recovery context
    recovery_mode VARCHAR NOT NULL,  -- hint, breakdown, reframe, etc.
    trigger_reason VARCHAR,  -- poor_answer, confusion, panic, etc.
    
    -- Before recovery
    initial_answer TEXT,
    initial_quality FLOAT,
    struggle_indicators JSONB,
    
    -- Recovery intervention
    intervention_provided TEXT,
    intervention_type VARCHAR,
    
    -- After recovery
    post_recovery_answer TEXT,
    post_recovery_quality FLOAT,
    improvement_delta FLOAT,
    
    -- Success metrics
    recovery_successful BOOLEAN,
    recovery_time_seconds FLOAT,
    confidence_restored BOOLEAN,
    
    timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_recovery_records_session ON recovery_records(session_id);
CREATE INDEX idx_recovery_records_candidate ON recovery_records(candidate_id, timestamp DESC);


-- ============================================
-- Confidence Events
-- ============================================

CREATE TABLE confidence_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    turn_id UUID REFERENCES turns(id),
    
    -- Event type
    event_type VARCHAR NOT NULL,  -- spike, collapse, recovery, milestone
    
    -- Confidence metrics
    confidence_before FLOAT,
    confidence_after FLOAT,
    confidence_delta FLOAT,
    
    -- Context
    trigger_context JSONB,
    contributing_factors JSONB,
    
    timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_confidence_events_candidate ON confidence_events(candidate_id, timestamp DESC);


-- ============================================
-- Training Journeys
-- ============================================

CREATE TABLE training_journeys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES users(id),
    journey_id VARCHAR NOT NULL,  -- first_interview_anxiety, faang_pressure, etc.
    
    -- Progress
    current_phase INTEGER DEFAULT 1,
    total_phases INTEGER,
    sessions_completed INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR DEFAULT 'in_progress',  -- in_progress, completed, abandoned
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    -- Performance tracking
    baseline_metrics JSONB,
    current_metrics JSONB,
    improvement_metrics JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_training_journeys_candidate ON training_journeys(candidate_id);


-- ============================================
-- Interviewer Persona Sessions
-- ============================================

CREATE TABLE interviewer_persona_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id),
    candidate_id UUID NOT NULL REFERENCES users(id),
    
    -- Persona details
    persona_id VARCHAR NOT NULL,
    persona_name VARCHAR,
    pressure_level VARCHAR,
    
    -- Performance under this persona
    avg_confidence FLOAT,
    avg_clarity FLOAT,
    avg_resilience FLOAT,
    
    -- Pressure events
    interruptions_count INTEGER DEFAULT 0,
    challenges_count INTEGER DEFAULT 0,
    silence_pressure_count INTEGER DEFAULT 0,
    
    -- Recovery stats
    successful_recoveries INTEGER DEFAULT 0,
    failed_recoveries INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_persona_sessions_candidate ON interviewer_persona_sessions(candidate_id);


-- ============================================
-- Micro Reinforcements
-- ============================================

CREATE TABLE micro_reinforcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id),
    turn_id UUID REFERENCES turns(id),
    candidate_id UUID NOT NULL REFERENCES users(id),
    
    -- Reinforcement details
    reinforcement_type VARCHAR NOT NULL,  -- improvement, recovery, structure, clarity
    reinforcement_text TEXT NOT NULL,
    
    -- Context
    trigger_behavior VARCHAR,
    improvement_demonstrated TEXT,
    
    timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_micro_reinforcements_candidate ON micro_reinforcements(candidate_id);
```

---

## 7. Service Layer Architecture

### 7.1 Service Hierarchy

```
┌─────────────────────────────────────────┐
│      CoachingOrchestrator               │
│  (Top-level coordinator)                │
└─────────────────────────────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
      ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Mind     │ │Confidence│ │ Pressure │
│ State    │ │ Engine   │ │Conditioning│
│ Engine   │ │          │ │ Engine   │
└──────────┘ └──────────┘ └──────────┘
      │           │           │
      └───────────┼───────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
      ▼                       ▼
┌─────────────────┐   ┌─────────────────┐
│ Signal          │   │ Scoring         │
│ Extraction      │   │ Engines         │
└─────────────────┘   └─────────────────┘
```

### 7.2 CoachingOrchestrator

**Location:** `/apps/api/app/ai/coaching/coaching_orchestrator.py`

```python
class CoachingOrchestrator:
    """
    Top-level orchestrator for confidence coaching system.
    
    Coordinates:
    - MindStateEngine
    - ConfidenceEngine
    - PressureConditioningEngine
    
    Integrates with:
    - TurnOrchestrator (for turn routing)
    - InterviewOrchestrator (for session management)
    - EventBus (for psychological events)
    """
    
    def __init__(
        self,
        mind_state_engine: MindStateEngine,
        confidence_engine: ConfidenceEngine,
        pressure_engine: PressureConditioningEngine,
        db_session_factory: Callable
    ):
        self.mind_state_engine = mind_state_engine
        self.confidence_engine = confidence_engine
        self.pressure_engine = pressure_engine
        self.db_session_factory = db_session_factory
        
    async def process_turn(
        self,
        turn_data: TurnData,
        evaluation: UnifiedEvaluation,
        session_context: SessionContext
    ) -> CoachingDecision:
        """
        Process turn through coaching system.
        
        Flow:
        1. Update mind state from turn
        2. Analyze confidence state
        3. Determine support needs
        4. Check pressure boundaries
        5. Generate coaching decision
        6. Emit psychological events
        """
        
    async def determine_turn_action(
        self,
        answer_quality: AnswerQuality,
        candidate_state: CandidateMindState,
        confidence_analysis: ConfidenceAnalysis,
        pressure_analysis: PressureAnalysis
    ) -> EnhancedTurnAction:
        """
        Confidence-aware turn routing.
        
        Returns: TurnAction + support strategy + tone adjustments
        """
        
    async def handle_confidence_collapse(
        self,
        candidate_id: str,
        session_id: str,
        collapse_context: CollapseContext
    ) -> RecoveryPlan:
        """Handle confidence collapse emergency."""
        
    async def adapt_session_difficulty(
        self,
        session_id: str,
        performance_trend: PerformanceTrend,
        candidate_state: CandidateMindState
    ) -> DifficultyAdjustment:
        """Dynamically adjust session difficulty."""
```

---

## 8. API Contracts

### 8.1 Mind State Endpoints

```python
# GET /api/candidates/{candidate_id}/mind-state
# Get current mind state
{
    "candidate_id": "uuid",
    "confidence_level": 72.5,
    "stress_tolerance": 68.0,
    "communication_clarity": 75.0,
    "pressure_handling": 65.0,
    "confidence_trend": "improving",
    "pressure_trend": "stable",
    "weak_topics": ["system_design", "algorithms"],
    "strong_topics": ["behavioral", "frontend"],
    "last_updated_at": "2026-05-25T10:30:00Z"
}

# GET /api/candidates/{candidate_id}/mind-state/evolution
# Get evolution over time
{
    "candidate_id": "uuid",
    "time_range": "30_days",
    "metrics": [
        {
            "date": "2026-05-01",
            "confidence": 60.0,
            "clarity": 65.0,
            "resilience": 55.0
        },
        {
            "date": "2026-05-25",
            "confidence": 72.5,
            "clarity": 75.0,
            "resilience": 68.0
        }
    ],
    "improvement_velocity": {
        "confidence": 0.5,  # points per day
        "clarity": 0.4,
        "resilience": 0.52
    }
}

# GET /api/sessions/{session_id}/confidence-analysis
# Get session confidence analysis
{
    "session_id": "uuid",
    "avg_confidence": 70.0,
    "confidence_trajectory": [65, 68, 72, 75],  # per turn
    "confidence_events": [
        {
            "turn": 3,
            "event": "confidence_spike",
            "trigger": "successful_recovery_after_hint"
        }
    ],
    "support_level": "standard",
    "pressure_level": "standard",
    "recovery_loops_triggered": 2
}
```

### 8.2 Confidence Engine Endpoints

```python
# GET /api/sessions/{session_id}/coaching-decisions
# Get coaching decisions made during session
{
    "session_id": "uuid",
    "decisions": [
        {
            "turn_id": "uuid",
            "timestamp": "2026-05-25T10:30:00Z",
            "decision_type": "recovery_loop_triggered",
            "recovery_mode": "hint",
            "reason": "poor_answer_but_high_recovery_potential",
            "outcome": "successful_recovery"
        },
        {
            "turn_id": "uuid",
            "timestamp": "2026-05-25T10:35:00Z",
            "decision_type": "pressure_reduced",
            "reason": "confidence_dropping",
            "adjustment": "slower_pacing"
        }
    ]
}

# POST /api/sessions/{session_id}/trigger-recovery
# Manually trigger recovery loop (for testing)
{
    "mode": "hint",
    "context": {...}
}
```

### 8.3 Pressure Conditioning Endpoints

```python
# GET /api/candidates/{candidate_id}/pressure-profile
# Get pressure conditioning profile
{
    "candidate_id": "uuid",
    "current_pressure_level": "standard",
    "resilience_score": 68.0,
    "pressure_events_experienced": 45,
    "successful_recoveries": 38,
    "recovery_rate": 0.84,
    "ready_for_next_level": true,
    "recommended_next_level": "fast_paced",
    "personas_experienced": [
        "supportive_recruiter",
        "calm_senior_engineer",
        "analytical_faang_interviewer"
    ]
}

# GET /api/training-journeys
# Get available training journeys
{
    "journeys": [
        {
            "journey_id": "first_interview_anxiety",
            "name": "First Interview Confidence Builder",
            "description": "...",
            "duration_weeks": 4,
            "suitable_for": ["beginners", "career_changers"]
        }
    ]
}

# POST /api/candidates/{candidate_id}/training-journeys
# Enroll in training journey
{
    "journey_id": "faang_pressure_simulation"
}

# GET /api/candidates/{candidate_id}/training-journeys/current
# Get current journey progress
{
    "journey_id": "faang_pressure_simulation",
    "current_phase": 2,
    "total_phases": 4,
    "sessions_completed": 6,
    "phase_name": "Fast-Paced Conditioning",
    "progress_percentage": 50,
    "metrics_improvement": {
        "confidence": +12.5,
        "resilience": +15.0,
        "clarity": +8.0
    }
}
```

---

## 9. UI Architecture

### 9.1 Design Principles

**Aesthetic:**
- Calm, minimal, executive
- Psychologically safe
- Professional, not gamified
- NO neon, NO dopamine-trash, NO red warnings

**Inspiration:**
- Linear (clean, functional)
- Notion (organized, calm)
- Apple Health (data-focused, calm)
- Headspace analytics (mindful, supportive)

### 9.2 Confidence Intelligence Dashboard

**Location:** `/apps/web/components/coaching/ConfidenceIntelligenceDashboard.tsx`

#### Component Hierarchy

```
ConfidenceIntelligenceDashboard
├── OverviewSection
│   ├── ConfidenceScoreCard
│   ├── ResilienceScoreCard
│   ├── ClarityScoreCard
│   └── PressureHandlingCard
├── EvolutionCharts
│   ├── ConfidenceTrendChart (line chart)
│   ├── PressureAdaptationCurve (line chart)
│   └── CommunicationGrowthChart (line chart)
├── StrengthsWeaknessesSection
│   ├── StrongTopicsList
│   ├── WeakTopicsList
│   └── RecurringPatterns
├── RecentSessionsTimeline
│   └── SessionPerformanceCard[]
└── TrainingJourneyProgress
    ├── CurrentPhaseCard
    ├── ProgressBar
    └── NextMilestoneCard
```

#### Visual Design

**Color Palette (Calm, Professional)**

```css
/* Primary (confidence) */
--confidence-color: #3b82f6;  /* Calm blue */

/* Success (growth) */
--growth-color: #10b981;  /* Calm green */

/* Warning (needs attention) */
--attention-color: #f59e0b;  /* Calm amber */

/* Neutral */
--neutral-bg: #f9fafb;
--neutral-border: #e5e7eb;
--neutral-text: #6b7280;

/* Dark mode */
--dark-bg: #1f2937;
--dark-surface: #374151;
--dark-text: #f3f4f6;
```

**Typography**

```css
/* Clean, professional fonts */
font-family: 
  'Inter', 
  -apple-system, 
  BlinkMacSystemFont, 
  'Segoe UI', 
  sans-serif;
```

#### Example Components

**ConfidenceScoreCard**

```tsx
interface ConfidenceScoreCardProps {
  score: number;  // 0-100
  trend: 'improving' | 'stable' | 'declining';
  deltaFromLastWeek: number;
}

// Visual:
// ┌─────────────────────────────┐
// │ Confidence                  │
// │                             │
// │        72.5                 │  <- Large, calm number
// │     ↗ +5.2 this week       │  <- Small trend indicator
// │                             │
// │ [Calm line chart]           │  <- 7-day sparkline
// └─────────────────────────────┘
```

**EvolutionChart**

```tsx
interface EvolutionChartProps {
  metric: 'confidence' | 'resilience' | 'clarity';
  data: TimeSeriesData[];
  timeRange: '7d' | '30d' | '90d';
}

// Visual: Smooth line chart with:
// - Calm colors
// - Subtle grid
// - No aggressive indicators
// - Annotations for key events (e.g., "Started FAANG training")
```

**RecoveryEventTimeline**

```tsx
// Shows recovery events in chronological order
// Each event shows:
// - What happened (e.g., "Struggled with system design")
// - Recovery strategy (e.g., "Breakdown mode")
// - Outcome (e.g., "Successful recovery, +8 confidence")
//
// Visual: Clean timeline with calm icons
```

### 9.3 In-Session UI Enhancements

**Confidence Indicator (Subtle)**

```tsx
// During interview session, show subtle confidence indicator
// NOT: Red flashing "YOU'RE PANICKING"
// YES: Calm indicator showing current state

interface ConfidenceIndicatorProps {
  confidenceLevel: number;
  supportLevel: SupportLevel;
}

// Visual: Small, unobtrusive indicator
// ┌────────────────┐
// │ ● 72  Standard │  <- Calm dot + number + level
// └────────────────┘
```

**Recovery Loop Notification (Supportive)**

```tsx
// When recovery loop triggers
// NOT: "YOU FAILED, TRY AGAIN"
// YES: "Let me help you think through this"

interface RecoveryNotificationProps {
  mode: RecoveryMode;
  message: string;
}

// Visual: Calm, supportive notification
// No red, no panic-inducing colors
```

### 9.4 State Management

```typescript
// Zustand store for coaching state
interface CoachingStore {
  // Mind state
  candidateMindState: CandidateMindState | null;
  mindStateLoading: boolean;
  
  // Confidence analysis
  sessionConfidenceAnalysis: ConfidenceAnalysis | null;
  
  // Pressure conditioning
  pressureProfile: PressureProfile | null;
  
  // Training journey
  currentJourney: TrainingJourney | null;
  journeyProgress: JourneyProgress | null;
  
  // Actions
  fetchMindState: (candidateId: string) => Promise<void>;
  updateMindState: (updates: Partial<CandidateMindState>) => void;
  fetchConfidenceAnalysis: (sessionId: string) => Promise<void>;
  fetchPressureProfile: (candidateId: string) => Promise<void>;
  enrollInJourney: (journeyId: string) => Promise<void>;
}
```

---

## 10. Integration with Existing Systems

### 10.1 OrchestratorHub Integration

**Update:** `/apps/api/app/ai/orchestrators/integration.py`

```python
class OrchestratorHub:
    def __init__(
        self,
        # ... existing orchestrators
        coaching_orchestrator: CoachingOrchestrator,  # NEW
        db_session_factory: Callable
    ):
        # ... existing init
        self.coaching_orchestrator = coaching_orchestrator
        
    async def process_turn(
        self,
        session_id: str,
        transcript: str,
        turn_context: TurnContext
    ) -> TurnResult:
        """
        Enhanced turn processing with coaching.
        
        Flow:
        1. Existing evaluation pipeline
        2. Coaching system analysis (NEW)
        3. Confidence-aware routing (NEW)
        4. Recovery loop check (NEW)
        5. Mind state update (NEW)
        6. Execute action
        """
        
        # Existing evaluation
        evaluation = await self.evaluation_orchestrator.evaluate(...)
        
        # NEW: Coaching analysis
        coaching_decision = await self.coaching_orchestrator.process_turn(
            turn_data=turn_data,
            evaluation=evaluation,
            session_context=session_context
        )
        
        # NEW: Confidence-aware routing
        enhanced_action = await self.coaching_orchestrator.determine_turn_action(
            answer_quality=evaluation.answer_quality,
            candidate_state=coaching_decision.candidate_state,
            confidence_analysis=coaching_decision.confidence_analysis,
            pressure_analysis=coaching_decision.pressure_analysis
        )
        
        # Execute action (with coaching modifications)
        return await self._execute_enhanced_action(enhanced_action)
```

### 10.2 EventBus Integration

**New Event Handlers:**

```python
# Register coaching event handlers
event_bus.on(Events.MIND_STATE_UPDATED, handle_mind_state_updated)
event_bus.on(Events.CONFIDENCE_COLLAPSE, handle_confidence_collapse)
event_bus.on(Events.RECOVERY_TRIGGERED, handle_recovery_triggered)
event_bus.on(Events.PRESSURE_ADJUSTED, handle_pressure_adjusted)

async def handle_confidence_collapse(event: ConfidenceCollapseEvent):
    """
    Emergency handler for confidence collapse.
    
    Actions:
    - Reduce pressure immediately
    - Trigger recovery loop
    - Notify coaching system
    - Log event for analysis
    """
```

### 10.3 TurnOrchestrator Enhancement

**Update:** `/apps/api/app/ai/orchestrators/turn_orchestrator.py`

```python
class TurnOrchestrator:
    def __init__(
        self,
        # ... existing dependencies
        coaching_orchestrator: CoachingOrchestrator  # NEW
    ):
        self.coaching_orchestrator = coaching_orchestrator
        
    async def decide_next_action(
        self,
        evaluation: UnifiedEvaluation,
        session_state: InterviewRuntimeState,
        turn_history: List[TurnData]
    ) -> TurnDecision:
        """
        Enhanced with confidence-aware routing.
        """
        
        # Get candidate mind state
        mind_state = await self.coaching_orchestrator.mind_state_engine.get_state(
            session_state.candidate_id
        )
        
        # Analyze confidence
        confidence_analysis = await self.coaching_orchestrator.confidence_engine.analyze_candidate_state(
            candidate_id=session_state.candidate_id,
            session_id=session_state.session_id,
            recent_turns=turn_history
        )
        
        # Confidence-aware routing
        if self._should_use_coaching_routing(mind_state, evaluation):
            return await self._confidence_aware_routing(
                evaluation=evaluation,
                mind_state=mind_state,
                confidence_analysis=confidence_analysis
            )
        
        # Fallback to traditional routing
        return await self._traditional_routing(evaluation, session_state)
```

---

## 11. Testing Strategy

### 11.1 Unit Tests

```python
# tests/coaching/test_mind_state_engine.py
class TestMindStateEngine:
    def test_confidence_calculation_from_signals(self):
        """Test confidence score calculation."""
        
    def test_freeze_detection(self):
        """Test cognitive freeze detection."""
        
    def test_recovery_pattern_detection(self):
        """Test recovery pattern recognition."""

# tests/coaching/test_confidence_engine.py
class TestConfidenceEngine:
    def test_support_level_determination(self):
        """Test support level logic."""
        
    def test_recovery_mode_selection(self):
        """Test recovery mode selection."""
        
    def test_pressure_boundary_enforcement(self):
        """Test safety boundaries."""

# tests/coaching/test_pressure_conditioning.py
class TestPressureConditioning:
    def test_pressure_progression_eligibility(self):
        """Test progression criteria."""
        
    def test_persona_behavior_simulation(self):
        """Test persona characteristics."""
        
    def test_pressure_event_triggering(self):
        """Test event triggering logic."""
```

### 11.2 Integration Tests

```python
# tests/coaching/test_coaching_integration.py
class TestCoachingIntegration:
    async def test_end_to_end_confidence_recovery(self):
        """
        Test full recovery loop:
        1. Candidate struggles
        2. System detects
        3. Recovery triggered
        4. Success measured
        """
        
    async def test_pressure_adaptation_flow(self):
        """
        Test pressure adaptation:
        1. Start at standard pressure
        2. Candidate performs well
        3. Pressure increases
        4. Performance maintained
        5. Resilience tracked
        """
        
    async def test_confidence_collapse_handling(self):
        """
        Test emergency handling:
        1. Confidence drops rapidly
        2. Safety triggered
        3. Pressure reduced
        4. Recovery injected
        5. State stabilized
        """
```

### 11.3 Psychological Adaptation Tests

```python
class TestPsychologicalAdaptation:
    async def test_support_increases_with_struggle(self):
        """Verify support increases when candidate struggles."""
        
    async def test_pressure_decreases_at_boundaries(self):
        """Verify safety boundaries enforced."""
        
    async def test_reinforcement_triggers_on_improvement(self):
        """Verify micro-reinforcement triggers."""
        
    async def test_recovery_potential_assessment(self):
        """Verify recovery potential calculation."""
```

---

## 12. Performance Considerations

### 12.1 Latency Requirements

All coaching systems must maintain realtime constraints:

- **Mind state update**: <50ms
- **Confidence analysis**: <100ms
- **Recovery decision**: <150ms
- **Total coaching overhead**: <300ms

### 12.2 Optimization Strategies

```python
# Cache candidate mind state in-memory during session
mind_state_cache: Dict[str, CandidateMindState] = {}

# Batch signal extraction
signals = await asyncio.gather(
    extract_confidence_signals(transcript),
    extract_stress_signals(pauses),
    extract_recovery_signals(turn_history)
)

# Lazy load historical data
# Only fetch evolution data when needed for dashboard
```

---

## 13. Observability

### 13.1 Coaching Metrics

```python
# OpenTelemetry metrics
metrics = [
    "coaching.mind_state_updates",
    "coaching.confidence_analyses",
    "coaching.recovery_loops_triggered",
    "coaching.pressure_adjustments",
    "coaching.confidence_collapses_detected",
    "coaching.reinforcements_delivered",
    "coaching.safety_boundaries_enforced"
]

# Histograms
histograms = [
    "coaching.mind_state_update_latency",
    "coaching.confidence_analysis_latency",
    "coaching.recovery_decision_latency"
]
```

### 13.2 Coaching Events

```python
# Span attributes for tracing
span_attributes = {
    "candidate_id": candidate_id,
    "confidence_level": mind_state.confidence_level,
    "support_level": support_level.value,
    "recovery_mode": recovery_mode.value if recovery_mode else None,
    "pressure_level": pressure_level.value,
    "safety_boundary_violated": bool
}
```

---

## 14. Migration Strategy

### 14.1 Rollout Phases

**Phase 1: Foundation (Week 1-2)**
- Deploy database schema
- Implement core engines
- Basic signal extraction
- No user-facing changes

**Phase 2: Backend Integration (Week 3-4)**
- Integrate CoachingOrchestrator
- Confidence-aware routing
- Recovery loops (server-side)
- Testing with synthetic data

**Phase 3: Soft Launch (Week 5-6)**
- Enable for beta users
- Dashboard UI rollout
- Monitor metrics
- Gather feedback

**Phase 4: Full Launch (Week 7+)**
- Enable for all users
- Training journeys available
- Pressure conditioning active
- Full observability

---

## 15. Success Metrics

### 15.1 System Metrics

- **Mind State Update Success Rate**: >99%
- **Confidence Analysis Latency**: <100ms p95
- **Recovery Loop Success Rate**: >70%
- **Safety Boundary Enforcement**: 100%
- **Pressure Adaptation Accuracy**: >80%

### 15.2 User Outcomes

- **Confidence Improvement**: +15% over 4 weeks
- **Interview Completion Rate**: +20%
- **User Satisfaction**: >4.5/5
- **Recovery After Struggle**: +25%
- **Pressure Resilience**: +20% over 8 weeks

---

## 16. Future Enhancements

### 16.1 Advanced Features

- **Multimodal Analysis**: Facial expressions, vocal tone
- **Peer Comparison**: Anonymous benchmarking
- **AI Coach Conversations**: Post-session analysis chat
- **Group Conditioning**: Cohort-based training
- **Custom Journeys**: Personalized progression paths

### 16.2 Research Opportunities

- **Psychological Research**: Partner with psych researchers
- **Bias Detection**: Identify and correct systemic biases
- **Longitudinal Studies**: Track long-term outcomes
- **Intervention Effectiveness**: A/B test recovery strategies

---

## Conclusion

This architecture transforms BrainTrain from an AI interviewer into a sophisticated **Human Performance Transformation System**. The three pillars—Mind State System, Confidence Engine, and Pressure Conditioning—work together to build candidate confidence, communication clarity, and interview resilience.

The system maintains BrainTrain's core principles:
- Deterministic orchestration
- Low-latency realtime performance
- Observable, testable architecture
- Psychological safety
- Human-centered design

**Most importantly**: The system feels like a coach helping humans grow stronger, NOT a machine judging humans.

---

**Status**: Ready for implementation  
**Next Steps**: Begin Phase 1 foundation work
