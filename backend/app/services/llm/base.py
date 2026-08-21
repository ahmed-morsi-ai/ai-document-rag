from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Provider-independent contract for generating text."""

    def generate(self, prompt: str) -> str:
        """Generate a plain-text answer from a prompt."""
        if not prompt.strip():
            raise ValueError("prompt must not be empty")

        return self._generate(prompt)

    @abstractmethod
    def _generate(self, prompt: str) -> str:
        """Implement provider-specific text generation."""
