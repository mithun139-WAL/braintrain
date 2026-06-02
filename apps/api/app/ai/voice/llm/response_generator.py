import time
import logging
import httpx
from app.core.config import get_settings

logger = logging.getLogger("response_generator")

class ResponseGenerator:
    def __init__(self):
        self.settings = get_settings()

    async def generate(self, messages: list[dict]) -> str:
        """
        Executes completion request against LLM API providers (e.g. NVIDIA NIM).
        Measures and logs API execution latency.
        """
        settings = self.settings
        url = f"{settings.nvidia_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.nvidia_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.nvidia_model,
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.7,
        }

        start_time = time.perf_counter()
        logger.info("response_generated | calling LLM | message_count: %d", len(messages))

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=30.0,
                )
                latency = time.perf_counter() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"].strip()
                    logger.info(
                        "response_generated | success | latency: %.3fs | tokens: %s",
                        latency,
                        result.get("usage", {}).get("total_tokens", "unknown"),
                    )
                    return content
                else:
                    logger.error(
                        "response_generated | error | status: %d | latency: %.3fs | message: %s",
                        response.status_code,
                        latency,
                        response.text,
                    )
                    return ""
        except Exception as exc:
            latency = time.perf_counter() - start_time
            logger.error(
                "response_generated | failure | latency: %.3fs | error: %s",
                latency,
                exc,
            )
            return ""
