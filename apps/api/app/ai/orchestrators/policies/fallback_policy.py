"""
Fallback policy for production resilience.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from app.ai.orchestrators.contracts.model_contracts import ModelProvider, FallbackTrigger

logger = logging.getLogger(__name__)


class FallbackStrategy(BaseModel):
    """Strategy for fallback behavior."""
    
    strategy_name: str
    
    # Retry configuration
    max_retries: int = 2
    retry_delay_seconds: float = 0.5
    exponential_backoff: bool = True
    
    # Provider fallback
    fallback_chain: List[ModelProvider] = Field(default_factory=list)
    skip_failed_providers: bool = True
    
    # Degraded mode
    enable_degraded_mode: bool = True
    degraded_mode_quality_threshold: float = 0.5
    
    # Caching
    use_cached_response: bool = True
    cache_fallback_duration_seconds: int = 300
    
    # Rule-based fallback
    use_rule_based_fallback: bool = True


class FallbackPolicy(BaseModel):
    """Comprehensive fallback policy for production resilience."""
    
    policy_name: str = "default_fallback"
    
    # Global settings
    enable_fallback: bool = True
    max_total_attempts: int = 3
    
    # Trigger-specific strategies
    timeout_strategy: FallbackStrategy = Field(
        default_factory=lambda: FallbackStrategy(
            strategy_name="timeout",
            max_retries=2,
            fallback_chain=[ModelProvider.GROQ, ModelProvider.LOCAL],
            use_cached_response=True
        )
    )
    
    error_strategy: FallbackStrategy = Field(
        default_factory=lambda: FallbackStrategy(
            strategy_name="error",
            max_retries=1,
            fallback_chain=[ModelProvider.OPENAI, ModelProvider.LOCAL],
            use_rule_based_fallback=True
        )
    )
    
    rate_limit_strategy: FallbackStrategy = Field(
        default_factory=lambda: FallbackStrategy(
            strategy_name="rate_limit",
            max_retries=0,
            fallback_chain=[ModelProvider.NIM, ModelProvider.LOCAL],
            use_cached_response=True
        )
    )
    
    quality_strategy: FallbackStrategy = Field(
        default_factory=lambda: FallbackStrategy(
            strategy_name="quality",
            max_retries=1,
            fallback_chain=[ModelProvider.OPENAI],
            enable_degraded_mode=False
        )
    )
    
    # Cache configuration
    cache_successful_responses: bool = True
    cache_ttl_seconds: int = 600
    
    # Metrics tracking
    track_fallback_metrics: bool = True
    alert_on_repeated_fallbacks: bool = True
    alert_threshold: int = 3
    
    def get_strategy(self, trigger: FallbackTrigger) -> FallbackStrategy:
        """Get fallback strategy for a specific trigger."""
        strategies = {
            FallbackTrigger.TIMEOUT: self.timeout_strategy,
            FallbackTrigger.ERROR: self.error_strategy,
            FallbackTrigger.RATE_LIMIT: self.rate_limit_strategy,
            FallbackTrigger.QUALITY_TOO_LOW: self.quality_strategy,
            FallbackTrigger.PROVIDER_DOWN: self.error_strategy,
        }
        return strategies.get(trigger, self.error_strategy)
    
    def should_use_cache(self, trigger: FallbackTrigger) -> bool:
        """Determine if cache should be used for this trigger."""
        strategy = self.get_strategy(trigger)
        return strategy.use_cached_response
    
    def should_use_rule_based(self, trigger: FallbackTrigger) -> bool:
        """Determine if rule-based fallback should be used."""
        strategy = self.get_strategy(trigger)
        return strategy.use_rule_based_fallback
    
    def get_fallback_chain(self, trigger: FallbackTrigger) -> List[ModelProvider]:
        """Get provider fallback chain for this trigger."""
        strategy = self.get_strategy(trigger)
        return strategy.fallback_chain


class DegradedModeConfig(BaseModel):
    """Configuration for degraded mode operation."""
    
    enabled: bool = True
    
    # Simplified responses
    use_template_responses: bool = True
    simplify_prompts: bool = True
    reduce_context_window: bool = True
    
    # Caching
    aggressive_caching: bool = True
    cache_common_questions: bool = True
    
    # Quality tradeoffs
    accept_lower_quality: bool = True
    min_acceptable_quality: float = 0.3
    
    # User communication
    notify_user: bool = False
    degraded_mode_message: str = "Experiencing temporary latency..."


class RuleBasedFallbackConfig(BaseModel):
    """Configuration for rule-based fallback when models fail."""
    
    enabled: bool = True
    
    # Response templates
    clarification_templates: List[str] = Field(
        default_factory=lambda: [
            "Could you elaborate on that?",
            "Can you provide more details?",
            "Tell me more about your approach."
        ]
    )
    
    acknowledgment_templates: List[str] = Field(
        default_factory=lambda: [
            "I see. Let's move on.",
            "Thank you for explaining that.",
            "That's helpful context."
        ]
    )
    
    followup_templates: List[str] = Field(
        default_factory=lambda: [
            "What challenges did you face with that?",
            "How did you decide on that approach?",
            "What alternatives did you consider?"
        ]
    )
    
    # Fallback actions
    default_action: str = "acknowledge_and_continue"
    use_previous_successful_question: bool = True
    skip_to_next_phase: bool = False


class CacheFallbackConfig(BaseModel):
    """Configuration for cached response fallback."""
    
    enabled: bool = True
    
    # Cache keys
    cache_by_question_similarity: bool = True
    similarity_threshold: float = 0.85
    
    # Cache strategy
    prefer_recent_cache: bool = True
    max_cache_age_seconds: int = 3600
    
    # Cache warming
    preload_common_questions: bool = True
    preload_count: int = 10
