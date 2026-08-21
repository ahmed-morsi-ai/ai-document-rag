import httpx

from app.services.llm.base import LLMProvider


class OllamaLLMProvider(LLMProvider):
    """LLM provider backed by a local Ollama HTTP API."""

    def __init__(
        self,
        base_url: str,
        model_name: str,
        timeout: float,
    ) -> None:
        if not base_url.strip():
            raise ValueError("base_url must not be empty")

        if not model_name.strip():
            raise ValueError("model_name must not be empty")

        if timeout <= 0:
            raise ValueError("timeout must be greater than 0")

        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout

    def _generate(self, prompt: str) -> str:
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        payload = response.json()
        answer = payload.get("response")

        if not isinstance(answer, str):
            raise ValueError("Ollama response did not contain text")

        return answer
