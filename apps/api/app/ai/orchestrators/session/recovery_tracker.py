"""
Recovery Tracker — detects and scores mistake-recovery arcs.

Core insight from the session assessment:
    Confidence is built during recovery, not success.
    The system must detect STUMBLE → RECOVERY_ATTEMPT → RECOVERED arcs
    and distinguish candidate-induced errors from interviewer-induced loops.

Why this matters for fairness:
    The current analytics engine sees "low quality answers" and penalises the
    candidate.  But in a recursive-detail-lock session, those low-quality answers
    were *caused by the interviewer looping*, not a genuine knowledge gap.
    The RecoveryTracker tags each stumble with its cause so downstream analytics
    don't automate injustice.

Recovery arc state machine:
    STABLE → STUMBLE → RECOVERY_ATTEMPT → RECOVERED
                    ↘                   ↘ COLLAPSED (if no recovery in 3 turns)

Stumble cause taxonomy:
    CANDIDATE_ERROR     — genuine knowledge gap or reasoning failure
    INTERVIEWER_LOOP    — caused by recursive questioning on the same topic
    AMBIGUOUS_QUESTION  — question was unclear or under-specified
    PRESSURE_INDUCED    — candidate destabilised by adversarial pressure
"""
from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RecoveryState(str, Enum):
    """Current state in the recovery arc state machine."""
    STABLE            = "stable"
    STUMBLE           = "stumble"
    RECOVERY_ATTEMPT  = "recovery_attempt"
    RECOVERED         = "recovered"
    COLLAPSED         = "collapsed"


class StumbleCause(str, Enum):
    """Attribution for each stumble event."""
    CANDIDATE_ERROR    = "candidate_error"
    INTERVIEWER_LOOP   = "interviewer_loop"
    AMBIGUOUS_QUESTION = "ambiguous_question"
    PRESSURE_INDUCED   = "pressure_induced"
    UNKNOWN            = "unknown"


# Quality buckets — mapped from AnswerQuality enum values
_GOOD_QUALITIES = {"excellent", "good"}
_WEAK_QUALITIES  = {"insufficient", "incorrect", "vague", "partial", "minimal"}

# Recovery signals detected in transcript (self-correction, hedging, clarification)
_RECOVERY_SIGNALS = [
    "actually", "let me correct", "i meant", "to clarify", "sorry,",
    "i should have said", "more precisely", "what i should have said",
    "rethinking", "on reflection", "let me reconsider", "wait,",
    "hmm, actually", "i realise", "i realize",
]

_CLARIFICATION_SIGNALS = [
    "can you clarify", "what do you mean", "could you rephrase",
    "i'm not sure i understand", "are you asking about",
]


class StumbleRecord(BaseModel):
    """A single stumble event with attribution."""
    turn_number: int
    cause: StumbleCause
    quality_at_stumble: str
    prior_quality: str
    was_in_loop: bool = False   # True if topic fixation was active at stumble time
    was_under_pressure: bool = False
    recovered: Optional[bool] = None  # None = outcome not yet known
    recovery_turns: Optional[int] = None
    recovery_quality_delta: Optional[float] = None


class RecoverySnapshot(BaseModel):
    """Analytics-ready summary of recovery arc tracking for a session."""

    total_stumbles: int = 0
    candidate_errors: int = 0      # CANDIDATE_ERROR only
    loop_induced_stumbles: int = 0  # INTERVIEWER_LOOP — excluded from candidate score
    pressure_induced_stumbles: int = 0
    ambiguous_question_stumbles: int = 0

    successful_recoveries: int = 0
    failed_recoveries: int = 0
    recovery_rate: float = 0.0      # successful / total stumbles with known outcome
    avg_recovery_turns: float = 0.0  # average turns to recover

    current_state: RecoveryState = RecoveryState.STABLE
    consecutive_stumbles: int = 0
    is_collapsed: bool = False


class RecoveryTracker:
    """
    Tracks the STUMBLE → RECOVERY arc for a single session.

    Call record_turn() after every candidate turn, passing the quality label
    and context signals.  Call get_snapshot() to obtain the current analytics state.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._state: RecoveryState = RecoveryState.STABLE
        self._stumbles: List[StumbleRecord] = []
        self._current_stumble: Optional[StumbleRecord] = None
        self._prior_quality: str = "good"
        self._total_turns: int = 0
        self._consecutive_stumbles: int = 0
        self._recovery_turn_count: int = 0

        # Running sums for averages
        self._recovery_turn_totals: int = 0
        self._recoveries_with_known_duration: int = 0

    # ── Public API ─────────────────────────────────────────────────────────────

    def record_turn(
        self,
        turn_number: int,
        answer_quality: str,           # AnswerQuality.value string
        transcript: str,
        is_topic_fixation_active: bool = False,
        is_under_pressure: bool = False,
        question_was_ambiguous: bool = False,
        performance_score: float = 70.0,
    ) -> RecoveryState:
        """
        Process one turn and advance the state machine.

        Returns the new RecoveryState after this turn.
        """
        self._total_turns += 1
        quality = answer_quality.lower()
        is_weak = quality in _WEAK_QUALITIES
        is_good = quality in _GOOD_QUALITIES

        # ── State transitions ──────────────────────────────────────────────────

        if self._state == RecoveryState.STABLE:
            if is_weak:
                cause = self._attribute_cause(
                    is_topic_fixation_active,
                    is_under_pressure,
                    question_was_ambiguous,
                    performance_score,
                )
                self._enter_stumble(turn_number, quality, cause, is_topic_fixation_active, is_under_pressure)

        elif self._state == RecoveryState.STUMBLE:
            self._recovery_turn_count += 1
            has_self_correction = self._detect_self_correction(transcript)
            has_clarification = self._detect_clarification_request(transcript)

            if is_good:
                self._enter_recovered(turn_number)
            elif has_self_correction or has_clarification:
                self._state = RecoveryState.RECOVERY_ATTEMPT
                logger.debug("RecoveryTracker: RECOVERY_ATTEMPT detected at turn %d", turn_number)
            elif self._recovery_turn_count >= 3:
                self._enter_collapsed(turn_number)

        elif self._state == RecoveryState.RECOVERY_ATTEMPT:
            self._recovery_turn_count += 1
            if is_good:
                self._enter_recovered(turn_number)
            elif self._recovery_turn_count >= 3:
                self._enter_collapsed(turn_number)

        elif self._state == RecoveryState.RECOVERED:
            # Back to stable after one good turn
            if is_weak:
                cause = self._attribute_cause(
                    is_topic_fixation_active, is_under_pressure,
                    question_was_ambiguous, performance_score,
                )
                self._enter_stumble(turn_number, quality, cause, is_topic_fixation_active, is_under_pressure)
            else:
                self._state = RecoveryState.STABLE

        elif self._state == RecoveryState.COLLAPSED:
            if is_good:
                # Pulled back from collapse
                self._state = RecoveryState.STABLE
                self._consecutive_stumbles = 0
                self._recovery_turn_count = 0
                logger.info("RecoveryTracker: recovered from COLLAPSE at turn %d", turn_number)

        self._prior_quality = quality
        return self._state

    def get_snapshot(self) -> RecoverySnapshot:
        """Return analytics-ready snapshot of recovery state."""
        candidate_errors = sum(
            1 for s in self._stumbles if s.cause == StumbleCause.CANDIDATE_ERROR
        )
        loop_induced = sum(
            1 for s in self._stumbles if s.cause == StumbleCause.INTERVIEWER_LOOP
        )
        pressure_induced = sum(
            1 for s in self._stumbles if s.cause == StumbleCause.PRESSURE_INDUCED
        )
        ambiguous = sum(
            1 for s in self._stumbles if s.cause == StumbleCause.AMBIGUOUS_QUESTION
        )
        successful = sum(1 for s in self._stumbles if s.recovered is True)
        failed = sum(1 for s in self._stumbles if s.recovered is False)
        known_outcomes = successful + failed

        return RecoverySnapshot(
            total_stumbles=len(self._stumbles),
            candidate_errors=candidate_errors,
            loop_induced_stumbles=loop_induced,
            pressure_induced_stumbles=pressure_induced,
            ambiguous_question_stumbles=ambiguous,
            successful_recoveries=successful,
            failed_recoveries=failed,
            recovery_rate=(successful / known_outcomes) if known_outcomes > 0 else 0.0,
            avg_recovery_turns=(
                self._recovery_turn_totals / self._recoveries_with_known_duration
                if self._recoveries_with_known_duration > 0 else 0.0
            ),
            current_state=self._state,
            consecutive_stumbles=self._consecutive_stumbles,
            is_collapsed=self._state == RecoveryState.COLLAPSED,
        )

    @property
    def current_state(self) -> RecoveryState:
        return self._state

    @property
    def is_in_stumble(self) -> bool:
        return self._state in (
            RecoveryState.STUMBLE,
            RecoveryState.RECOVERY_ATTEMPT,
        )

    @property
    def is_collapsed(self) -> bool:
        return self._state == RecoveryState.COLLAPSED

    # ── State machine helpers ─────────────────────────────────────────────────

    def _enter_stumble(
        self,
        turn_number: int,
        quality: str,
        cause: StumbleCause,
        in_loop: bool,
        under_pressure: bool,
    ) -> None:
        self._state = RecoveryState.STUMBLE
        self._recovery_turn_count = 0
        self._consecutive_stumbles += 1

        record = StumbleRecord(
            turn_number=turn_number,
            cause=cause,
            quality_at_stumble=quality,
            prior_quality=self._prior_quality,
            was_in_loop=in_loop,
            was_under_pressure=under_pressure,
        )
        self._stumbles.append(record)
        self._current_stumble = record

        logger.info(
            "RecoveryTracker: STUMBLE at turn %d | cause=%s in_loop=%s",
            turn_number, cause.value, in_loop,
        )

    def _enter_recovered(self, turn_number: int) -> None:
        self._state = RecoveryState.RECOVERED
        self._consecutive_stumbles = 0
        turns_taken = self._recovery_turn_count

        if self._current_stumble:
            self._current_stumble.recovered = True
            self._current_stumble.recovery_turns = turns_taken

        self._recovery_turn_totals += turns_taken
        self._recoveries_with_known_duration += 1
        self._recovery_turn_count = 0
        self._current_stumble = None

        logger.info(
            "RecoveryTracker: RECOVERED at turn %d in %d turns",
            turn_number, turns_taken,
        )

    def _enter_collapsed(self, turn_number: int) -> None:
        self._state = RecoveryState.COLLAPSED
        if self._current_stumble:
            self._current_stumble.recovered = False
            self._current_stumble.recovery_turns = self._recovery_turn_count
        self._current_stumble = None

        logger.warning(
            "RecoveryTracker: COLLAPSED at turn %d after %d recovery attempts",
            turn_number, self._recovery_turn_count,
        )

    # ── Attribution ───────────────────────────────────────────────────────────

    def _attribute_cause(
        self,
        is_topic_fixation_active: bool,
        is_under_pressure: bool,
        question_was_ambiguous: bool,
        performance_score: float,
    ) -> StumbleCause:
        """
        Determine why the stumble occurred.

        Priority: loop > ambiguous question > pressure > genuine error.
        This ordering is conservative — we don't blame the candidate unless
        there's no other explanation.
        """
        if is_topic_fixation_active:
            return StumbleCause.INTERVIEWER_LOOP
        if question_was_ambiguous:
            return StumbleCause.AMBIGUOUS_QUESTION
        if is_under_pressure and performance_score >= 50:
            # Score was OK before — pressure likely caused the stumble
            return StumbleCause.PRESSURE_INDUCED
        return StumbleCause.CANDIDATE_ERROR

    # ── Transcript signal detection ───────────────────────────────────────────

    def _detect_self_correction(self, transcript: str) -> bool:
        text = transcript.lower()
        return any(sig in text for sig in _RECOVERY_SIGNALS)

    def _detect_clarification_request(self, transcript: str) -> bool:
        text = transcript.lower()
        return any(sig in text for sig in _CLARIFICATION_SIGNALS)
