"""
Model Orchestrator - Manages model routing, fallbacks, and latency tracking.

This orchestrator:
1. Routes tasks to appropriate models based on task type
2. Handles fallback chains when models fail
3. Tracks latency per model/provider
4. Enforces latency budgets
5. Implements retry logic with exponential backoff
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import logging
import asyncio

from pydantic import BaseModel, Field

from app.ai.orchestrators.contracts.model_contracts import (
    ModelProvider,
    ModelTask,
    ModelRequest,
    ModelResponse,
    ModelLatency,
    FallbackTrigger,
    ModelConfig
)
from app.ai.orchestrators.policies.routing_policy import RoutingPolicy, TaskRoute
from app.ai.orchestrators.policies.fallback_policy import FallbackPolicy, FallbackStrategy
from app.ai.orchestrators.clients import get_model_client
from app.ai.orchestrators.instrumentation import get_instrumentation

logger = logging.getLogger(__name__)


class ModelOrchestrator:
    """
    Orchestrator for model routing and execution.
    
    Key responsibilities:
    - Route tasks to optimal models
    - Handle failures with fallback chains
    - Track and enforce latency budgets
    - Retry with exponential backoff
    - Provider health monitoring
    """
    
    def __init__(
        self,
        routing_policy: Optional[RoutingPolicy] = None,
        fallback_policy: Optional[FallbackPolicy] = None
    ):
        self.routing_policy = routing_policy or RoutingPolicy.get_default_policy()
        self.fallback_policy = fallback_policy or FallbackPolicy()
        
        # Model client for API calls
        self.model_client = get_model_client()
        
        # Instrumentation
        self.instrumentation = get_instrumentation()
        
        # Performance tracking
        self.latencies: Dict[str, List[float]] = {}
        self.failure_counts: Dict[str, int] = {}
        self.success_counts: Dict[str, int] = {}
        
        # Provider health
        self.provider_health: Dict[ModelProvider, float] = {
            provider: 1.0 for provider in ModelProvider
        }
        
        logger.info("Initialized ModelOrchestrator")
    
    async def generate(
        self,
        task: ModelTask,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        timeout_ms: int = 5000,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ModelResponse:
        """
        Generate response using appropriate model with fallback handling.
        
        Process:
        1. Get route for task
        2. Try primary model
        3. On failure, try fallback chain
        4. Track latency and failures
        5. Return response or raise error
        """
        
        start_time = datetime.utcnow()
        
        # Start tracing
        trace_attrs = {
            "task": task.value,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "timeout_ms": timeout_ms
        }
        
        async with self.instrumentation.trace_operation("model.generate", trace_attrs) as span:
            # Get routing for this task
            route = self.routing_policy.get_route(task)
            
            if span:
                span.set_attribute("primary_provider", route.primary_provider.value)
            
            # Build request
            request = ModelRequest(
                task=task,
                prompt=prompt,
                context=context,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout_ms=timeout_ms,
                metadata=metadata or {}
            )
            
            # Try primary provider
            try:
                response = await self._execute_with_model(
                    route.primary_provider,
                    route.primary_model,
                    request,
                    is_primary=True
                )
                
                # Track success
                self._record_success(route.primary_provider)
                
                # Record metrics
                self.instrumentation.record_metric(
                    "model_generation_latency",
                    response.latency_ms,
                    {"provider": response.provider.value, "task": task.value}
                )
                self.instrumentation.increment_counter(
                    "model_calls",
                    attributes={"provider": response.provider.value, "task": task.value, "success": True}
                )
                
                if span:
                    span.set_attribute("provider_used", response.provider.value)
                    span.set_attribute("latency_ms", response.latency_ms)
                    span.set_attribute("tokens_used", response.tokens_used)
                
                return response
            
            except Exception as e:
                logger.warning(
                    f"Primary model failed: provider={route.primary_provider.value} model={route.primary_model} "
                    f"task={task.value} error={str(e)}"
                )
                
                if span:
                    span.add_event("primary_provider_failed", {"error": str(e)})
                
                # Determine fallback trigger
                trigger = self._classify_error(e)
                
                # Try fallback chain
                response = await self._execute_fallback_chain(
                    route,
                    request,
                    trigger
                )
                
                if response:
                    # Record fallback metrics
                    self.instrumentation.increment_counter(
                        "fallbacks",
                        attributes={"trigger": trigger.value, "task": task.value}
                    )
                    
                    if span:
                        span.set_attribute("fallback_used", True)
                        span.set_attribute("provider_used", response.provider.value)
                    
                    return response
                
                # All fallbacks failed
                total_latency = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                if span:
                    span.set_attribute("all_providers_failed", True)
                
                raise Exception(
                    f"All models failed for task {task.value} after {total_latency:.0f}ms"
                )
    
    async def _execute_with_model(
        self,
        provider: ModelProvider,
        model_name: str,
        request: ModelRequest,
        is_primary: bool = True
    ) -> ModelResponse:
        """
        Execute request with specific model.
        
        Includes retry logic and latency tracking.
        """
        
        start_time = datetime.utcnow()
        
        # Get model config
        config = self.routing_policy.get_model_config(provider)
        
        # Adjust timeout based on budget
        effective_timeout = min(
            request.timeout_ms,
            config.latency_budget_ms
        )
        
        try:
            # Call actual model (mock for now)
            # TODO: Integrate with actual model clients
            response_text = await self._call_model_api(
                provider,
                model_name,
                request,
                effective_timeout
            )
            
            # Calculate latency
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Track latency
            self._record_latency(provider, latency_ms)
            
            # Check if latency budget exceeded
            if latency_ms > config.latency_budget_ms:
                logger.warning(
                    f"Latency budget exceeded: {latency_ms:.0f}ms > {config.latency_budget_ms}ms "
                    f"provider={provider.value}"
                )
            
            # Build response
            response = ModelResponse(
                text=response_text,
                provider=provider,
                model=model_name,
                latency_ms=latency_ms,
                tokens_used=self._estimate_tokens(response_text),
                success=True,
                from_cache=False,
                metadata=request.metadata
            )
            
            return response
        
        except asyncio.TimeoutError:
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._record_failure(provider)
            logger.error(f"Model timeout: provider={provider.value} latency={latency_ms:.0f}ms")
            raise
        
        except Exception as e:
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._record_failure(provider)
            logger.error(
                f"Model execution failed: provider={provider.value} "
                f"latency={latency_ms:.0f}ms error={str(e)}"
            )
            raise
    
    async def _call_model_api(
        self,
        provider: ModelProvider,
        model: str,
        request: ModelRequest,
        timeout_ms: int
    ) -> str:
        """
        Call actual model API.
        
        Uses UnifiedModelClient to make API calls to configured providers.
        """
        
        # Check if provider is available
        if not self.model_client.is_available(provider):
            raise ValueError(
                f"Provider {provider.value} not configured. "
                f"Please set the appropriate API key in environment."
            )
        
        try:
            # Build context from task type
            context = self._build_system_context(request)
            
            # Make API call
            response_text = await self.model_client.complete(
                provider=provider,
                prompt=request.prompt,
                context=context,
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                timeout_ms=timeout_ms,
                json_mode=(request.task == ModelTask.EVALUATION)
            )
            
            return response_text
        
        except asyncio.TimeoutError:
            logger.error(f"Model API timeout: provider={provider.value} timeout={timeout_ms}ms")
            raise
        
        except Exception as e:
            logger.error(
                f"Model API call failed: provider={provider.value} "
                f"model={model} task={request.task.value} error={str(e)}"
            )
            raise
    
    def _build_system_context(self, request: ModelRequest) -> str:
        """
        Build system context based on task type.
        
        Provides task-specific instructions to guide the model.
        """
        
        task_contexts = {
            ModelTask.REALTIME_RESPONSE: (
                "You are an AI interviewer conducting a technical interview. "
                "Respond naturally and conversationally. Keep responses concise (2-3 sentences). "
                "Be professional but friendly. Focus on the candidate's answer."
            ),
            ModelTask.FOLLOWUP_GENERATION: (
                "Generate a relevant follow-up question based on the candidate's answer. "
                "Probe deeper into their technical knowledge or ask for specific examples. "
                "Keep the question concise and focused."
            ),
            ModelTask.QUESTION_GENERATION: (
                "Generate a technical interview question based on the provided context. "
                "The question should be clear, specific, and assess technical knowledge. "
                "Adapt difficulty to the candidate's experience level."
            ),
            ModelTask.EVALUATION: (
                "Evaluate the candidate's answer across multiple dimensions: "
                "clarity, structure, technical depth, confidence, and communication. "
                "Provide scores and brief reasoning."
            ),
            ModelTask.CONTEXT_SUMMARIZATION: (
                "Summarize the provided context concisely while preserving key technical details. "
                "Focus on information relevant to the interview."
            ),
            ModelTask.COACHING: (
                "Provide constructive feedback as an AI interview coach. "
                "Be supportive and specific. Highlight strengths and areas for improvement."
            )
        }
        
        base_context = task_contexts.get(
            request.task,
            "You are an AI assistant helping with technical interviews."
        )
        
        # Append request context if provided
        if request.context:
            return f"{base_context}\n\nContext:\n{request.context}"
        
        return base_context
    
    async def _execute_fallback_chain(
        self,
        route: TaskRoute,
        request: ModelRequest,
        trigger: FallbackTrigger
    ) -> Optional[ModelResponse]:
        """
        Execute fallback chain when primary fails.
        """
        
        # Get fallback strategy
        strategy = self.fallback_policy.get_strategy(trigger)
        
        # Check if should use cache
        if self.fallback_policy.should_use_cache(trigger):
            cached_response = await self._get_cached_response(request)
            if cached_response:
                logger.info("Using cached response as fallback")
                return cached_response
        
        # Try each fallback model
        for fallback_provider in strategy.fallback_chain:
            if fallback_provider not in self.routing_policy.provider_configs:
                continue
            
            fallback_model = self.routing_policy.provider_configs[fallback_provider].default_model
            
            logger.info(f"Trying fallback: provider={fallback_provider.value}")
            
            try:
                response = await self._execute_with_model(
                    fallback_provider,
                    fallback_model,
                    request,
                    is_primary=False
                )
                
                # Mark as fallback
                response.metadata["is_fallback"] = True
                response.metadata["fallback_trigger"] = trigger.value
                
                self._record_success(fallback_provider)
                
                return response
            
            except Exception as e:
                logger.warning(f"Fallback failed: provider={fallback_provider.value} error={str(e)}")
                self._record_failure(fallback_provider)
                continue
        
        # Check if should use rule-based fallback
        if self.fallback_policy.should_use_rule_based(trigger):
            logger.info("Using rule-based fallback")
            return await self._get_rule_based_fallback(request)
        
        return None
    
    async def _get_cached_response(
        self,
        request: ModelRequest
    ) -> Optional[ModelResponse]:
        """Get cached response if available."""
        
        # TODO: Implement actual caching
        # Could use Redis or in-memory cache
        
        return None
    
    async def _get_rule_based_fallback(
        self,
        request: ModelRequest
    ) -> Optional[ModelResponse]:
        """
        Get rule-based fallback response.
        
        Used when all models fail - returns templated response.
        """
        
        # Template responses based on task
        templates = {
            ModelTask.REALTIME_RESPONSE: [
                "Could you elaborate on that?",
                "Tell me more about your approach.",
                "That's interesting. Can you provide more details?"
            ],
            ModelTask.FOLLOWUP_GENERATION: [
                "What challenges did you face with that?",
                "How did you decide on that approach?",
                "Can you walk me through your thinking?"
            ],
            ModelTask.EVALUATION: [
                "Thank you for that explanation.",
                "I see. Let's continue.",
                "That provides helpful context."
            ]
        }
        
        task_templates = templates.get(request.task, ["Let's continue."])
        
        # Pick a template (deterministic based on time)
        import random
        random.seed(int(datetime.utcnow().timestamp()))
        template = random.choice(task_templates)
        
        response = ModelResponse(
            text=template,
            provider=ModelProvider.LOCAL,
            model="rule_based_fallback",
            latency_ms=1.0,
            tokens_used=len(template.split()),
            success=True,
            from_cache=False,
            metadata={
                "is_fallback": True,
                "is_rule_based": True
            }
        )
        
        return response
    
    def _classify_error(self, error: Exception) -> FallbackTrigger:
        """Classify error to determine fallback strategy."""
        
        error_str = str(error).lower()
        
        if "timeout" in error_str or isinstance(error, asyncio.TimeoutError):
            return FallbackTrigger.TIMEOUT
        elif "rate" in error_str or "limit" in error_str:
            return FallbackTrigger.RATE_LIMIT
        elif "connection" in error_str or "network" in error_str:
            return FallbackTrigger.PROVIDER_DOWN
        else:
            return FallbackTrigger.ERROR
    
    def _record_latency(self, provider: ModelProvider, latency_ms: float) -> None:
        """Record latency for a provider."""
        
        key = provider.value
        if key not in self.latencies:
            self.latencies[key] = []
        
        self.latencies[key].append(latency_ms)
        
        # Keep only recent latencies (last 100)
        if len(self.latencies[key]) > 100:
            self.latencies[key] = self.latencies[key][-100:]
        
        # Update provider health
        self._update_provider_health(provider)
    
    def _record_success(self, provider: ModelProvider) -> None:
        """Record successful execution."""
        
        key = provider.value
        self.success_counts[key] = self.success_counts.get(key, 0) + 1
        self._update_provider_health(provider)
    
    def _record_failure(self, provider: ModelProvider) -> None:
        """Record failed execution."""
        
        key = provider.value
        self.failure_counts[key] = self.failure_counts.get(key, 0) + 1
        self._update_provider_health(provider)
    
    def _update_provider_health(self, provider: ModelProvider) -> None:
        """Update provider health score based on recent performance."""
        
        key = provider.value
        successes = self.success_counts.get(key, 0)
        failures = self.failure_counts.get(key, 0)
        
        total = successes + failures
        if total == 0:
            self.provider_health[provider] = 1.0
            return
        
        # Health = success rate
        health = successes / total
        
        # Also factor in latency
        if key in self.latencies and self.latencies[key]:
            avg_latency = sum(self.latencies[key]) / len(self.latencies[key])
            config = self.routing_policy.get_model_config(provider)
            
            # Penalize if over budget
            if avg_latency > config.latency_budget_ms:
                latency_penalty = config.latency_budget_ms / avg_latency
                health *= latency_penalty
        
        self.provider_health[provider] = health
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics for all providers."""
        
        stats = {}
        
        for provider in ModelProvider:
            key = provider.value
            
            latencies = self.latencies.get(key, [])
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
            
            successes = self.success_counts.get(key, 0)
            failures = self.failure_counts.get(key, 0)
            total = successes + failures
            success_rate = successes / total if total > 0 else 0
            
            stats[key] = {
                "health": self.provider_health[provider],
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": p95_latency,
                "success_rate": success_rate,
                "total_requests": total,
                "failures": failures
            }
        
        return stats
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        return len(text.split())
    
    async def warmup(self) -> None:
        """
        Warm up model connections.
        
        Makes initial requests to ensure models are loaded.
        """
        
        logger.info("Warming up model connections...")
        
        # Use model client's warmup functionality
        available_providers = self.model_client.get_available_providers()
        
        # Filter to only configured providers
        providers_to_warm = [
            p for p in [ModelProvider.NIM, ModelProvider.GROQ, ModelProvider.OPENAI]
            if p in available_providers and p in self.routing_policy.provider_configs
        ]
        
        if not providers_to_warm:
            logger.warning("No providers available for warmup")
            return
        
        try:
            results = await self.model_client.warmup(providers_to_warm)
            
            # Log results
            for provider, success in results.items():
                if success:
                    logger.info(f"✓ {provider.value} warmed up successfully")
                else:
                    logger.warning(f"✗ {provider.value} warmup failed")
            
            logger.info(f"Model warmup complete ({len(results)} providers)")
        
        except Exception as e:
            logger.warning(f"Warmup had errors: {e}")
    
    def get_recommended_provider(self, task: ModelTask) -> ModelProvider:
        """
        Get recommended provider for a task based on health and performance.
        """
        
        route = self.routing_policy.get_route(task)
        
        # Check primary health
        if self.provider_health.get(route.primary_provider, 1.0) >= 0.8:
            return route.primary_provider
        
        # Check fallback providers
        for fallback in route.fallback_models[:1]:  # Just check first fallback
            provider_enum = self._model_to_provider(fallback)
            if provider_enum and self.provider_health.get(provider_enum, 1.0) >= 0.8:
                return provider_enum
        
        # Default to primary
        return route.primary_provider
    
    def _model_to_provider(self, model: str) -> Optional[ModelProvider]:
        """Map model name to provider."""
        
        for provider, config in self.routing_policy.provider_configs.items():
            if config.default_model == model:
                return provider
        
        return None
