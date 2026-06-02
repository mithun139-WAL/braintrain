import asyncio
import uuid
from typing import List, Dict, Any

from app.ai.voice.evaluation.evaluation_types import EvaluationDimension, EvaluatorOutput
from app.ai.voice.evaluation.evaluator import BaseEvaluator
from app.ai.voice.evaluation.evaluation_pipeline import EvaluationPipeline
from app.ai.voice.conversation.memory import ConversationMessage

# Mock Evaluators for Testing
class MockTechnicalEvaluator(BaseEvaluator):
    @property
    def name(self) -> str:
        return "mock_technical_evaluator"

    async def evaluate(
        self,
        messages: List[ConversationMessage],
        behavioral_metrics: Dict[str, Any]
    ) -> EvaluatorOutput:
        return EvaluatorOutput(
            evaluator_name=self.name,
            dimension=EvaluationDimension.TECHNICAL,
            score=4.5, # Advanced technical skill
            confidence_score=0.9,
            evidence=["Demonstrated deep knowledge of event loops", "Explained macro/micro tasks correctly"]
        )

class MockBehavioralEvaluator(BaseEvaluator):
    @property
    def name(self) -> str:
        return "mock_behavioral_evaluator"

    async def evaluate(
        self,
        messages: List[ConversationMessage],
        behavioral_metrics: Dict[str, Any]
    ) -> EvaluatorOutput:
        # Simulate hesitation causing confidence penalty (score 2.0)
        return EvaluatorOutput(
            evaluator_name=self.name,
            dimension=EvaluationDimension.BEHAVIORAL,
            score=2.0,
            confidence_score=0.8,
            evidence=["Exhibited frequent long pauses when discussing complex topics"]
        )

async def run_tests():
    print("=== Running Evaluation Intelligence Engine Tests ===")
    
    session_id = uuid.uuid4()
    candidate_id = uuid.uuid4()
    
    # 1. Register Mock Evaluators in Pipeline
    pipeline = EvaluationPipeline()
    pipeline.register_evaluator(MockTechnicalEvaluator())
    pipeline.register_evaluator(MockBehavioralEvaluator())
    
    messages = [
        ConversationMessage(role="assistant", content="Explain how you handle concurrency in your application."),
        ConversationMessage(role="user", content="We use concurrency for non-blocking I/O. I definitely know it is useful for handling multiple operations simultaneously. I designed the concurrency system which reduced latency, and I implemented the task queue which ensured that all messages were processed efficiently and without data loss.")
    ]
    metrics = {
        "hesitation_count": 5,
        "response_time_ms": 15000.0,
    }
    
    # 2. Execute Evaluation Pipeline
    report = await pipeline.execute_evaluation(session_id, candidate_id, messages, metrics)
    
    # 3. Assertions
    print(f"Technical Score: {report.scores[EvaluationDimension.TECHNICAL]}")
    print(f"Behavioral Score: {report.scores[EvaluationDimension.BEHAVIORAL]}")
    print(f"Confidence Interval: {report.confidence_interval}")
    
    # The consistency penalty (due to high technical score but high hesitation/low behavioral score) should decrease technical score
    # Score without penalty: 4.5
    # Consistency multiplier: 1.0 - 0.15 = 0.85
    # Penalized technical score: 4.5 * 0.85 = 3.825 (rounded to 3.83 or close)
    assert report.scores[EvaluationDimension.TECHNICAL] < 4.5, "Expected consistency penalty to reduce technical score"
    assert len(report.feedback["strengths"]) > 0, "Expected strengths feedback to be populated"
    assert len(report.feedback["areas_of_improvement"]) > 0, "Expected improvement feedback to be populated"
    
    print("\n✓ Evaluation Pipeline ran and completed assertions successfully.")
    print("=== All Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
