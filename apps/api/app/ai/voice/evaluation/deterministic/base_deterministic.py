from abc import ABC, abstractmethod
from typing import Any, Dict, List

class DeterministicEvaluator(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def evaluate(self, text: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def evidence(self, result: Dict[str, Any]) -> List[str]:
        pass
