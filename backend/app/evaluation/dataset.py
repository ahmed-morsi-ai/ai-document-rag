from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


class EvaluationDatasetError(ValueError):
    """Raised when the repository evaluation dataset is malformed."""


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    query: str
    relevant_chunk_ids: tuple[str, ...]


@dataclass(frozen=True)
class GroundingCase:
    id: str
    query: str
    answer: str
    expected_evidence: tuple[str, ...]


def _require_non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvaluationDatasetError(
            f"{field} must be a non-empty string"
        )
    return value


def _validate_chunk_id(value: Any, field: str) -> str:
    value = _require_non_empty_string(value, field)

    document_id, separator, chunk_index = value.rpartition(":")
    if not separator or not document_id or not chunk_index.isdigit():
        raise EvaluationDatasetError(
            f"{field} must use '<document_id>:<chunk_index>' format"
        )

    return value


def load_dataset(path: Path) -> list[EvaluationCase]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvaluationDatasetError(
            f"Evaluation dataset not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise EvaluationDatasetError(
            f"Evaluation dataset is not valid JSON: {path}"
        ) from exc

    if not isinstance(payload, list):
        raise EvaluationDatasetError(
            "Evaluation dataset root must be a JSON array"
        )

    if not payload:
        raise EvaluationDatasetError(
            "Evaluation dataset must contain at least one case"
        )

    cases: list[EvaluationCase] = []
    seen_case_ids: set[str] = set()

    for index, raw_case in enumerate(payload):
        if not isinstance(raw_case, dict):
            raise EvaluationDatasetError(
                f"Case {index} must be a JSON object"
            )

        missing = [
            field
            for field in ("id", "query", "relevant_chunk_ids")
            if field not in raw_case
        ]
        if missing:
            raise EvaluationDatasetError(
                f"Case {index} is missing required fields: "
                f"{', '.join(missing)}"
            )

        case_id = _require_non_empty_string(
            raw_case["id"],
            f"case {index} id",
        )

        if case_id in seen_case_ids:
            raise EvaluationDatasetError(
                f"Duplicate case id: {case_id}"
            )
        seen_case_ids.add(case_id)

        query = _require_non_empty_string(
            raw_case["query"],
            f"case {case_id} query",
        )

        relevant_chunk_ids = raw_case["relevant_chunk_ids"]
        if not isinstance(relevant_chunk_ids, list):
            raise EvaluationDatasetError(
                f"Case {case_id} relevant_chunk_ids must be a JSON array"
            )

        normalized_ids: list[str] = []
        seen_chunk_ids: set[str] = set()

        for chunk_position, chunk_id in enumerate(relevant_chunk_ids):
            validated = _validate_chunk_id(
                chunk_id,
                f"case {case_id} relevant_chunk_ids[{chunk_position}]",
            )

            if validated in seen_chunk_ids:
                raise EvaluationDatasetError(
                    f"Case {case_id} contains duplicate relevant chunk id: "
                    f"{validated}"
                )

            seen_chunk_ids.add(validated)
            normalized_ids.append(validated)

        cases.append(
            EvaluationCase(
                id=case_id,
                query=query,
                relevant_chunk_ids=tuple(normalized_ids),
            )
        )

    return cases


def load_grounding_dataset(path: Path) -> list[GroundingCase]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvaluationDatasetError(
            f"Grounding evaluation dataset not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise EvaluationDatasetError(
            f"Grounding evaluation dataset is not valid JSON: {path}"
        ) from exc

    if not isinstance(payload, list):
        raise EvaluationDatasetError(
            "Grounding evaluation dataset root must be a JSON array"
        )

    if not payload:
        raise EvaluationDatasetError(
            "Grounding evaluation dataset must contain at least one case"
        )

    cases: list[GroundingCase] = []
    seen_case_ids: set[str] = set()

    for index, raw_case in enumerate(payload):
        if not isinstance(raw_case, dict):
            raise EvaluationDatasetError(
                f"Case {index} must be a JSON object"
            )

        missing = [
            field
            for field in ("id", "query", "answer", "expected_evidence")
            if field not in raw_case
        ]
        if missing:
            raise EvaluationDatasetError(
                f"Case {index} is missing required fields: "
                f"{', '.join(missing)}"
            )

        case_id = _require_non_empty_string(
            raw_case["id"],
            f"case {index} id",
        )

        if case_id in seen_case_ids:
            raise EvaluationDatasetError(
                f"Duplicate case id: {case_id}"
            )
        seen_case_ids.add(case_id)

        query = _require_non_empty_string(
            raw_case["query"],
            f"case {case_id} query",
        )

        answer = _require_non_empty_string(
            raw_case["answer"],
            f"case {case_id} answer",
        )

        raw_evidence = raw_case["expected_evidence"]
        if not isinstance(raw_evidence, list):
            raise EvaluationDatasetError(
                f"Case {case_id} expected_evidence must be a JSON array"
            )

        validated_evidence: list[str] = []
        for pos, item in enumerate(raw_evidence):
            val = _require_non_empty_string(
                item,
                f"case {case_id} expected_evidence[{pos}]",
            )
            validated_evidence.append(val)

        cases.append(
            GroundingCase(
                id=case_id,
                query=query,
                answer=answer,
                expected_evidence=tuple(validated_evidence),
            )
        )

    return cases
