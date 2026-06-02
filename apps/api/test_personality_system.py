import asyncio
import os
from app.ai.voice.simulation.personality_profiles import PersonalityProfile
from app.ai.voice.simulation.personality_loader import PersonalityLoader
from app.ai.voice.simulation.personality_registry import PersonalityRegistry
from app.ai.voice.simulation.personality_engine import PersonalityEngine

async def run_tests():
    print("=== Running Dynamic Personality Simulation Tests ===")

    # Test 1: Simple YAML parsing fallback
    print("\n[Test 1] Testing simple YAML parsing fallback...")
    yaml_mock = """
name: "Mock Interviewer"
archetype: "Coder"
characteristics:
  pacing_speed: 1.2
  interruption_frequency: 0.6
  silence_tolerance: 0.9
  skepticism_level: 0.7
  technical_depth: 0.8
  followup_aggressiveness: 0.5
  verbosity_tolerance: 0.4
  ambiguity_tolerance: 0.5
  pressure_intensity: 0.6
  conversational_warmth: 0.4
  challenge_escalation: "CodeProbing"
acknowledgment_patterns:
  - "Ok, let's write code."
  - "Hmm, what about time complexity?"
"""
    parsed = PersonalityLoader._parse_simple_yaml(yaml_mock)
    profile = PersonalityLoader.load_from_dict(parsed)
    
    assert profile.name == "Mock Interviewer"
    assert profile.pacing_speed == 1.2
    assert profile.silence_tolerance == 0.9
    assert len(profile.acknowledgment_patterns) == 2
    print("✓ Simple YAML parsing passed.")

    # Test 2: Registry loading
    print("\n[Test 2] Testing PersonalityRegistry...")
    registry = PersonalityRegistry(personas_dir="personas")
    
    google_prof = await registry.get_profile("google_system_design")
    assert google_prof.name == "Google System Design Interviewer"
    assert google_prof.skepticism_level == 0.9
    
    hr_prof = await registry.get_profile("friendly_hr")
    assert hr_prof.name == "Friendly HR Interviewer"
    assert hr_prof.conversational_warmth == 0.9
    print("✓ PersonalityRegistry loaded yaml profiles successfully.")

    # Test 3: Engine dynamics and dynamic adaptation
    print("\n[Test 3] Testing PersonalityEngine dynamics...")
    engine = PersonalityEngine(personas_dir="personas")
    await engine.select_persona("google_system_design")
    
    # Simulate a strong/evasive user answer turn (causing drift and verbosity)
    adapted_params, prompt_directive = engine.process_user_turn(topic_drift=75.0, hesitation=10.0, verbosity=80.0)
    print(f"Adapted silence tolerance: {adapted_params['silence_tolerance']:.2f}")
    print(f"Target drill depth: {adapted_params['target_drill_depth']}")
    print(f"Generated prompt directive:\n  {prompt_directive}")
    
    # Google system designer has base silence_tolerance = 1.2s. 
    # Evasiveness (drift=75) drops patience, which reduces silence tolerance further.
    assert adapted_params["silence_tolerance"] < 1.2, "Expected silence tolerance to adapt down under evasiveness"
    assert "skepticism" in prompt_directive.lower() or "challenge" in prompt_directive.lower(), "Expected skepticism prompts"
    
    # Test 4: Realism injection
    print("\n[Test 4] Testing RealismEngine speech formatting...")
    speech = "Let's build a replication queue."
    formatted = speech
    for _ in range(20):
        formatted = engine.format_interviewer_speech(speech)
        if formatted != speech:
            break
    print(f"Original Speech: '{speech}'")
    print(f"Formatted Speech: '{formatted}'")
    
    # Since skepticism is high, it should have pre-pended an acknowledgment pattern from Google persona
    assert formatted != speech, "Expected filler or acknowledgment pattern injection"
    
    delay = engine.get_thinking_delay()
    print(f"Thinking delay: {delay:.2f}s")
    assert 0.2 <= delay <= 2.0, "Expected delay to fall in standard human threshold range"
    
    print("\n=== All Personality Simulation Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
