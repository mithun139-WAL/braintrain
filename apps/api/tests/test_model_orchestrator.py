#!/usr/bin/env python3
"""
Test script for ModelOrchestrator with actual API clients.

Run this script to verify that the ModelOrchestrator can successfully
make calls to configured providers (OpenAI, NIM, Groq).

Usage:
    python test_model_orchestrator.py
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.ai.orchestrators import ModelOrchestrator
from app.ai.orchestrators.contracts.model_contracts import ModelTask
from app.ai.orchestrators.clients import get_model_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_basic_generation():
    """Test basic text generation across providers."""
    
    print("\n" + "="*60)
    print("TEST 1: Basic Generation")
    print("="*60 + "\n")
    
    orchestrator = ModelOrchestrator()
    
    # Test prompt
    prompt = "Explain what a Python decorator is in one sentence."
    
    try:
        response = await orchestrator.generate(
            task=ModelTask.REALTIME_RESPONSE,
            prompt=prompt,
            max_tokens=100,
            temperature=0.7,
            timeout_ms=10000
        )
        
        print(f"✓ Provider: {response.provider.value}")
        print(f"✓ Model: {response.model}")
        print(f"✓ Latency: {response.latency_ms:.0f}ms")
        print(f"✓ Tokens: {response.tokens_used}")
        print(f"✓ Response: {response.text[:200]}")
        
        return True
    
    except Exception as e:
        print(f"✗ Generation failed: {e}")
        return False


async def test_evaluation_task():
    """Test evaluation task with JSON response."""
    
    print("\n" + "="*60)
    print("TEST 2: Evaluation Task")
    print("="*60 + "\n")
    
    orchestrator = ModelOrchestrator()
    
    prompt = """Evaluate this interview answer on a scale of 0-100.

**Question:** What is dependency injection?

**Answer:** Dependency injection is a design pattern where you pass dependencies into a class rather than creating them inside the class. This makes the code more testable and flexible.

Provide scores for:
1. Technical Accuracy (0-100)
2. Depth (0-100)
3. Problem-Solving (0-100)

Respond in JSON format:
{
    "technical_accuracy": <score>,
    "depth": <score>,
    "problem_solving": <score>,
    "reasoning": "<brief explanation>"
}
"""
    
    try:
        response = await orchestrator.generate(
            task=ModelTask.EVALUATION,
            prompt=prompt,
            max_tokens=200,
            temperature=0.1,
            timeout_ms=10000
        )
        
        print(f"✓ Provider: {response.provider.value}")
        print(f"✓ Model: {response.model}")
        print(f"✓ Latency: {response.latency_ms:.0f}ms")
        print(f"✓ Response: {response.text}")
        
        # Try to parse JSON
        import json
        try:
            result = json.loads(response.text)
            print(f"✓ JSON parsing successful")
            print(f"  - Technical Accuracy: {result.get('technical_accuracy')}")
            print(f"  - Depth: {result.get('depth')}")
            print(f"  - Problem Solving: {result.get('problem_solving')}")
        except json.JSONDecodeError:
            print(f"⚠ Response is not valid JSON (may need fence extraction)")
        
        return True
    
    except Exception as e:
        print(f"✗ Evaluation failed: {e}")
        return False


async def test_fallback_behavior():
    """Test fallback chain when primary provider times out."""
    
    print("\n" + "="*60)
    print("TEST 3: Fallback Behavior")
    print("="*60 + "\n")
    
    orchestrator = ModelOrchestrator()
    
    # Use very short timeout to trigger fallback
    try:
        response = await orchestrator.generate(
            task=ModelTask.REALTIME_RESPONSE,
            prompt="Hello, world!",
            max_tokens=50,
            temperature=0.7,
            timeout_ms=10  # Very short timeout
        )
        
        is_fallback = response.metadata.get("is_fallback", False)
        
        if is_fallback:
            print(f"✓ Fallback triggered successfully")
            print(f"✓ Fallback provider: {response.provider.value}")
            print(f"✓ Response: {response.text[:100]}")
        else:
            print(f"✓ Primary provider was fast enough")
            print(f"✓ Provider: {response.provider.value}")
        
        return True
    
    except Exception as e:
        print(f"⚠ All providers failed (expected if timeout too short): {e}")
        return False


async def test_provider_stats():
    """Test provider statistics tracking."""
    
    print("\n" + "="*60)
    print("TEST 4: Provider Statistics")
    print("="*60 + "\n")
    
    orchestrator = ModelOrchestrator()
    
    # Make a few requests
    for i in range(3):
        try:
            await orchestrator.generate(
                task=ModelTask.REALTIME_RESPONSE,
                prompt=f"Test request {i+1}",
                max_tokens=20,
                temperature=0.7,
                timeout_ms=10000
            )
        except:
            pass
    
    # Get stats
    stats = orchestrator.get_provider_stats()
    
    print("Provider Statistics:")
    for provider, provider_stats in stats.items():
        print(f"\n  {provider}:")
        print(f"    - Health: {provider_stats['health']:.2f}")
        print(f"    - Avg Latency: {provider_stats['avg_latency_ms']:.0f}ms")
        print(f"    - P95 Latency: {provider_stats['p95_latency_ms']:.0f}ms")
        print(f"    - Success Rate: {provider_stats['success_rate']:.2%}")
        print(f"    - Total Requests: {provider_stats['total_requests']}")
        print(f"    - Failures: {provider_stats['failures']}")
    
    return True


async def test_model_client_directly():
    """Test UnifiedModelClient directly."""
    
    print("\n" + "="*60)
    print("TEST 5: Direct Model Client Test")
    print("="*60 + "\n")
    
    client = get_model_client()
    
    print(f"Available providers: {[p.value for p in client.get_available_providers()]}")
    
    # Test each available provider
    for provider in client.get_available_providers():
        print(f"\nTesting {provider.value}...")
        
        try:
            response = await client.complete(
                provider=provider,
                prompt="Say 'Hello' in exactly 3 words",
                max_tokens=20,
                temperature=0,
                timeout_ms=10000
            )
            
            print(f"✓ {provider.value}: {response}")
        
        except Exception as e:
            print(f"✗ {provider.value}: {e}")
    
    return True


async def test_warmup():
    """Test model warmup."""
    
    print("\n" + "="*60)
    print("TEST 6: Model Warmup")
    print("="*60 + "\n")
    
    orchestrator = ModelOrchestrator()
    
    print("Warming up models...")
    await orchestrator.warmup()
    
    print("✓ Warmup complete")
    
    return True


async def main():
    """Run all tests."""
    
    print("\n" + "="*60)
    print("ORCHESTRATOR MODEL CLIENT INTEGRATION TESTS")
    print("="*60)
    
    tests = [
        ("Basic Generation", test_basic_generation),
        ("Evaluation Task", test_evaluation_task),
        ("Fallback Behavior", test_fallback_behavior),
        ("Provider Statistics", test_provider_stats),
        ("Direct Model Client", test_model_client_directly),
        ("Model Warmup", test_warmup),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.exception(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
        
        # Small delay between tests
        await asyncio.sleep(0.5)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
