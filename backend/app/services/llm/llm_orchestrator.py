import psutil
from typing import AsyncIterator
from typing import Dict, Any
from app.config import LLM_PROVIDER, RAM_ALERT_THRESHOLD
from .llm_local import LocalLLM
from .llm_cloud import CloudLLM


local_llm = LocalLLM()
cloud_llm = CloudLLM()


# ===============================
# MEMORY CHECK
# ===============================

def ram_usage_percent() -> float:
    """Return current RAM usage percentage."""
    return psutil.virtual_memory().percent


# ===============================
# MAIN ROUTING
# ===============================

def ask_llm(prompt: str) -> Dict[str, Any]:

    try:

        if LLM_PROVIDER == "local":
            result = local_llm.generate(prompt)
            result["router"] = "forced_local"
            result["ram_usage"] = ram_usage_percent()
            return result

        if LLM_PROVIDER == "cloud":
            result = cloud_llm.generate(prompt)
            result["router"] = "forced_cloud"
            result["ram_usage"] = ram_usage_percent()
            return result

        if LLM_PROVIDER == "auto":

            ram_usage = ram_usage_percent()

            if ram_usage < RAM_ALERT_THRESHOLD:
                result = local_llm.generate(prompt)
                result["router"] = "auto_local"
            else:
                result = cloud_llm.generate(prompt)
                result["router"] = "auto_cloud"

            result["ram_usage"] = ram_usage
            return result

        result = local_llm.generate(prompt)
        result["router"] = "default_local"
        result["ram_usage"] = ram_usage_percent()
        return result

    except Exception as e:

        try:
            fallback = cloud_llm.generate(prompt)
            fallback["provider"] = "cloud_fallback"
            fallback["router"] = "error_fallback"
            fallback["ram_usage"] = ram_usage_percent()
            return fallback

        except Exception:
            raise RuntimeError(
                f"Both local and cloud LLM failed: {str(e)}"
            )
 # ===============================
# STREAMING FUNCTION
# ===============================

local_llm = LocalLLM()
cloud_llm = CloudLLM()

async def ask_llm_stream(prompt: str, max_tokens: int = 500) -> AsyncIterator[str]:
    """
    Stream tokens from either local or cloud LLM based on configuration.
    """
    try:
        if LLM_PROVIDER == "local":
            async for token in local_llm.stream(prompt, max_tokens=max_tokens):
                yield token
            return

        if LLM_PROVIDER == "cloud":
            async for token in cloud_llm.stream(prompt, max_tokens=max_tokens):
                yield token
            return

        # auto-routing (choose local if memory < threshold, otherwise cloud)
        # optional: implement RAM check here if needed
        async for token in local_llm.stream(prompt, max_tokens=max_tokens):
            yield token

    except Exception as e:
        # fallback to cloud if local fails
        async for token in cloud_llm.stream(prompt, max_tokens=max_tokens):
            yield token