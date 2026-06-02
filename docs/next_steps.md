# NEXT STEPS: Getting the Intelligence Layer Running

## Immediate Actions Required

### 1. Create Database Migration

```bash
cd apps/api
python -m alembic revision --autogenerate -m "Add knowledge base tables"
python -m alembic upgrade head
```

This will create the new tables:
- `knowledge_documents`
- `knowledge_chunks`  
- `knowledge_tags`

### 2. Verify New Models Are Importable

```bash
cd apps/api
python -c "from app.db.models import KnowledgeDocument, KnowledgeChunk, KnowledgeTag; print('✓ Models imported successfully')"
```

### 3. Test Rules Engine

Create a test file to verify the rules engine works:

```python
# apps/api/test_intelligence.py

from app.ai.intelligence.rules.hallucination_rules import HallucinationRuleEngine

def test_rules_engine():
    engine = HallucinationRuleEngine()
    
    # Test case: Question assumes unverified React experience
    context = {
        "generated_question": "In your React project, how did you handle state management?",
        "verified_profile": {"skills": ["JavaScript"]},  # No React listed
        "conversation_history": []
    }
    
    violations = engine.evaluate_all(context)
    
    print(f"Total violations: {len(violations)}")
    print(f"Blocker violations: {len(engine.get_blocker_violations(violations))}")
    
    for v in violations:
        if v.violated:
            print(f"\n❌ Rule: {v.rule.name}")
            print(f"   Reason: {v.reason}")
            print(f"   Severity: {v.rule.severity.value}")

if __name__ == "__main__":
    test_rules_engine()
```

Run:
```bash
cd apps/api
python test_intelligence.py
```

### 4. Test Behavior Engine

```python
# apps/api/test_behavior.py

from app.ai.intelligence.behavior.behavior_engine import BehaviorEngine

def test_behavior():
    # Test Amazon configuration
    amazon_behavior = BehaviorEngine()
    amazon_behavior.configure_from_company("amazon")
    
    print("Amazon Configuration:")
    print(f"  Pressure: {amazon_behavior.state.pressure_level.value}")
    print(f"  Personality: {amazon_behavior.state.personality.value}")
    print(f"  Follow-up depth: {amazon_behavior.state.follow_up_depth}")
    print(f"  Supportiveness: {amazon_behavior.state.supportiveness}")
    
    # Test Google configuration
    google_behavior = BehaviorEngine()
    google_behavior.configure_from_company("google")
    
    print("\nGoogle Configuration:")
    print(f"  Pressure: {google_behavior.state.pressure_level.value}")
    print(f"  Personality: {google_behavior.state.personality.value}")
    print(f"  Follow-up depth: {google_behavior.state.follow_up_depth}")
    print(f"  Supportiveness: {google_behavior.state.supportiveness}")
    
    # Test performance adjustment
    google_behavior.adjust_for_performance(performance_score=40, confidence_score=30)
    print("\nAfter poor performance:")
    print(f"  Recovery mode: {google_behavior.state.recovery_mode}")
    print(f"  Supportiveness: {google_behavior.state.supportiveness}")

if __name__ == "__main__":
    test_behavior()
```

### 5. Test Validators

```python
# apps/api/test_validators.py

from app.ai.intelligence.validators.hallucination_validator import HallucinationValidator
from app.ai.intelligence.validators.topic_validator import TopicValidator

def test_validators():
    # Hallucination validator
    h_validator = HallucinationValidator()
    
    # Should BLOCK this question (assumes unverified microservices)
    is_valid, reason, details = h_validator.validate_question(
        generated_question="In your microservices architecture, how did you handle service discovery?",
        verified_profile={"skills": ["Python"]},
        conversation_history=[]
    )
    
    print("Hallucination Validation Test:")
    print(f"  Valid: {is_valid}")
    print(f"  Reason: {reason}")
    
    # Topic validator
    t_validator = TopicValidator()
    
    # Should BLOCK this question (frontend interview drifting to backend)
    is_valid, reason, details = t_validator.validate_question(
        generated_question="How would you design a distributed caching system with Redis?",
        interview_config={"domain": "frontend", "type": "technical"}
    )
    
    print("\nTopic Boundary Validation Test:")
    print(f"  Valid: {is_valid}")
    print(f"  Reason: {reason}")

if __name__ == "__main__":
    test_validators()
```

### 6. Test Evaluation Rules

```python
# apps/api/test_evaluation.py

from app.ai.intelligence.rules.evaluation_rules import EvaluationRuleEngine

def test_evaluation():
    engine = EvaluationRuleEngine()
    
    # Test response with lots of filler words and hesitation
    poor_response = """
    Um, so like, I think we used, you know, React for the project.
    And, like, maybe we had some state management stuff, I guess.
    I'm not really sure about the details, but I believe it was Redux or something.
    """
    
    metrics = engine.compute_all_metrics(poor_response)
    
    print("Poor Response Metrics:")
    print(f"  Filler word score: {metrics['filler_word_score']:.1f}/100")
    print(f"  Confidence score: {metrics['confidence_score']:.1f}/100")
    print(f"  Filler count: {metrics.get('filler_count', 0)}")
    print(f"  Hesitation count: {metrics.get('hesitation_count', 0)}")
    
    # Test response with good structure and ownership
    good_response = """
    I led the development of a payment processing system that reduced transaction time by 40%.
    I designed the architecture, implemented the core logic, and optimized database queries.
    The system now handles 10,000 transactions per day with 99.9% uptime.
    I took ownership of the entire project from conception to deployment.
    """
    
    metrics = engine.compute_all_metrics(good_response)
    
    print("\nGood Response Metrics:")
    print(f"  Filler word score: {metrics['filler_word_score']:.1f}/100")
    print(f"  Confidence score: {metrics['confidence_score']:.1f}/100")
    print(f"  Ownership score: {metrics['ownership_score']:.1f}/100")
    print(f"  Impact score: {metrics['impact_score']:.1f}/100")

if __name__ == "__main__":
    test_evaluation()
```

## Integration Steps

### Step 1: Add Validation to Question Generation

Modify `apps/api/app/modules/questions/service.py`:

```python
# At the top
from app.ai.intelligence.validators.hallucination_validator import HallucinationValidator
from app.ai.intelligence.validators.topic_validator import TopicValidator

# Create validators
hallucination_validator = HallucinationValidator()
topic_validator = TopicValidator()

# In your generate_question method, add after LLM generation:

async def generate_question(...):
    # ... existing code to generate question ...
    
    # NEW: Validate before returning
    max_retries = 3
    for attempt in range(max_retries):
        # Hallucination check
        is_valid, reason, _ = hallucination_validator.validate_question(
            generated_question=question,
            verified_profile=session.candidate_profile,  # or however you get profile
            conversation_history=previous_turns
        )
        
        if not is_valid:
            logger.warning(f"Question blocked (hallucination): {reason}")
            question = await self._regenerate_question_safe(original_question, reason)
            continue
        
        # Topic boundary check
        is_valid, reason, _ = topic_validator.validate_question(
            generated_question=question,
            interview_config={
                "domain": session.domain,
                "type": session.interview_type
            }
        )
        
        if not is_valid:
            logger.warning(f"Question blocked (topic drift): {reason}")
            question = await self._regenerate_question_in_scope(original_question, reason)
            continue
        
        # Both checks passed
        break
    
    return question
```

### Step 2: Add Behavior Engine to Persona Generation

Modify `apps/api/app/interview_journey/personas/generator.py`:

```python
from app.ai.intelligence.behavior.behavior_engine import BehaviorEngine

async def generate_interviewer_persona(company: str, ...):
    # Configure behavior
    behavior = BehaviorEngine()
    behavior.configure_from_company(company.lower())
    
    # Get behavioral instructions
    instructions = behavior.get_behavioral_instructions()
    
    # Build persona with behavior
    persona = f"""
You are conducting a {company} technical interview.

Behavioral Guidelines:
{instructions['personality_instruction']}

{instructions['pressure_instruction']}

Follow-up Strategy:
- Depth: {instructions['follow_up_depth']}/5
- Supportiveness: {instructions['supportiveness']:.1f}
- Interruption: {'Enabled' if instructions['interruption_enabled'] else 'Disabled'}

{'[RECOVERY MODE: Be supportive and patient]' if instructions['recovery_mode'] else ''}
    """
    
    return persona, behavior  # Return behavior for later adjustment
```

### Step 3: Add Rule-Based Evaluation

Modify `apps/api/app/modules/evaluation/service.py`:

```python
from app.ai.intelligence.rules.evaluation_rules import EvaluationRuleEngine

# Create evaluation engine
eval_rule_engine = EvaluationRuleEngine()

async def evaluate_response(response: ResponseInstance, ...):
    # Get recent responses for stability analysis
    recent_responses = await self._get_recent_responses(response.session_id, limit=5)
    
    # Compute rule-based metrics (PRIMARY)
    rule_metrics = eval_rule_engine.compute_all_metrics(
        candidate_response=response.transcribed_text,
        recent_responses=[r.transcribed_text for r in recent_responses]
    )
    
    # Compute LLM-based metrics (SECONDARY)
    llm_metrics = await self._evaluate_with_llm(response)
    
    # Combined scoring (rule-based is 60%, LLM is 40%)
    final_score = (
        rule_metrics['filler_word_score'] * 0.15 +
        rule_metrics['confidence_score'] * 0.15 +
        rule_metrics['star_score'] * 0.10 +
        rule_metrics['ownership_score'] * 0.10 +
        rule_metrics['impact_score'] * 0.10 +
        llm_metrics.get('technical_accuracy', 70) * 0.20 +
        llm_metrics.get('depth', 70) * 0.20
    )
    
    # Store both sets of metrics
    response.rule_based_metrics = rule_metrics
    response.llm_metrics = llm_metrics
    response.final_score = final_score
    
    return final_score
```

## Testing Checklist

- [ ] Database migration runs successfully
- [ ] Models import without errors
- [ ] Rules engine blocks unverified assumptions
- [ ] Behavior engine configures Amazon vs Google correctly
- [ ] Validators block hallucinations and topic drift
- [ ] Evaluation rules compute deterministic metrics
- [ ] Integration with existing question generation works
- [ ] Integration with existing evaluation works

## Documentation

Read the comprehensive implementation guide:

```
INTELLIGENCE_LAYER_IMPLEMENTATION.md
```

This document contains:
- Full architecture overview
- All components explained
- Usage examples
- Integration guides
- Next phase roadmap

## Support

If you encounter issues:

1. Check imports work: `python -c "from app.ai.intelligence.rules import *"`
2. Check logs for validation failures
3. Test components individually before integration
4. Review metrics: `rule_engine.get_metrics()`

## Next Phase: Orchestrators

Once the foundation is tested and integrated, build:

1. **Interview Orchestrator** - End-to-end interview flow
2. **Turn Orchestrator** - Single turn processing
3. **Follow-up Orchestrator** - Answer classification and routing
4. **Prompt Assembler** - Layered prompt construction

See `INTELLIGENCE_LAYER_IMPLEMENTATION.md` for full roadmap.
