import ast
import json
import tempfile
import unittest
from pathlib import Path

from app.evaluation.dataset import (
    EvaluationCase,
    EvaluationDatasetError,
    load_dataset,
)
from app.evaluation.metrics import (
    calculate_metrics,
    chunk_key,
    hit_rate_at_k,
    precision_at_k,
    recall_at_k,
)
from app.evaluation.runner import run_evaluation
from app.services.rag import RagService
from app.services.retrieval import RetrievalResult, Retriever


class EvaluationTests(unittest.TestCase):
    DATASET_PATH = (
        Path(__file__).resolve().parents[1]
        / "evaluation"
        / "retrieval_v1.json"
    )

    def test_valid_dataset_loads(self):
        cases = load_dataset(self.DATASET_PATH)

        self.assertEqual(len(cases), 6)
        self.assertEqual(cases[0].id, "retrieval-001")
        self.assertEqual(
            cases[1].relevant_chunk_ids,
            ("document-alpha:0",),
        )

    def test_malformed_dataset_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.json"
            path.write_text('{"id":"wrong-root"}', encoding="utf-8")

            with self.assertRaisesRegex(
                EvaluationDatasetError,
                "root must be a JSON array",
            ):
                load_dataset(path)

    def test_invalid_case_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "id": "case-1",
                            "query": "hello",
                            "relevant_chunk_ids": ["bad-id"],
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                EvaluationDatasetError,
                "format",
            ):
                load_dataset(path)

    def test_chunk_key_construction(self):
        self.assertEqual(
            chunk_key("document-123", 1),
            "document-123:1",
        )

    def test_perfect_recall(self):
        self.assertEqual(
            recall_at_k(
                ["document-1:0", "document-1:1"],
                ["document-1:0", "document-1:1"],
                2,
            ),
            1.0,
        )

    def test_partial_recall(self):
        self.assertEqual(
            recall_at_k(
                ["document-1:0", "document-1:1"],
                ["document-1:0"],
                2,
            ),
            0.5,
        )

    def test_zero_relevant_retrieved(self):
        self.assertEqual(
            recall_at_k(
                ["document-1:0"],
                [],
                3,
            ),
            0.0,
        )

    def test_perfect_precision(self):
        self.assertEqual(
            precision_at_k(
                ["document-1:0"],
                ["document-1:0"],
                3,
            ),
            1.0,
        )

    def test_mixed_precision(self):
        self.assertEqual(
            precision_at_k(
                ["document-1:0"],
                ["document-1:0", "document-9:0"],
                2,
            ),
            0.5,
        )

    def test_empty_retrieval_precision_is_explicitly_zero(self):
        self.assertEqual(
            precision_at_k(
                ["document-1:0"],
                [],
                3,
            ),
            0.0,
        )

    def test_hit_rate_hit(self):
        self.assertEqual(
            hit_rate_at_k(
                ["document-1:0"],
                ["document-1:0"],
                3,
            ),
            1.0,
        )

    def test_hit_rate_miss(self):
        self.assertEqual(
            hit_rate_at_k(
                ["document-1:0"],
                ["document-9:0"],
                3,
            ),
            0.0,
        )

    def test_k_larger_than_available_results(self):
        self.assertEqual(
            precision_at_k(
                ["document-1:0"],
                ["document-1:0"],
                10,
            ),
            1.0,
        )
        self.assertEqual(
            recall_at_k(
                ["document-1:0", "document-1:1"],
                ["document-1:0"],
                10,
            ),
            0.5,
        )

    def test_multiple_relevant_chunks(self):
        self.assertEqual(
            hit_rate_at_k(
                ["document-1:0", "document-1:1"],
                ["document-1:1"],
                2,
            ),
            1.0,
        )
        self.assertEqual(
            recall_at_k(
                ["document-1:0", "document-1:1"],
                ["document-1:1"],
                2,
            ),
            0.5,
        )

    def test_duplicate_retrieved_ids_do_not_inflate_precision(self):
        self.assertEqual(
            precision_at_k(
                ["document-1:0"],
                ["document-1:0", "document-1:0", "document-9:0"],
                3,
            ),
            0.5,
        )

    def test_duplicates_do_not_pull_results_from_beyond_top_k(self):
        self.assertEqual(
            precision_at_k(
                ["document-1:0", "document-9:0"],
                ["document-1:0", "document-1:0", "document-9:0"],
                2,
            ),
            1.0,
        )

    def test_zero_relevant_chunk_behavior_is_explicit(self):
        self.assertEqual(
            recall_at_k([], ["document-1:0"], 3),
            0.0,
        )
        self.assertEqual(
            hit_rate_at_k([], ["document-1:0"], 3),
            0.0,
        )
        self.assertEqual(
            precision_at_k([], [], 3),
            0.0,
        )

    def test_dataset_aggregation_is_macro_average(self):
        cases = [
            EvaluationCase(
                id="case-1",
                query="one",
                relevant_chunk_ids=("document-1:0",),
            ),
            EvaluationCase(
                id="case-2",
                query="two",
                relevant_chunk_ids=("document-2:0",),
            ),
        ]

        metrics = calculate_metrics(
            cases,
            {
                "case-1": ["document-1:0"],
                "case-2": ["document-9:0"],
            },
            1,
        )

        self.assertEqual(metrics.recall_at_k, 0.5)
        self.assertEqual(metrics.precision_at_k, 0.5)
        self.assertEqual(metrics.hit_rate_at_k, 0.5)

    def test_deterministic_runner_output(self):
        dataset = load_dataset(self.DATASET_PATH)

        fake_results = {
            "retrieval-001": ["document-1:0"],
            "retrieval-002": [
                "document-1:0",
                "document-9:0",
            ],
            "retrieval-003": [],
            "retrieval-004": ["document-9:0"],
            "retrieval-005": [],
            "retrieval-006": [],
        }

        def retrieve(case, _k):
            return fake_results[case.id]

        first = run_evaluation(dataset, retrieve, 3)
        second = run_evaluation(dataset, retrieve, 3)

        self.assertEqual(first, second)
        self.assertEqual(first.cases, 6)
        self.assertEqual(first.k, 3)

    def test_provider_independence(self):
        evaluation_dir = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "evaluation"
        )
        forbidden = {
            "chromadb",
            "ollama",
            "sentence_transformers",
            "httpx",
        }

        for path in evaluation_dir.glob("*.py"):
            tree = ast.parse(
                path.read_text(encoding="utf-8"),
                filename=str(path),
            )

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported = [
                        alias.name.split(".")[0]
                        for alias in node.names
                    ]
                elif isinstance(node, ast.ImportFrom):
                    imported = [
                        node.module.split(".")[0]
                    ] if node.module else []
                else:
                    continue

                self.assertTrue(
                    forbidden.isdisjoint(imported),
                    f"Provider-specific import found in {path}: {imported}",
                )

    def test_existing_retrieval_behavior_remains_provider_independent(self):
        class FakeEmbeddingProvider:
            def embed(self, text):
                return [1.0, 0.0]

        class FakeVectorStore:
            def query(self, embedding, top_k=5):
                self.call = (embedding, top_k)
                return []

        retriever = Retriever(
            embedding_provider=FakeEmbeddingProvider(),
            vector_store=FakeVectorStore(),
        )

        self.assertEqual(
            retriever.retrieve("hello", top_k=2),
            [],
        )

    def test_existing_rag_behavior_remains_unchanged(self):
        result = RetrievalResult(
            text="first chunk",
            document_id="document-1",
            chunk_index=0,
            distance=0.1,
            metadata={
                "document_id": "document-1",
                "chunk_index": "0",
            },
        )

        class FakeRetriever:
            def retrieve(self, query, top_k=5):
                self.asserted = (query, top_k)
                return [result]

        class FakeLLM:
            def generate(self, prompt):
                return "generated answer"

        service = RagService(
            FakeRetriever(),
            llm_provider=FakeLLM(),
        )

        response = service.generate_answer(
            "hello",
            top_k=1,
        )

        self.assertEqual(response.answer, "generated answer")
        self.assertEqual(response.sources, [result])
        self.assertEqual(
            response.context.context,
            "[Source 1]\nfirst chunk",
        )


if __name__ == "__main__":
    unittest.main()
