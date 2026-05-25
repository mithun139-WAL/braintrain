"""
Realtime orchestrator contracts.

Defines data models for realtime interview orchestration and latency optimization.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    """Stages in the realtime interview pipeline."""
    STT = "stt"  # Speech to text
    TURN_ANALYSIS = "turn_analysis"  # Analyze turn completion
    DECISION_MAKING = "decision_making"  # Decide next action
    CONTEXT_ASSEMBLY = "context_assembly"  # Assemble context
    GENERATION = "generation"  # Generate response
    TTS = "tts"  # Text to speech
    DELIVERY = "delivery"  # Deliver to client


class RealtimeLatencyTarget(BaseModel):
    """Latency targets for realtime interview."""
    
    # Target: AI response begins within 700ms after candidate stops speaking
    total_target_ms: int = 700
    
    # Component targets
    stt_target_ms: int = 150
    turn_analysis_target_ms: int = 50
    decision_making_target_ms: int = 50
    context_assembly_target_ms: int = 100
    question_generation_target_ms: int = 250
    tts_target_ms: int = 100
    
    # Acceptable p95
    p95_total_ms: int = 1000


class RealtimeMetrics(BaseModel):
    """Real-time latency metrics."""
    
    # Measured latencies
    stt_latency_ms: Optional[int] = None
    turn_analysis_latency_ms: Optional[int] = None
    decision_latency_ms: Optional[int] = None
    context_assembly_latency_ms: Optional[int] = None
    question_generation_latency_ms: Optional[int] = None
    tts_latency_ms: Optional[int] = None
    transport_latency_ms: Optional[int] = None
    
    # Total
    total_latency_ms: Optional[int] = None
    
    # Flags
    met_target: bool = False
    exceeded_p95: bool = False
    
    # Optimization
    cache_hit: bool = False
    speculative_generation_used: bool = False
    prefetch_used: bool = False


class SpeculativeGeneration(BaseModel):
    """Speculative generation for latency reduction."""
    
    enabled: bool = True
    
    # Pre-generate next question
    pregenerate_next_question: bool = True
    pregenerate_followup: bool = True
    pregenerate_hint: bool = False
    
    # Cache strategy
    cache_likely_questions: bool = True
    cache_ttl_seconds: int = 300


class PartialTranscript(BaseModel):
    """Partial transcript for early processing."""
    
    text: str
    is_final: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class InterruptionEvent(BaseModel):
    """Candidate interruption event."""
    
    interrupted_at_ms: int
    partial_transcript_before_interruption: str
    candidate_new_transcript: str
    
    # Cancellation
    should_cancel_generation: bool = True
    should_cancel_tts: bool = True


class ResponseStreamChunk(BaseModel):
    """Chunk of streaming response."""
    
    chunk_text: str
    chunk_index: int
    is_final: bool = False
    
    # Audio
    audio_chunk: Optional[bytes] = None
    audio_duration_ms: Optional[int] = None


class RealtimeOptimization(BaseModel):
    """Optimization strategies for realtime performance."""
    
    # Parallelization
    parallel_stt_and_analysis: bool = True
    parallel_context_and_knowledge: bool = True
    
    # Prefetching
    prefetch_resume_chunks: bool = True
    prefetch_knowledge: bool = True
    prefetch_memories: bool = True
    
    # Caching
    cache_persona: bool = True
    cache_interview_rules: bool = True
    cache_system_prompt: bool = True
    
    # Speculative execution
    enable_speculative_generation: bool = True
    speculative_confidence_threshold: float = 0.7


class RealtimeBuffer(BaseModel):
    """Buffering strategy for smooth playback."""
    
    enable_buffering: bool = True
    buffer_size_ms: int = 500
    min_buffer_ms: int = 200
    
    # Adaptive buffering
    adaptive_buffer: bool = True
    increase_on_jitter: bool = True


class LatencyBreakdown(BaseModel):
    """Detailed latency breakdown for optimization."""
    
    # End-to-end
    candidate_stops_speaking_timestamp: datetime
    ai_starts_speaking_timestamp: datetime
    total_latency_ms: int
    
    # Pipeline stages
    stt_start: datetime
    stt_end: datetime
    stt_duration_ms: int
    
    analysis_start: datetime
    analysis_end: datetime
    analysis_duration_ms: int
    
    decision_start: datetime
    decision_end: datetime
    decision_duration_ms: int
    
    context_start: datetime
    context_end: datetime
    context_duration_ms: int
    
    generation_start: datetime
    generation_end: datetime
    generation_duration_ms: int
    
    tts_start: datetime
    tts_end: datetime
    tts_duration_ms: int
    
    # Bottleneck identification
    slowest_stage: str
    slowest_stage_duration_ms: int


class RealtimeQualityMetrics(BaseModel):
    """Quality metrics for realtime experience."""
    
    # Responsiveness
    average_latency_ms: float
    p50_latency_ms: int
    p95_latency_ms: int
    p99_latency_ms: int
    
    # Consistency
    latency_variance_ms: float
    latency_jitter_ms: float
    
    # Interruption handling
    interruption_count: int
    interruption_recovery_avg_ms: float
    
    # Audio quality
    audio_stutter_count: int
    audio_gap_count: int
    
    # Success rate
    successful_turns: int
    failed_turns: int
    timeout_turns: int


class RealtimeAlert(BaseModel):
    """Alert for realtime performance issues."""
    
    alert_type: str  # latency_spike, timeout, error, degradation
    severity: str  # low, medium, high, critical
    message: str
    
    # Context
    session_id: str
    turn_index: int
    latency_ms: Optional[int] = None
    
    # Impact
    user_visible: bool
    requires_fallback: bool
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
