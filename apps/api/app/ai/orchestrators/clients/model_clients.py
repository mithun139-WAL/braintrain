"""
Unified model clients for all AI providers.

Provides a simple interface for ModelOrchestrator to call any provider
without worrying about provider-specific implementation details.
"""
from typing import Optional, Dict, Any
import logging
from enum import Enum
import asyncio

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import get_settings
from app.ai.orchestrators.contracts.model_contracts import ModelProvider

logger = logging.getLogger(__name__)


class ModelClientConfig(BaseModel):
    """Configuration for a model client."""
    
    provider: ModelProvider
    api_key: str
    base_url: Optional[str] = None
    model: str
    timeout: int = 30


class UnifiedModelClient:
    """
    Unified client for all AI model providers.
    
    Uses OpenAI-compatible API for all providers (OpenAI, NIM, Groq).
    Supports local vLLM with OpenAI-compatible server.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.clients: Dict[ModelProvider, AsyncOpenAI] = {}
        self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Initialize clients for all configured providers."""
        
        # OpenAI client
        if self.settings.openai_enabled:
            self.clients[ModelProvider.OPENAI] = AsyncOpenAI(
                api_key=self.settings.openai_api_key,
                timeout=30.0
            )
            logger.info("Initialized OpenAI client")
        
        # NVIDIA NIM client (uses OpenAI-compatible API)
        if self.settings.nim_enabled:
            self.clients[ModelProvider.NIM] = AsyncOpenAI(
                api_key=self.settings.nvidia_api_key,
                base_url=self.settings.nvidia_base_url,
                timeout=30.0
            )
            logger.info(f"Initialized NVIDIA NIM client (model: {self.settings.nvidia_model})")
        
        # Groq client (uses OpenAI-compatible API)
        if self.settings.groq_enabled:
            self.clients[ModelProvider.GROQ] = AsyncOpenAI(
                api_key=self.settings.groq_api_key,
                base_url=self.settings.groq_base_url,
                timeout=30.0
            )
            logger.info("Initialized Groq client")
        
        # Local vLLM client (if configured)
        # Note: vLLM runs OpenAI-compatible server on localhost
        # Set VLLM_BASE_URL in environment to enable
        vllm_base_url = getattr(self.settings, "vllm_base_url", None)
        if vllm_base_url:
            self.clients[ModelProvider.LOCAL] = AsyncOpenAI(
                api_key="dummy",  # vLLM doesn't require real API key
                base_url=vllm_base_url,
                timeout=30.0
            )
            logger.info(f"Initialized vLLM client (base_url: {vllm_base_url})")
    
    def is_available(self, provider: ModelProvider) -> bool:
        """Check if a provider is available."""
        return provider in self.clients
    
    async def complete(
        self,
        provider: ModelProvider,
        prompt: str,
        context: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        timeout_ms: int = 5000,
        json_mode: bool = False
    ) -> str:
        """
        Generate completion from specified provider.
        
        Args:
            provider: Provider to use
            prompt: User prompt
            context: Optional system context
            model: Override default model
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            timeout_ms: Timeout in milliseconds
            json_mode: Enable JSON response format
        
        Returns:
            Generated text response
        
        Raises:
            ValueError: If provider not available
            asyncio.TimeoutError: If request times out
            Exception: On API errors
        """
        
        if provider not in self.clients:
            raise ValueError(f"Provider {provider.value} not available")
        
        client = self.clients[provider]
        
        # Get model name
        if model is None:
            model = self._get_default_model(provider)
        
        # Build messages
        messages = []
        
        if context:
            messages.append({
                "role": "system",
                "content": context
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Build request params
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Add JSON mode if requested (OpenAI specific)
        if json_mode and provider == ModelProvider.OPENAI:
            params["response_format"] = {"type": "json_object"}
        
        try:
            # Make request with timeout
            timeout_seconds = timeout_ms / 1000
            
            response = await asyncio.wait_for(
                client.chat.completions.create(**params),
                timeout=timeout_seconds
            )
            
            # Extract text
            text = response.choices[0].message.content
            
            # For NIM, extract from markdown fences if present
            if provider == ModelProvider.NIM and json_mode:
                text = self._extract_json_from_markdown(text)
            
            return text or ""
        
        except asyncio.TimeoutError:
            logger.error(f"Request timeout: provider={provider.value} timeout={timeout_ms}ms")
            raise
        
        except Exception as e:
            logger.error(
                f"API request failed: provider={provider.value} "
                f"model={model} error={str(e)}"
            )
            raise
    
    async def complete_streaming(
        self,
        provider: ModelProvider,
        prompt: str,
        context: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7
    ):
        """
        Generate streaming completion.
        
        Yields text chunks as they arrive.
        """
        
        if provider not in self.clients:
            raise ValueError(f"Provider {provider.value} not available")
        
        client = self.clients[provider]
        
        # Get model name
        if model is None:
            model = self._get_default_model(provider)
        
        # Build messages
        messages = []
        
        if context:
            messages.append({
                "role": "system",
                "content": context
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.error(
                f"Streaming request failed: provider={provider.value} "
                f"model={model} error={str(e)}"
            )
            raise
    
    def _get_default_model(self, provider: ModelProvider) -> str:
        """Get default model for provider."""
        
        defaults = {
            ModelProvider.OPENAI: "gpt-4o-mini",
            ModelProvider.NIM: self.settings.nvidia_model,
            ModelProvider.GROQ: "llama-3.1-8b-instant",
            ModelProvider.LOCAL: "meta-llama/Llama-2-7b-chat-hf"
        }
        
        return defaults.get(provider, "gpt-4o-mini")
    
    def _extract_json_from_markdown(self, text: str) -> str:
        """
        Extract JSON from markdown code fences.
        
        NVIDIA NIM sometimes wraps JSON in ```json ... ``` fences.
        """
        
        import re
        
        # Try to find JSON in markdown fences
        pattern = r'```(?:json)?\s*(.*?)\s*```'
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return text
    
    async def health_check(self, provider: ModelProvider) -> bool:
        """
        Check if provider is healthy.
        
        Makes a minimal request to verify connectivity.
        """
        
        try:
            response = await self.complete(
                provider=provider,
                prompt="Hello",
                max_tokens=5,
                temperature=0,
                timeout_ms=5000
            )
            return len(response) > 0
        
        except Exception as e:
            logger.warning(f"Health check failed: provider={provider.value} error={str(e)}")
            return False
    
    async def warmup(self, providers: Optional[list[ModelProvider]] = None) -> Dict[ModelProvider, bool]:
        """
        Warm up model connections.
        
        Args:
            providers: List of providers to warm up (all if None)
        
        Returns:
            Dict of provider -> success status
        """
        
        if providers is None:
            providers = list(self.clients.keys())
        
        results = {}
        
        for provider in providers:
            if provider in self.clients:
                logger.info(f"Warming up {provider.value}...")
                results[provider] = await self.health_check(provider)
        
        return results
    
    def get_available_providers(self) -> list[ModelProvider]:
        """Get list of available providers."""
        return list(self.clients.keys())


# Singleton instance
_client: Optional[UnifiedModelClient] = None


def get_model_client() -> UnifiedModelClient:
    """Get singleton model client instance."""
    global _client
    
    if _client is None:
        _client = UnifiedModelClient()
    
    return _client


async def test_providers() -> None:
    """Test all configured providers."""
    
    client = get_model_client()
    
    print("\n=== Testing AI Providers ===\n")
    
    for provider in client.get_available_providers():
        print(f"Testing {provider.value}...")
        
        try:
            response = await client.complete(
                provider=provider,
                prompt="Say 'Hello from provider' in 5 words or less",
                max_tokens=20,
                temperature=0,
                timeout_ms=10000
            )
            
            print(f"✓ {provider.value}: {response[:50]}")
        
        except Exception as e:
            print(f"✗ {provider.value}: {str(e)}")
    
    print("\n=== Provider Test Complete ===\n")


if __name__ == "__main__":
    # Test all providers
    import asyncio
    asyncio.run(test_providers())
