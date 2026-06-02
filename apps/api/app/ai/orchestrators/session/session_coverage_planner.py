"""
Session Coverage Planner — session-level competency breadth manager.

Responsibility:
    Track which competency areas have been explored and how deeply, then
    issue deterministic steering directives (PIVOT, ZOOM_OUT, etc.) so the
    interviewer agent covers the full competency map before the session ends.

Why this exists:
    The turn layer optimises for immediate conversational relevance.  It has
    no notion of "we've spent 6 turns on caching and never touched API design."
    This planner holds that macro view and injects it as a CoverageDirective
    that the SessionOrchestrator feeds into every turn decision.

Design principles:
    • Deterministic: no LLM involved in coverage tracking or directive selection.
    • Bridge phrases are pre-rendered templates — zero added latency.
    • Coverage is area-level (not sub-topic level) to keep state small.
    • Directive is advisory, not mandatory — turn layer can override if
      the candidate is mid-recovery or escalation is active.
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, PrivateAttr

from app.ai.orchestrators.contracts.interview_contracts import InterviewDomain

logger = logging.getLogger(__name__)

# ─── Competency Maps ──────────────────────────────────────────────────────────

# Each domain maps competency area → list of signals/keywords that indicate
# the candidate is discussing that area (used for area detection from transcript).
_DOMAIN_COMPETENCY_SIGNALS: Dict[str, Dict[str, List[str]]] = {
    "backend": {
        "scalability": [
            "scale", "throughput", "load balanc", "horizontal", "vertical",
            "partition", "shard", "replica", "cdn", "rate limit",
        ],
        "data_layer": [
            "index", "query", "sql", "nosql", "schema", "migration", "join",
            "postgres", "mysql", "mongodb", "dynamo", "cassandra",
        ],
        "caching": [
            "cache", "redis", "memcached", "ttl", "invalidat", "evict",
            "warm", "hit rate", "stale",
        ],
        "api_design": [
            "api", "rest", "graphql", "grpc", "endpoint", "versioning",
            "contract", "webhook", "rate limit", "pagination",
        ],
        "reliability": [
            "retry", "circuit", "failover", "timeout", "idempotent",
            "observ", "metric", "alert", "sla", "slo", "uptime",
        ],
        "async_processing": [
            "queue", "kafka", "rabbitmq", "worker", "job", "event",
            "async", "stream", "consumer", "producer", "message",
        ],
        "security": [
            "auth", "oauth", "jwt", "encrypt", "permission", "role",
            "secret", "token", "ssl", "tls",
        ],
        "communication": [
            "tradeoff", "decision", "chose", "alternative", "consider",
            "constraint", "requirement", "stakeholder",
        ],
    },
    "frontend": {
        "rendering": [
            "render", "ssr", "csr", "hydrat", "virtual dom", "reconcil",
            "paint", "reflow",
        ],
        "state_management": [
            "state", "redux", "context", "zustand", "mobx", "signal",
            "reactive", "store",
        ],
        "performance": [
            "bundle", "lazy", "code split", "lcp", "fid", "cls", "lighthouse",
            "prefetch", "cache", "web vital",
        ],
        "component_design": [
            "component", "prop", "hook", "composition", "pattern",
            "reusab", "abstraction",
        ],
        "accessibility": [
            "a11y", "aria", "keyboard", "screen reader", "wcag", "focus",
            "semantic",
        ],
        "communication": [
            "tradeoff", "decision", "chose", "alternative", "consider",
            "constraint",
        ],
    },
    "system_design": {
        "architecture": [
            "architect", "monolith", "microservice", "service mesh",
            "event-driven", "cqrs", "saga",
        ],
        "data_modeling": [
            "schema", "model", "entit", "relation", "normali", "denormali",
            "data flow",
        ],
        "scalability": [
            "scale", "throughput", "partiti", "shard", "replica", "cap",
            "consistency", "availability",
        ],
        "reliability": [
            "failover", "replication", "backup", "recovery", "rto", "rpo",
            "disaster",
        ],
        "tradeoffs": [
            "tradeoff", "chose", "versus", "alternative", "pros and cons",
            "compromise",
        ],
        "communication": [
            "requirement", "clarif", "constraint", "assumption", "stakeholder",
            "priorit",
        ],
    },
}

# Fallback for mixed/unknown domains
_DEFAULT_COMPETENCIES = {
    "technical_depth": ["implement", "design", "build", "architect", "scale"],
    "problem_solving": ["approach", "solve", "debug", "root cause", "diagnose"],
    "communication": ["tradeoff", "consider", "chose", "alternative", "explain"],
    "behavioral": ["team", "conflict", "ownership", "failure", "lesson"],
}

# ─── Bridge Phrase Templates ──────────────────────────────────────────────────
# Keyed as (from_area, to_area) → template string.
# {from_area} and {to_area} are substituted at runtime.
# These are deliberately human-sounding — not stiff transitions.

_BRIDGE_TEMPLATES: Dict[Tuple[str, str], str] = {
    ("caching", "api_design"): (
        "Good discussion on cache consistency. "
        "Let's zoom out — how did those caching decisions shape your API design?"
    ),
    ("caching", "data_layer"): (
        "Solid caching strategy. "
        "What drove the underlying data model that cache sat in front of?"
    ),
    ("caching", "scalability"): (
        "Good. Caching is one piece of the puzzle. "
        "Let's step back — how did caching fit into your overall scalability approach?"
    ),
    ("data_layer", "scalability"): (
        "Strong on the data layer. "
        "How did those schema and indexing choices hold up as traffic scaled?"
    ),
    ("data_layer", "api_design"): (
        "Good database depth. "
        "How did the data model influence how you designed the APIs on top of it?"
    ),
    ("data_layer", "reliability"): (
        "Solid data design. "
        "What happened when that layer failed — how did you handle recovery?"
    ),
    ("api_design", "scalability"): (
        "Good API design thinking. "
        "How did those APIs hold up under load — what was your scalability strategy?"
    ),
    ("api_design", "reliability"): (
        "Good on API contracts. "
        "What was your approach to making those APIs resilient to downstream failures?"
    ),
    ("api_design", "async_processing"): (
        "Good REST/GraphQL depth. "
        "Were there operations too slow for synchronous APIs — how did you handle those?"
    ),
    ("scalability", "reliability"): (
        "Solid scalability thinking. "
        "What was your strategy when individual components in that scaled system failed?"
    ),
    ("scalability", "data_layer"): (
        "Good on scale. "
        "Let's go deeper on the data layer — how did the DB handle that traffic?"
    ),
    ("reliability", "async_processing"): (
        "Good reliability design. "
        "Were there async workflows in that system — how did you handle failure there?"
    ),
    ("async_processing", "api_design"): (
        "Good on event-driven systems. "
        "How did clients interact with those async operations — what did the API contract look like?"
    ),
    ("communication", "technical_depth"): (
        "Good architectural reasoning. "
        "Let's go deeper technically — walk me through the implementation of the key component."
    ),
}

# Generic fallback bridge when no specific template exists
_GENERIC_BRIDGE = (
    "Good. Let's shift focus — {to_area_label}. "
    "How did you approach that in this system?"
)

_AREA_LABELS: Dict[str, str] = {
    "scalability": "let's talk scalability",
    "data_layer": "let's look at the data layer",
    "caching": "on caching",
    "api_design": "on API design",
    "reliability": "let's talk about reliability and failure handling",
    "async_processing": "on async and event-driven design",
    "security": "on security and auth",
    "communication": "let's zoom out to architectural decision-making",
    "rendering": "on rendering strategy",
    "state_management": "on state management",
    "performance": "on frontend performance",
    "component_design": "on component architecture",
    "accessibility": "on accessibility",
    "architecture": "on overall system architecture",
    "data_modeling": "on data modeling",
    "tradeoffs": "on tradeoffs and decision rationale",
    "technical_depth": "let's go deeper technically",
    "problem_solving": "let's talk problem-solving approach",
    "behavioral": "let's shift to a behavioral question",
}


# ─── Enums & Models ───────────────────────────────────────────────────────────

class SteerAction(str, Enum):
    """Directive the coverage planner issues for the current turn."""
    CONTINUE            = "continue"           # area has more depth; keep going
    PIVOT_TO            = "pivot_to"           # move to a different competency area
    ZOOM_OUT            = "zoom_out"           # elevate to architectural level in same area
    INTRODUCE_CONSTRAINT = "introduce_constraint"  # inject conflicting constraint
    PRESSURE_PROBE      = "pressure_probe"     # hand off to pressure layer
    COVERAGE_COMPLETE   = "coverage_complete"  # all areas adequately covered


class CompetencyArea(BaseModel):
    """Live tracking state for a single competency area."""

    name: str
    signals: List[str] = Field(default_factory=list)

    # Coverage tracking
    turns_spent: int = 0
    last_visited_turn: int = -1   # -1 = never visited
    coverage_score: float = 0.0   # 0.0 → 1.0, approaches 1 with diminishing returns

    # Saturation tracking
    consecutive_turns: int = 0    # unbroken run of turns in this area
    signal_hits_last_turn: int = 0

    def record_visit(self, turn_number: int, signal_hits: int) -> None:
        """Update coverage state when this area is active in a turn."""
        self.turns_spent += 1
        
        if self.last_visited_turn == turn_number - 1:
            self.consecutive_turns += 1
        else:
            self.consecutive_turns = 1
            
        self.last_visited_turn = turn_number
        self.signal_hits_last_turn = signal_hits

        # Diminishing returns: each additional turn adds less to coverage_score
        gain = 0.25 / (1 + self.turns_spent * 0.4)
        self.coverage_score = min(1.0, self.coverage_score + gain)

    def is_saturated(self, saturation_threshold: float = 0.75) -> bool:
        return self.coverage_score >= saturation_threshold

    def is_unvisited(self) -> bool:
        return self.last_visited_turn == -1

    @property
    def turns_since_visited(self) -> int:
        """Returns inf sentinel (999) if never visited."""
        return 999 if self.last_visited_turn == -1 else 0  # computed externally with turn_number


class CoverageDirective(BaseModel):
    """Output of the coverage planner for a single turn."""

    steer_action: SteerAction
    current_area: Optional[str] = None
    target_area: Optional[str] = None

    # Pre-rendered bridge phrase for PIVOT / ZOOM_OUT — injected verbatim
    bridge_phrase: Optional[str] = None

    # For INTRODUCE_CONSTRAINT: the constraint scenario to inject
    constraint_scenario: Optional[str] = None

    # Metadata for observability
    coverage_snapshot: Dict[str, float] = Field(default_factory=dict)
    uncovered_areas: List[str] = Field(default_factory=list)
    reason: str = ""


class CoveragePlannerConfig(BaseModel):
    """Tunable thresholds for the coverage planner."""

    # Turns before a single area is considered over-explored
    max_turns_per_area: int = 4

    # Consecutive turns in one area before forcing pivot
    max_consecutive_turns_in_area: int = 3

    # Coverage score threshold above which area is "saturated"
    saturation_threshold: float = 0.75

    # Minimum coverage fraction across all areas before "complete"
    min_overall_coverage: float = 0.60

    # How many unvisited areas trigger breadth-debt pressure
    breadth_debt_threshold: int = 2

    # Minimum total session turns before activating (cold-start guard)
    min_turns_to_activate: int = 3

    # Constraint scenarios library (injected when INTRODUCE_CONSTRAINT fires)
    constraint_scenarios: List[str] = Field(default_factory=lambda: [
        "Now assume your traffic suddenly 10x'd overnight — what breaks first?",
        "Your primary database just became unavailable for 30 seconds. Walk me through what happens.",
        "Product tells you the API latency SLA just tightened from 500ms to 100ms. What changes?",
        "You need to add multi-tenancy to this system with zero downtime. Where do you start?",
        "Your cache hit rate dropped from 95% to 40% — how do you diagnose and fix it?",
    ])
    _constraint_index: int = PrivateAttr(default=0)


# ─── Planner ─────────────────────────────────────────────────────────────────

class SessionCoveragePlanner:
    """
    Tracks competency coverage across the session and issues steering directives.

    Instantiate once per session.  Call record_turn() after every candidate
    response, then get_directive() to obtain the steering recommendation for
    the current turn.
    """

    def __init__(
        self,
        domain: str = "backend",
        config: Optional[CoveragePlannerConfig] = None,
    ) -> None:
        self.config = config or CoveragePlannerConfig()
        self.domain = domain

        # Build competency map for this domain
        signal_map = (
            _DOMAIN_COMPETENCY_SIGNALS.get(domain)
            or _DEFAULT_COMPETENCIES
        )
        self.areas: Dict[str, CompetencyArea] = {
            name: CompetencyArea(name=name, signals=signals)
            for name, signals in signal_map.items()
        }

        self._total_turns: int = 0
        self._current_area: Optional[str] = None
        self._prev_area: Optional[str] = None

        logger.info(
            "SessionCoveragePlanner init: domain=%s areas=%s",
            domain,
            list(self.areas.keys()),
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def record_turn(self, transcript: str, turn_number: int) -> str:
        """
        Detect which competency area is active in this turn and update state.

        Returns:
            The name of the detected area (or "unknown").
        """
        self._total_turns += 1
        detected = self._detect_area(transcript)

        if detected:
            self.areas[detected].record_visit(turn_number, self._count_signals(transcript, detected))
            self._prev_area = self._current_area
            self._current_area = detected
        else:
            # Transcript didn't match any area — attribute to current if known
            if self._current_area:
                self.areas[self._current_area].record_visit(turn_number, 0)

        return detected or (self._current_area or "unknown")

    def get_directive(self, turn_number: int) -> CoverageDirective:
        """
        Return the coverage steering directive for the current turn.

        Called AFTER record_turn() for the same turn.
        """
        # Cold-start: don't steer until we have enough signal
        if self._total_turns < self.config.min_turns_to_activate:
            return CoverageDirective(
                steer_action=SteerAction.CONTINUE,
                current_area=self._current_area,
                reason="cold_start",
                coverage_snapshot=self._snapshot(),
            )

        # Check overall coverage completeness
        if self._overall_coverage() >= self.config.min_overall_coverage:
            return CoverageDirective(
                steer_action=SteerAction.COVERAGE_COMPLETE,
                current_area=self._current_area,
                reason="all_areas_adequately_covered",
                coverage_snapshot=self._snapshot(),
            )

        current = self._current_area
        if current is None:
            return self._pivot_to_best_uncovered(turn_number, reason="no_area_detected")

        area = self.areas[current]

        # 1. Consecutive turns exceeded — force pivot
        if area.consecutive_turns >= self.config.max_consecutive_turns_in_area:
            return self._pivot_to_best_uncovered(
                turn_number,
                reason=f"consecutive_turns_exceeded:{area.consecutive_turns}",
            )

        # 2. Total turns in area exceeded — force pivot
        if area.turns_spent >= self.config.max_turns_per_area:
            return self._pivot_to_best_uncovered(
                turn_number,
                reason=f"max_turns_per_area_exceeded:{area.turns_spent}",
            )

        # 3. Area saturated + breadth debt — force pivot
        if area.is_saturated(self.config.saturation_threshold):
            unvisited = self._unvisited_areas()
            if len(unvisited) >= self.config.breadth_debt_threshold:
                return self._pivot_to_best_uncovered(
                    turn_number,
                    reason=f"area_saturated+breadth_debt:{len(unvisited)}_unvisited",
                )
            else:
                # Saturated but breadth is OK — zoom out
                return CoverageDirective(
                    steer_action=SteerAction.ZOOM_OUT,
                    current_area=current,
                    bridge_phrase=self._zoom_out_phrase(current),
                    reason="area_saturated_zoom_out",
                    coverage_snapshot=self._snapshot(),
                    uncovered_areas=[a for a in self._unvisited_areas()],
                )

        # 4. Continue in current area
        return CoverageDirective(
            steer_action=SteerAction.CONTINUE,
            current_area=current,
            reason="within_depth_budget",
            coverage_snapshot=self._snapshot(),
            uncovered_areas=[a for a in self._unvisited_areas()],
        )

    def next_constraint_scenario(self) -> str:
        """Round-robin constraint scenario injection."""
        idx = self.config._constraint_index
        scenario = self.config.constraint_scenarios[idx % len(self.config.constraint_scenarios)]
        self.config._constraint_index = idx + 1
        return scenario

    def get_coverage_summary(self) -> Dict[str, float]:
        return {name: area.coverage_score for name, area in self.areas.items()}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _detect_area(self, transcript: str) -> Optional[str]:
        """Return the area with the most signal hits, or None if below threshold."""
        text = transcript.lower()
        scores: Dict[str, int] = {}
        for name, area in self.areas.items():
            hits = sum(1 for sig in area.signals if sig in text)
            if hits > 0:
                scores[name] = hits
        if not scores:
            return None
        return max(scores, key=lambda k: scores[k])

    def _count_signals(self, transcript: str, area_name: str) -> int:
        text = transcript.lower()
        return sum(1 for sig in self.areas[area_name].signals if sig in text)

    def _unvisited_areas(self) -> List[str]:
        return [n for n, a in self.areas.items() if a.is_unvisited()]

    def _least_covered_area(self, exclude: Optional[str] = None) -> Optional[str]:
        """Return the area with the lowest coverage score, excluding current."""
        candidates = {
            n: a for n, a in self.areas.items()
            if n != exclude
        }
        if not candidates:
            return None
        return min(candidates, key=lambda k: candidates[k].coverage_score)

    def _pivot_to_best_uncovered(self, turn_number: int, reason: str) -> CoverageDirective:
        # Prefer completely unvisited, then least covered
        unvisited = self._unvisited_areas()
        target = (
            unvisited[0] if unvisited
            else self._least_covered_area(exclude=self._current_area)
        )

        bridge = self._make_bridge(self._current_area, target)

        logger.info(
            "CoveragePlanner PIVOT: %s → %s | reason=%s",
            self._current_area,
            target,
            reason,
        )

        return CoverageDirective(
            steer_action=SteerAction.PIVOT_TO,
            current_area=self._current_area,
            target_area=target,
            bridge_phrase=bridge,
            reason=reason,
            coverage_snapshot=self._snapshot(),
            uncovered_areas=self._unvisited_areas(),
        )

    def _make_bridge(self, from_area: Optional[str], to_area: Optional[str]) -> str:
        if from_area and to_area:
            key = (from_area, to_area)
            if key in _BRIDGE_TEMPLATES:
                return _BRIDGE_TEMPLATES[key]
        # Generic fallback
        label = _AREA_LABELS.get(to_area or "", "a different area") if to_area else "the broader picture"
        return _GENERIC_BRIDGE.format(to_area_label=label)

    def _zoom_out_phrase(self, area: str) -> str:
        label = _AREA_LABELS.get(area, area)
        return (
            f"We've covered {label} in good depth. "
            "Let's zoom out — how did this fit into the overall system architecture and "
            "what were the key architectural tradeoffs you made?"
        )

    def _overall_coverage(self) -> float:
        if not self.areas:
            return 0.0
        return sum(a.coverage_score for a in self.areas.values()) / len(self.areas)

    def _snapshot(self) -> Dict[str, float]:
        return {n: round(a.coverage_score, 2) for n, a in self.areas.items()}
