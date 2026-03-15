import requests
import json
import asyncio
import httpx  # Aanbevolen voor asynchrone streaming
from typing import AsyncIterator, Dict, Any
from app.services.llm.base import BaseLLM
from app.config import LOCAL_MODEL_NAME, OLLAMA_URL

class LocalLLM(BaseLLM):

    PROVIDER_NAME = "local"

    # ===============================
    # 1️⃣ GENERATE (Non-streaming)
    # ===============================
    def generate(
        self,
        prompt: str,
        max_tokens: int = 500
    ) -> Dict[str, Any]: # Teruggeven van een Dict, geen AsyncIterator

        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": LOCAL_MODEL_NAME, # Gebruik de config variabele
                    "prompt": prompt,
                    "stream": False, # Voor generate zetten we stream op False
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.2
                    }
                },
                timeout=120
            )

            response.raise_for_status()
            data = response.json()

            text = data.get("response", "")
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            return {
                "text": text,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens
                },
                "cost": 0.0,
                "provider": self.PROVIDER_NAME
            }

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Local LLM generate failed: {str(e)}")

    # ===============================
    # 2️⃣ STREAM (Async streaming)
    # ===============================
    async def stream(
        self,
        prompt: str,
        max_tokens: int = 500
    ) -> AsyncIterator[str]:

        payload = {
            "model": LOCAL_MODEL_NAME,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.2
            }
        }

        try:
            # We gebruiken httpx omdat 'requests' de event-loop blokkeert
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", OLLAMA_URL, json=payload) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        try:
                            data = json.loads(line)
                            
                            if data.get("done"):
                                break

                            chunk = data.get("response", "")
                            if chunk:
                                yield chunk
                                # Geef de event-loop even ruimte
                                await asyncio.sleep(0)

                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            yield f"\n[Local streaming error: {str(e)}]"