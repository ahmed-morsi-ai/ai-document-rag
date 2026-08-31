import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Sequence

from app.evaluation.dataset import EvaluationCase, load_dataset
from app.evaluation.metrics import (
    EvaluationMetrics,
    calculate_metrics,
    chunk_key,
)


class EvaluationRunnerError(ValueError):
    """Raised when injected evaluation retrieval data is invalid."""


RetrievalFunction = Callable[
    [EvaluationCase, int],
    Sequence[Any],
]


def _as_chunk_id(value: Any) -> str:
    if isinstance(value, str):
        if not value.strip():
            raise EvaluationRunnerError(
                "Injected retrieval result contains an empty chunk id"
            )
        return value

    try:
        return chunk_key(
            value.document_id,
            value.chunk_index,
        )
    except AttributeError as exc:
        raise EvaluationRunnerError(
            "Injected retrieval results must be chunk-id strings "
            "or objects exposing document_id and chunk_index"
        ) from exc


@dataclass(frozen=True)
class EvaluationResult:
    evaluation: str
    k: int
    cases: int
    metrics: EvaluationMetrics

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation": self.evaluation,
            "k": self.k,
            "cases": self.cases,
            "metrics": {
                "recall_at_k": self.metrics.recall_at_k,
                "precision_at_k": self.metrics.precision_at_k,
                "hit_rate_at_k": self.metrics.hit_rate_at_k,
            },
        }


def run_evaluation(
    dataset: Sequence[EvaluationCase],
    retrieve: RetrievalFunction,
    k: int,
    *,
    evaluation_name: str = "retrieval-v1",
) -> EvaluationResult:
    if not dataset:
        raise EvaluationRunnerError("dataset must not be empty")

    retrieved_by_case: dict[str, list[str]] = {}

    for case in dataset:
        raw_results = retrieve(case, k)
        if raw_results is None:
            raise EvaluationRunnerError(
                f"Retriever returned None for case {case.id}"
            )

        retrieved_by_case[case.id] = [
            _as_chunk_id(result)
            for result in raw_results
        ]

    metrics = calculate_metrics(
        dataset,
        retrieved_by_case,
        k,
    )

    return EvaluationResult(
        evaluation=evaluation_name,
        k=k,
        cases=len(dataset),
        metrics=metrics,
    )


def _load_fixture_results(path: Path) -> dict[str, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvaluationRunnerError(
            f"Retrieval results file not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise EvaluationRunnerError(
            f"Retrieval results file is not valid JSON: {path}"
        ) from exc

    if not isinstance(payload, dict):
        raise EvaluationRunnerError(
            "Retrieval results root must be a JSON object keyed by case id"
        )

    results: dict[str, list[str]] = {}

    for case_id, values in payload.items():
        if not isinstance(case_id, str) or not case_id.strip():
            raise EvaluationRunnerError(
                "Retrieval result case ids must be non-empty strings"
            )

        if not isinstance(values, list):
            raise EvaluationRunnerError(
                f"Retrieval results for {case_id} must be a JSON array"
            )

        normalized: list[str] = []
        for position, value in enumerate(values):
            if not isinstance(value, str) or not value.strip():
                raise EvaluationRunnerError(
                    f"Retrieval result {case_id}[{position}] "
                    "must be a non-empty string"
                )
            normalized.append(value)

        results[case_id] = normalized

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run deterministic retrieval evaluation."
    )
    parser.add_argument(
        "--dataset",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--results",
        required=True,
        type=Path,
        help=(
            "JSON object mapping evaluation case ids to retrieved "
            "stable chunk ids."
        ),
    )
    parser.add_argument(
        "--k",
        required=True,
        type=int,
    )

    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    fixture_results = _load_fixture_results(args.results)

    result = run_evaluation(
        dataset,
        lambda case, _k: fixture_results.get(case.id, []),
        args.k,
        evaluation_name=args.dataset.stem,
    )

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
