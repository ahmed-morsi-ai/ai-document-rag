import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.document_chunking import chunk_text
from app.services.document_indexing import DocumentIndexer


class FakeEmbeddingProvider:
    def __init__(self):
        self.calls = []

    def embed_many(self, texts):
        self.calls.append(list(texts))

        return [
            [float(index), float(len(text))]
            for index, text in enumerate(texts)
        ]


class FakeVectorStore:
    def __init__(self):
        self.calls = []

    def add(
        self,
        ids,
        embeddings,
        texts,
        metadatas=None,
    ):
        self.calls.append(
            {
                "ids": list(ids),
                "embeddings": [list(embedding) for embedding in embeddings],
                "texts": list(texts),
                "metadatas": list(metadatas or []),
            }
        )


class DocumentIndexingTests(unittest.TestCase):
    def test_indexes_document_using_parser_chunker_embedding_and_vector_store(
        self,
    ):
        document_id = "document-123"
        original_text = (
            "abcdefghij"
        )
        expected_chunks = chunk_text(
            original_text,
            chunk_size=5,
            chunk_overlap=0,
        )

        embedding_provider = FakeEmbeddingProvider()
        vector_store = FakeVectorStore()
        indexer = DocumentIndexer(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "document.txt"
            file_path.write_text(
                original_text,
                encoding="utf-8",
            )

            with patch(
                "app.services.document_indexing.chunk_text",
                side_effect=lambda text: chunk_text(
                    text,
                    chunk_size=5,
                    chunk_overlap=0,
                ),
            ) as chunker:
                indexed_count = indexer.index_document(
                    document_id=document_id,
                    file_path=file_path,
                )

        self.assertEqual(
            indexed_count,
            len(expected_chunks),
        )
        chunker.assert_called_once_with(
            original_text,
        )
        self.assertEqual(
            embedding_provider.calls,
            [expected_chunks],
        )
        self.assertEqual(
            vector_store.calls,
            [
                {
                    "ids": [
                        "document-123:0",
                        "document-123:1",
                    ],
                    "embeddings": [
                        [0.0, 5.0],
                        [1.0, 5.0],
                    ],
                    "texts": expected_chunks,
                    "metadatas": [
                        {
                            "document_id": "document-123",
                            "chunk_index": "0",
                        },
                        {
                            "document_id": "document-123",
                            "chunk_index": "1",
                        },
                    ],
                }
            ],
        )

    def test_empty_document_returns_zero_without_embedding_or_vector_store(
        self,
    ):
        embedding_provider = Mock()
        vector_store = Mock()
        indexer = DocumentIndexer(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "empty.txt"
            file_path.write_text(
                "",
                encoding="utf-8",
            )

            indexed_count = indexer.index_document(
                document_id="empty-document",
                file_path=file_path,
            )

        self.assertEqual(indexed_count, 0)
        embedding_provider.embed_many.assert_not_called()
        vector_store.add.assert_not_called()

    def test_parser_failure_propagates(self):
        embedding_provider = Mock()
        vector_store = Mock()
        indexer = DocumentIndexer(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )

        parser = Mock()
        parser.parse.side_effect = RuntimeError(
            "parser failure"
        )

        with patch(
            "app.services.document_indexing.get_document_parser",
            return_value=parser,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "parser failure",
            ):
                indexer.index_document(
                    document_id="document-123",
                    file_path=Path("document.txt"),
                )

        embedding_provider.embed_many.assert_not_called()
        vector_store.add.assert_not_called()

    def test_embedding_failure_propagates(self):
        embedding_provider = Mock()
        vector_store = Mock()
        indexer = DocumentIndexer(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )

        embedding_provider.embed_many.side_effect = RuntimeError(
            "embedding failure"
        )

        parser = Mock()
        parser.parse.return_value = "abcdefghij"

        with patch(
            "app.services.document_indexing.get_document_parser",
            return_value=parser,
        ):
            with patch(
                "app.services.document_indexing.chunk_text",
                return_value=["abc", "def"],
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "embedding failure",
                ):
                    indexer.index_document(
                        document_id="document-123",
                        file_path=Path("document.txt"),
                    )

        vector_store.add.assert_not_called()

    def test_vector_store_failure_propagates(self):
        embedding_provider = FakeEmbeddingProvider()
        vector_store = Mock()
        vector_store.add.side_effect = RuntimeError(
            "vector store failure"
        )

        indexer = DocumentIndexer(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )

        parser = Mock()
        parser.parse.return_value = "abcdefghij"

        with patch(
            "app.services.document_indexing.get_document_parser",
            return_value=parser,
        ):
            with patch(
                "app.services.document_indexing.chunk_text",
                return_value=["abc", "def"],
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "vector store failure",
                ):
                    indexer.index_document(
                        document_id="document-123",
                        file_path=Path("document.txt"),
                    )

        self.assertEqual(
            embedding_provider.calls,
            [["abc", "def"]],
        )

    def test_repeated_indexing_generates_same_vector_ids(self):
        embedding_provider = FakeEmbeddingProvider()
        vector_store = FakeVectorStore()
        indexer = DocumentIndexer(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )

        parser = Mock()
        parser.parse.return_value = "abcdefghij"

        with patch(
            "app.services.document_indexing.get_document_parser",
            return_value=parser,
        ):
            with patch(
                "app.services.document_indexing.chunk_text",
                return_value=["abc", "def"],
            ):
                first_count = indexer.index_document(
                    document_id="document-123",
                    file_path=Path("document.txt"),
                )
                second_count = indexer.index_document(
                    document_id="document-123",
                    file_path=Path("document.txt"),
                )

        self.assertEqual(first_count, 2)
        self.assertEqual(second_count, 2)

        self.assertEqual(
            vector_store.calls[0]["ids"],
            [
                "document-123:0",
                "document-123:1",
            ],
        )
        self.assertEqual(
            vector_store.calls[1]["ids"],
            [
                "document-123:0",
                "document-123:1",
            ],
        )

    def test_rejects_empty_document_id(self):
        indexer = DocumentIndexer(
            embedding_provider=Mock(),
            vector_store=Mock(),
        )

        with self.assertRaisesRegex(
            ValueError,
            "document_id must not be empty",
        ):
            indexer.index_document(
                document_id="",
                file_path=Path("document.txt"),
            )


if __name__ == "__main__":
    unittest.main()
