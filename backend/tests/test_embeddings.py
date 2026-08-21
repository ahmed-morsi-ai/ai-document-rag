import unittest

from app.services.embeddings import EmbeddingProvider


class DeterministicEmbeddingProvider(EmbeddingProvider):
    """Simple test-only embedding provider."""

    def embed(self, text: str) -> list[float]:
        return [
            float(len(text)),
            float(sum(ord(char) for char in text)),
        ]


class EmbeddingProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = DeterministicEmbeddingProvider()

    def test_embedding_provider_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            EmbeddingProvider()

    def test_embed_returns_expected_embedding_structure(self):
        embedding = self.provider.embed("abc")

        self.assertEqual(
            embedding,
            [3.0, 294.0],
        )
        self.assertTrue(
            all(
                isinstance(value, float)
                for value in embedding
            )
        )

    def test_embed_many_preserves_input_order(self):
        texts = [
            "a",
            "ab",
            "abc",
        ]

        embeddings = self.provider.embed_many(texts)

        self.assertEqual(
            embeddings,
            [
                [1.0, 97.0],
                [2.0, 195.0],
                [3.0, 294.0],
            ],
        )

    def test_empty_text_has_explicit_embedding(self):
        self.assertEqual(
            self.provider.embed(""),
            [0.0, 0.0],
        )

    def test_empty_batch_returns_empty_list(self):
        self.assertEqual(
            self.provider.embed_many([]),
            [],
        )

    def test_repeated_calls_are_deterministic(self):
        text = "deterministic embedding"

        first = self.provider.embed(text)
        second = self.provider.embed(text)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
