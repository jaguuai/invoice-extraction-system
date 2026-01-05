import requests
from src.core.config import settings
from src.core.logging import logger


class LLMClient:
    def __init__(self):
        self.use_local = settings.USE_LOCAL_LLM
        self.ollama_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL

    def complete(self, prompt: str) -> str:
        logger.info("🤖 Sending prompt to LLM")

        if self.use_local:
            return self._ollama_complete(prompt)
        else:
            raise RuntimeError("OpenAI fallback not implemented yet")

    def _ollama_complete(self, prompt: str) -> str:
        url = f"{self.ollama_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(url, json=payload, timeout=120)

        if response.status_code != 200:
            logger.error(f"Ollama error {response.status_code}: {response.text}")
            raise RuntimeError("Ollama request failed")

        data = response.json()

        if "response" not in data:
            logger.error(f"Unexpected Ollama response: {data}")
            raise RuntimeError("Invalid Ollama response format")

        return data["response"]


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
