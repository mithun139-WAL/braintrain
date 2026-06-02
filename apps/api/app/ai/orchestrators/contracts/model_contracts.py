"""
Model orchestrator contracts.

Defines data models for model selection, routing, and fallback.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


class ModelTask(str, Enum):
    """Task types for model selection."""
    REALTIME_RESPONSE = "realtime_response"
    FOLLOWUP_GENERATION = "followup_generation"
    EVALUATION = "evaluation"
    SUMMARIZATION = "summarization"
    MEMORY_EXTRACTION = "memory_extraction"
    KNOWLEDGE_SYNTHESIS = "knowledge_synthesis"
    TRANSCRIPT_CLEANUP = "transcript_cleanup"
    PERSONA_GENERATION = "persona_generation"
    ANSWER_CLASSIFICATION = "answer_classification"
    TOPIC_EXTRACTION = "topic_extraction"
    QUESTION_GENERATION = "question_generation"
    CONTEXT_SUMMARIZATION = "context_summarization"
    COACHING = "coaching"


class ModelProvider(str, Enum):
    """Supported model providers."""
    OPENAI = "openai"
    NIM = "nim"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    LOCAL = "local"
    STUB = "stub"


class ModelCapability(str, Enum):
    """Model capabilities."""
    REALTIME = "realtime"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    JSON_MODE = "json_mode"
    VISION = "vision"
    EMBEDDING = "embedding"


class ModelSelection(BaseModel):
    """Selected model configuration."""
    
    provider: ModelProvider
    model: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=32000)
    timeout_seconds: int = Field(default=10, ge=1, le=60)
    
    # Advanced parameters
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    
    # Capabilities
    supports_streaming: bool = False
    supports_json_mode: bool = False
    supports_function_calling: bool = False
    
    # Cost/performance
    estimated_cost_per_1k_tokens: float = 0.0
    estimated_latency_p50_ms: int = 0
    estimated_latency_p95_ms: int = 0


class ModelRoutingPolicy(BaseModel):
    """Policy for routing tasks to models."""
    
    policy_name: str
    
    # Task routing
    task_model_mapping: Dict[str, str] = Field(default_factory=dict)
    
    # Criteria
    prioritize_latency: bool = False
    prioritize_cost: bool = False
    prioritize_quality: bool = True
    
    # Thresholds
    max_latency_ms: Optional[int] = None
    max_cost_per_request: Optional[float] = None
    min_quality_score: float = 0.7
    
    # Fallback chain
    fallback_providers: List[ModelProvider] = Field(default_factory=list)


class ModelLatency(BaseModel):
    """Latency tracking for a model call."""
    provider: ModelProvider
    total_ms: float
    queue_ms: float = 0.0
    generation_ms: float = 0.0
    network_ms: float = 0.0


class ModelConfig(BaseModel):
    """Configuration for a model provider."""
    provider: ModelProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout_seconds: int = 30


class ModelPerformanceMetrics(BaseModel):
    """Performance metrics for a model."""
    
    provider: ModelProvider
    model: str
    
    # Latency
    avg_latency_ms: float
    p50_latency_ms: int
    p95_latency_ms: int
    p99_latency_ms: int
    
    # Success rate
    success_rate: float = Field(ge=0.0, le=1.0)
    timeout_rate: float = Field(ge=0.0, le=1.0)
    error_rate: float = Field(ge=0.0, le=1.0)
    
    # Quality
    average_quality_score: float = Field(ge=0.0, le=1.0)
    
    # Cost
    total_cost_usd: float
    cost_per_request_usd: float
    
    # Volume
    request_count: int
    token_count: int


class ModelRequest(BaseModel):
    """Request to a model."""
    
    task: ModelTask
    prompt: str
    system_prompt: Optional[str] = None
    
    # Context (accepts string, dict, or None)
    context: Optional[Any] = None
    
    # Parameters
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout_seconds: Optional[int] = None
    timeout_ms: Optional[int] = None
    
    # Format
    response_format: Optional[str] = None  # json, text
    json_schema: Optional[Dict[str, Any]] = None
    
    # Streaming
    stream: bool = False
    
    # Metadata
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def convert_context_and_timeout(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Ensure context defaults to dict if needed by any downstream consumers
            # but allow string / None values in the instance field by keeping it Any
            if "timeout_ms" in data and "timeout_seconds" not in data:
                data["timeout_seconds"] = int(data["timeout_ms"] / 1000)
        return data


class ModelResponse(BaseModel):
    """Response from a model."""
    
    content: Optional[str] = None
    text: str = ""
    
    # Metadata
    provider: ModelProvider
    model: str
    task: Optional[ModelTask] = None
    
    # Tokens
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tokens_used: int = 0
    
    # Performance
    latency_ms: float
    cost_usd: Optional[float] = None
    
    # Quality
    quality_score: Optional[float] = None
    
    # Flags
    was_cached: bool = False
    was_fallback: bool = False
    success: bool = True
    from_cache: bool = False
    
    # Request metadata
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def populate_compat_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync text and content
            if "text" in data and not data.get("content"):
                data["content"] = data["text"]
            elif "content" in data and not data.get("text"):
                data["text"] = data["content"]
            
            # Sync tokens
            if "tokens_used" in data and not data.get("total_tokens"):
                data["total_tokens"] = data["tokens_used"]
            elif "total_tokens" in data and not data.get("tokens_used"):
                data["tokens_used"] = data["total_tokens"]
                
            # Sync cache status
            if "was_cached" in data and "from_cache" not in data:
                data["from_cache"] = data["was_cached"]
            elif "from_cache" in data and "was_cached" not in data:
                data["was_cached"] = data["from_cache"]
        return data


class FallbackTrigger(str, Enum):
    """Reasons for fallback."""
    TIMEOUT = "timeout"
    ERROR = "error"
    RATE_LIMIT = "rate_limit"
    QUALITY_TOO_LOW = "quality_too_low"
    COST_TOO_HIGH = "cost_too_high"
    PROVIDER_DOWN = "provider_down"


class FallbackEvent(BaseModel):
    """Fallback event record."""
    
    trigger: FallbackTrigger
    original_provider: ModelProvider
    original_model: str
    fallback_provider: ModelProvider
    fallback_model: str
    
    task: ModelTask
    reason: str
    
    # Impact
    latency_impact_ms: int
    cost_impact_usd: Optional[float] = None
    
    request_id: Optional[str] = None


class ModelHealthStatus(BaseModel):
    """Health status of a model."""
    
    provider: ModelProvider
    model: str
    
    is_healthy: bool
    status: str  # healthy, degraded, down
    
    # Recent metrics (last 5 min)
    recent_success_rate: float
    recent_avg_latency_ms: float
    recent_error_rate: float
    
    last_successful_request: Optional[int] = None  # timestamp
    last_error: Optional[str] = None
    consecutive_failures: int = 0


class ModelSelectionRequest(BaseModel):
    """Request for model selection."""
    
    task: ModelTask
    
    # Requirements
    required_capabilities: List[ModelCapability] = Field(default_factory=list)
    max_latency_ms: Optional[int] = None
    max_cost: Optional[float] = None
    
    # Context
    urgency: str = "normal"  # low, normal, high, critical
    quality_requirement: str = "standard"  # low, standard, high
    
    # Fallback
    enable_fallback: bool = True
    max_fallback_attempts: int = 2
