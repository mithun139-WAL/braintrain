"""
Routing policy for model selection and task routing.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.ai.orchestrators.contracts.model_contracts import (
    ModelTask,
    ModelProvider,
    ModelSelection,
    ModelCapability
)


class TaskRoutingConfig(BaseModel):
    """Configuration for routing a specific task type."""
    
    task: ModelTask
    
    # Primary model
    primary_provider: ModelProvider
    primary_model: str
    
    # Fallback models (in order)
    fallback_providers: List[ModelProvider] = Field(default_factory=list)
    fallback_models: List[str] = Field(default_factory=list)
    
    # Parameters
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout_seconds: int = 10
    
    # Requirements
    required_capabilities: List[ModelCapability] = Field(default_factory=list)


class ProviderConfig(BaseModel):
    """Configuration for a specific model provider."""
    provider: ModelProvider
    default_model: str
    latency_budget_ms: int = 5000


# Alias for backward compatibility
TaskRoute = TaskRoutingConfig


class RoutingPolicy(BaseModel):
    """Policy for routing tasks to appropriate models."""
    
    policy_name: str = "default"
    policy_version: str = "1.0"
    
    # Provider-specific configurations
    provider_configs: Dict[ModelProvider, ProviderConfig] = Field(default_factory=dict)
    
    # Task-specific routing
    task_routes: Dict[str, TaskRoutingConfig] = Field(default_factory=dict)
    
    # Global preferences
    prioritize_latency_over_cost: bool = True
    prioritize_quality_over_cost: bool = True
    
    # Thresholds
    max_acceptable_latency_ms: int = 3000
    max_acceptable_cost_per_request: float = 0.10
    min_quality_score: float = 0.7
    
    # Fallback strategy
    max_fallback_attempts: int = 2
    fallback_on_timeout: bool = True
    fallback_on_error: bool = True
    fallback_on_quality: bool = False
    
    @classmethod
    def get_default_policy(cls) -> "RoutingPolicy":
        """Get default routing policy optimized for realtime interviews."""
        
        return cls(
            policy_name="interview_default",
            provider_configs={
                ModelProvider.NIM: ProviderConfig(provider=ModelProvider.NIM, default_model="llama-3.1-8b-instruct", latency_budget_ms=3000),
                ModelProvider.GROQ: ProviderConfig(provider=ModelProvider.GROQ, default_model="llama-3.1-8b-instant", latency_budget_ms=3000),
                ModelProvider.OPENAI: ProviderConfig(provider=ModelProvider.OPENAI, default_model="gpt-4o-mini", latency_budget_ms=5000),
                ModelProvider.LOCAL: ProviderConfig(provider=ModelProvider.LOCAL, default_model="local-model", latency_budget_ms=5000),
                ModelProvider.STUB: ProviderConfig(provider=ModelProvider.STUB, default_model="stub-model", latency_budget_ms=1000),
            },
            task_routes={
                # Realtime tasks - prioritize speed
                ModelTask.REALTIME_RESPONSE.value: TaskRoutingConfig(
                    task=ModelTask.REALTIME_RESPONSE,
                    primary_provider=ModelProvider.NIM,
                    primary_model="llama-3.1-8b-instruct",
                    fallback_providers=[ModelProvider.GROQ, ModelProvider.OPENAI],
                    fallback_models=["llama-3.1-8b-instant", "gpt-4o-mini"],
                    temperature=0.7,
                    max_tokens=500,
                    timeout_seconds=3,
                    required_capabilities=[ModelCapability.REALTIME]
                ),
                
                # Follow-up generation - balance speed and quality
                ModelTask.FOLLOWUP_GENERATION.value: TaskRoutingConfig(
                    task=ModelTask.FOLLOWUP_GENERATION,
                    primary_provider=ModelProvider.NIM,
                    primary_model="llama-3.1-70b-instruct",
                    fallback_providers=[ModelProvider.OPENAI],
                    fallback_models=["gpt-4o-mini"],
                    temperature=0.7,
                    max_tokens=300,
                    timeout_seconds=5
                ),
                
                # Evaluation - prioritize quality
                ModelTask.EVALUATION.value: TaskRoutingConfig(
                    task=ModelTask.EVALUATION,
                    primary_provider=ModelProvider.OPENAI,
                    primary_model="gpt-4o-mini",
                    fallback_providers=[ModelProvider.NIM],
                    fallback_models=["llama-3.1-70b-instruct"],
                    temperature=0.3,
                    max_tokens=1000,
                    timeout_seconds=10,
                    required_capabilities=[ModelCapability.JSON_MODE]
                ),
                
                # Summarization - cost-effective
                ModelTask.SUMMARIZATION.value: TaskRoutingConfig(
                    task=ModelTask.SUMMARIZATION,
                    primary_provider=ModelProvider.OPENAI,
                    primary_model="gpt-4o-mini",
                    fallback_providers=[ModelProvider.NIM],
                    fallback_models=["llama-3.1-8b-instruct"],
                    temperature=0.5,
                    max_tokens=500,
                    timeout_seconds=8
                ),
                
                # Memory extraction - accurate
                ModelTask.MEMORY_EXTRACTION.value: TaskRoutingConfig(
                    task=ModelTask.MEMORY_EXTRACTION,
                    primary_provider=ModelProvider.OPENAI,
                    primary_model="gpt-4o-mini",
                    fallback_providers=[ModelProvider.NIM],
                    fallback_models=["llama-3.1-70b-instruct"],
                    temperature=0.2,
                    max_tokens=800,
                    timeout_seconds=10
                ),
                
                # Answer classification - fast and accurate
                ModelTask.ANSWER_CLASSIFICATION.value: TaskRoutingConfig(
                    task=ModelTask.ANSWER_CLASSIFICATION,
                    primary_provider=ModelProvider.NIM,
                    primary_model="llama-3.1-8b-instruct",
                    fallback_providers=[ModelProvider.OPENAI],
                    fallback_models=["gpt-4o-mini"],
                    temperature=0.1,
                    max_tokens=100,
                    timeout_seconds=2,
                    required_capabilities=[ModelCapability.JSON_MODE]
                )
            }
        )
    
    def get_route_for_task(self, task: ModelTask) -> Optional[TaskRoutingConfig]:
        """Get routing configuration for a task."""
        return self.task_routes.get(task.value)
    
    def get_route(self, task: ModelTask) -> Optional[TaskRoutingConfig]:
        """Alias for get_route_for_task for backward compatibility."""
        return self.get_route_for_task(task)
        
    def get_model_config(self, provider: ModelProvider) -> ProviderConfig:
        """Get model config for a provider."""
        return self.provider_configs.get(
            provider, 
            ProviderConfig(provider=provider, default_model="unknown", latency_budget_ms=5000)
        )
    
    def should_fallback(self, latency_ms: Optional[int] = None, error: Optional[str] = None) -> bool:
        """Determine if fallback should be triggered."""
        if error and self.fallback_on_error:
            return True
        
        if latency_ms and latency_ms > self.max_acceptable_latency_ms and self.fallback_on_timeout:
            return True
        
        return False
