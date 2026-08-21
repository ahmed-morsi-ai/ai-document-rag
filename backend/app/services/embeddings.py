from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Provider-independent interface for generating text embeddings."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single text input."""

    def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate embeddings while preserving input order."""
        return [
            self.embed(text)
            for text in texts
        ]
