import unittest
from unittest.mock import Mock, patch

from app.services.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)


class SentenceTransformerEmbeddingProviderTests(unittest.TestCase):
    @patch(
        "app.services.embeddings.sentence_transformer.SentenceTransformer"
    )
    def test_initialization_passes_model_name_to_sentence_transformer(
        self,
        sentence_transformer_cls,
    ):
        SentenceTransformerEmbeddingProvider(
            "test-model"
        )

        sentence_transformer_cls.assert_called_once_with(
            "test-model"
        )

    @patch(
        "app.services.embeddings.sentence_transformer.SentenceTransformer"
    )
    def test_embed_returns_model_embedding_as_list(
        self,
        sentence_transformer_cls,
    ):
        model = Mock()
        encoded_embedding = Mock()
        encoded_embedding.tolist.return_value = [
            0.1,
            0.2,
            0.3,
        ]

        model.encode.return_value = encoded_embedding
        sentence_transformer_cls.return_value = model

        provider = SentenceTransformerEmbeddingProvider(
            "test-model"
        )

        result = provider.embed("hello")

        self.assertEqual(
            result,
            [0.1, 0.2, 0.3],
        )

        model.encode.assert_called_once_with(
            "hello",
            convert_to_numpy=True,
        )

    @patch(
        "app.services.embeddings.sentence_transformer.SentenceTransformer"
    )
    def test_embed_many_preserves_input_order(
        self,
        sentence_transformer_cls,
    ):
        model = Mock()
        encoded_embeddings = Mock()
        encoded_embeddings.tolist.return_value = [
            [0.1, 0.2],
            [0.3, 0.4],
        ]

        model.encode.return_value = encoded_embeddings
        sentence_transformer_cls.return_value = model

        provider = SentenceTransformerEmbeddingProvider(
            "test-model"
        )

        texts = [
            "first",
            "second",
        ]

        result = provider.embed_many(texts)

        self.assertEqual(
            result,
            [
                [0.1, 0.2],
                [0.3, 0.4],
            ],
        )

        model.encode.assert_called_once_with(
            texts,
            convert_to_numpy=True,
        )


if __name__ == "__main__":
    unittest.main()
