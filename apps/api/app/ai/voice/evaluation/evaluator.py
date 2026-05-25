from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.ai.voice.conversation.memory import ConversationMessage
from app.ai.voice.evaluation.evaluation_types import EvaluatorOutput

class BaseEvaluator(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """The identifier name of the evaluator."""
        pass

    @abstractmethod
    async def evaluate(
        self,
        messages: List[ConversationMessage],
        behavioral_metrics: Dict[str, Any]
    ) -> EvaluatorOutput:
        """
        Processes conversation history and behavioral signals to generate an evaluation output.
        """
        pass
