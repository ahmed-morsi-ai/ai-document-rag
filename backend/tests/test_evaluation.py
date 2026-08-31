import ast
import json
import tempfile
import unittest
from pathlib import Path

from app.evaluation.dataset import (
    EvaluationCase,
    EvaluationDatasetError,
    GroundingCase,
    load_dataset,
    load_grounding_dataset,
)
from app.evaluation.grounding import (
    GroundingEvaluationError,
    GroundingEvaluationResult,
    evaluate_grounding,
    normalize_evidence,
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
    GROUNDING_DATASET_PATH = (
        Path(__file__).resolve().parents[1]
        / "evaluation"
        / "grounding_v1.json"
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

    def test_valid_grounding_dataset_loads(self):
        cases = load_grounding_dataset(self.GROUNDING_DATASET_PATH)

        self.assertEqual(len(cases), 5)
        self.assertEqual(cases[0].id, "grounding-001")
        self.assertEqual(
            cases[0].query,
            "What is the termination notice period?",
        )
        self.assertEqual(
            cases[0].answer,
            "Either party may terminate with 30 days written notice.",
        )
        self.assertEqual(
            cases[0].expected_evidence,
            ("30 days written notice",),
        )
        self.assertEqual(
            cases[2].expected_evidence,
            (
                "one additional year",
                "non-renewal notice before the renewal deadline",
            ),
        )

    def test_grounding_dataset_missing_file_raises_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nonexistent.json"
            with self.assertRaisesRegex(
                EvaluationDatasetError,
                "dataset not found",
            ):
                load_grounding_dataset(path)

    def test_grounding_dataset_invalid_json_raises_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.json"
            path.write_text("{bad-json", encoding="utf-8")

            with self.assertRaisesRegex(
                EvaluationDatasetError,
                "not valid JSON",
            ):
                load_grounding_dataset(path)

    def test_grounding_dataset_non_array_root_raises_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.json"
            path.write_text('{"id": "grounding-001"}', encoding="utf-8")

            with self.assertRaisesRegex(
                EvaluationDatasetError,
                "root must be a JSON array",
            ):
                load_grounding_dataset(path)

    def test_grounding_dataset_empty_root_raises_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.json"
            path.write_text("[]", encoding="utf-8")

            with self.assertRaisesRegex(
                EvaluationDatasetError,
                "must contain at least one case",
            ):
                load_grounding_dataset(path)

    def test_grounding_dataset_non_object_case_raises_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.json"
            path.write_text('["not-an-object"]', encoding="utf-8")

            with self.assertRaisesRegex(
                EvaluationDatasetError,
                "must be a JSON object",
            ):
                load_grounding_dataset(path)

    def test_grounding_dataset_missing_fields_raises_error(self):
        required_fields = ["id", "query", "answer", "expected_evidence"]
        base_case = {
            "id": "case-1",
            "query": "query text",
            "answer": "answer text",
            "expected_evidence": ["evidence text"],
        }

        for field in required_fields:
            with tempfile.TemporaryDirectory() as temp_dir:
                case_data = dict(base_case)
                del case_data[field]
                path = Path(temp_dir) / "invalid.json"
                path.write_text(json.dumps([case_data]), encoding="utf-8")

                with self.assertRaisesRegex(
                    EvaluationDatasetError,
                    "missing required fields",
                ):
                    load_grounding_dataset(path)

    def test_grounding_dataset_invalid_field_types_raises_error(self):
        invalid_cases = [
            {"id": 123, "query": "q", "answer": "a", "expected_evidence": []},
            {"id": "c1", "query": 123, "answer": "a", "expected_evidence": []},
            {"id": "c1", "query": "q", "answer": 123, "expected_evidence": []},
            {"id": "c1", "query": "q", "answer": "a", "expected_evidence": "not-a-list"},
        ]

        for case_data in invalid_cases:
            with tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "invalid.json"
                path.write_text(json.dumps([case_data]), encoding="utf-8")

                with self.assertRaises(EvaluationDatasetError):
                    load_grounding_dataset(path)

    def test_grounding_dataset_empty_strings_raises_error(self):
        empty_cases = [
            {"id": "   ", "query": "q", "answer": "a", "expected_evidence": []},
            {"id": "c1", "query": "", "answer": "a", "expected_evidence": []},
            {"id": "c1", "query": "q", "answer": "  ", "expected_evidence": []},
        ]

        for case_data in empty_cases:
            with tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "invalid.json"
                path.write_text(json.dumps([case_data]), encoding="utf-8")

                with self.assertRaisesRegex(
                    EvaluationDatasetError,
                    "must be a non-empty string",
                ):
                    load_grounding_dataset(path)

    def test_grounding_dataset_duplicate_case_ids_raises_error(self):
        duplicate_data = [
            {"id": "dup-1", "query": "q1", "answer": "a1", "expected_evidence": []},
            {"id": "dup-1", "query": "q2", "answer": "a2", "expected_evidence": []},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.json"
            path.write_text(json.dumps(duplicate_data), encoding="utf-8")

            with self.assertRaisesRegex(
                EvaluationDatasetError,
                "Duplicate case id",
            ):
                load_grounding_dataset(path)

    def test_grounding_dataset_invalid_evidence_items_raises_error(self):
        invalid_cases = [
            {"id": "c1", "query": "q", "answer": "a", "expected_evidence": [123]},
            {"id": "c1", "query": "q", "answer": "a", "expected_evidence": ["  "]},
        ]

        for case_data in invalid_cases:
            with tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "invalid.json"
                path.write_text(json.dumps([case_data]), encoding="utf-8")

                with self.assertRaisesRegex(
                    EvaluationDatasetError,
                    "must be a non-empty string",
                ):
                    load_grounding_dataset(path)

    def test_grounding_dataset_empty_expected_evidence_allowed(self):
        case_data = [
            {"id": "c1", "query": "q", "answer": "a", "expected_evidence": []}
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "valid.json"
            path.write_text(json.dumps(case_data), encoding="utf-8")

            loaded = load_grounding_dataset(path)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].expected_evidence, ())

    def test_normalize_evidence_behavior(self):
        self.assertEqual(
            normalize_evidence("  Hello   WORLD \t\n  "),
            "hello world",
        )
        self.assertEqual(
            normalize_evidence("Sample Text"),
            "sample text",
        )

        with self.assertRaisesRegex(
            GroundingEvaluationError,
            "evidence must be a string",
        ):
            normalize_evidence(123)

    def test_evaluate_grounding_perfect_match(self):
        result = evaluate_grounding(
            expected_evidence=["30 days written notice", "either party"],
            source_texts=["Either party may terminate with 30 days written notice."],
        )

        self.assertEqual(result.matched_count, 2)
        self.assertEqual(result.expected_count, 2)
        self.assertEqual(result.coverage, 1.0)

    def test_evaluate_grounding_partial_match(self):
        result = evaluate_grounding(
            expected_evidence=["one additional year", "non-existent claim"],
            source_texts=["The agreement renews for one additional year."],
        )

        self.assertEqual(result.matched_count, 1)
        self.assertEqual(result.expected_count, 2)
        self.assertEqual(result.coverage, 0.5)

    def test_evaluate_grounding_zero_match(self):
        result = evaluate_grounding(
            expected_evidence=["unsupported claim"],
            source_texts=["Completely unrelated content."],
        )

        self.assertEqual(result.matched_count, 0)
        self.assertEqual(result.expected_count, 1)
        self.assertEqual(result.coverage, 0.0)

    def test_evaluate_grounding_empty_expected_evidence(self):
        result = evaluate_grounding(
            expected_evidence=[],
            source_texts=["Some source text."],
        )

        self.assertEqual(result.matched_count, 0)
        self.assertEqual(result.expected_count, 0)
        self.assertEqual(result.coverage, 1.0)

    def test_evaluate_grounding_deduplication_and_whitespace_in_expected(self):
        result = evaluate_grounding(
            expected_evidence=["  30 days  ", "30   DAYS", "   "],
            source_texts=["Requires 30 days notice."],
        )

        self.assertEqual(result.matched_count, 1)
        self.assertEqual(result.expected_count, 1)
        self.assertEqual(result.coverage, 1.0)

    def test_evaluate_grounding_multiple_sources_and_non_string_sources(self):
        result = evaluate_grounding(
            expected_evidence=["part one", "part two"],
            source_texts=["Contains part one.", 123, None, "And part two."],
        )

        self.assertEqual(result.matched_count, 2)
        self.assertEqual(result.expected_count, 2)
        self.assertEqual(result.coverage, 1.0)


if __name__ == "__main__":
    unittest.main()
