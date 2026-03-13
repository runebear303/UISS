from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncIterator


class BaseLLM(ABC):
    """
    Abstract base class for all LLM providers.
    Enforces consistent response contract across
    local and cloud implementations.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Returns:
        {
            "text": str,
            "usage": dict | None,
            "cost": float,
            "provider": str
        }
        """
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        max_tokens: int = 500
    ) -> AsyncIterator[str]:
        """
        Async token streaming generator.
        """
        pass