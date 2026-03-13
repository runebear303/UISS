from app.services.llm.base import BaseLLM
from app.config import CLOUD_MODEL_NAME, CLOUD_SIMULATION
from typing import AsyncIterator, Dict, Any
import asyncio


# ===============================
# MODEL PRICING (USD per 1K tokens)
# ===============================

MODEL_PRICING = {
    "gpt-4o-mini": {
        "input": 0.00015,
        "output": 0.00060
    }
}


class CloudLLM(BaseLLM):

    # -------------------------------
    # COST CALCULATION
    # -------------------------------

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = MODEL_PRICING.get(
            CLOUD_MODEL_NAME,
            {"input": 0, "output": 0}
        )

        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]

        return round(input_cost + output_cost, 6)

    # -------------------------------
    # GENERATE (Non-streaming)
    # -------------------------------

    def generate(self, prompt: str, max_tokens: int = 500) -> Dict[str, Any]:

        # -------------------------------
        # CLOUD SIMULATION MODE
        # -------------------------------

        if CLOUD_SIMULATION:

            prompt_tokens = 120
            completion_tokens = 80
            total_tokens = prompt_tokens + completion_tokens

            cost = self._calculate_cost(prompt_tokens, completion_tokens)

            return {
                "text": (
                    "[SIMULATED CLOUD RESPONSE]\n\n"
                    "This response demonstrates that the system "
                    "can route requests to a cloud-based LLM provider."
                ),
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                },
                "cost": cost,
                "provider": "cloud_simulation"
            }

        # -------------------------------
        # REAL CLOUD DISABLED
        # -------------------------------

        raise RuntimeError(
            "Cloud provider disabled. Enable CLOUD_SIMULATION or configure a real provider."
        )

    # -------------------------------
    # STREAM (Async)
    # -------------------------------

    async def stream(
        self,
        prompt: str,
        max_tokens: int = 500
    ) -> AsyncIterator[str]:

        if CLOUD_SIMULATION:

            demo_text = (
                "[SIMULATED CLOUD STREAM]\n"
                "This demonstrates streaming responses from a cloud-based LLM."
            )

            for word in demo_text.split():
                yield word + " "
                await asyncio.sleep(0.05)

            return

        yield "[Cloud provider disabled]"

        