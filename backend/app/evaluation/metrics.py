from dataclasses import dataclass
from typing import Sequence


def chunk_key(document_id: str, chunk_index: int) -> str:
    if not isinstance(document_id, str) or not document_id.strip():
        raise ValueError("document_id must be a non-empty string")

    if isinstance(chunk_index, bool) or not isinstance(chunk_index, int):
        raise ValueError("chunk_index must be an integer")

    if chunk_index < 0:
        raise ValueError("chunk_index must be greater than or equal to 0")

    return f"{document_id}:{chunk_index}"


def _validate_k(k: int) -> int:
    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        raise ValueError("k must be greater than 0")
    return k


def _unique_top_k(
    retrieved_chunk_ids: Sequence[str],
    k: int,
) -> list[str]:
    _validate_k(k)

    # K applies to the actual retrieval positions first.
    # Duplicates are then removed so repeated IDs cannot inflate metrics.
    top_k = retrieved_chunk_ids[:k]

    unique: list[str] = []
    seen: set[str] = set()

    for chunk_id in top_k:
        if chunk_id in seen:
            continue

        seen.add(chunk_id)
        unique.append(chunk_id)

    return unique


def recall_at_k(
    relevant_chunk_ids: Sequence[str],
    retrieved_chunk_ids: Sequence[str],
    k: int,
) -> float:
    _validate_k(k)

    relevant = set(relevant_chunk_ids)

    # Undefined recall is made explicit as 0.0 when no target exists.
    if not relevant:
        return 0.0

    retrieved = set(_unique_top_k(retrieved_chunk_ids, k))
    return len(relevant & retrieved) / len(relevant)


def precision_at_k(
    relevant_chunk_ids: Sequence[str],
    retrieved_chunk_ids: Sequence[str],
    k: int,
) -> float:
    _validate_k(k)

    retrieved = _unique_top_k(retrieved_chunk_ids, k)

    # Undefined precision for no retrieved evidence is explicit as 0.0.
    if not retrieved:
        return 0.0

    relevant = set(relevant_chunk_ids)
    return len(relevant & set(retrieved)) / len(retrieved)


def hit_rate_at_k(
    relevant_chunk_ids: Sequence[str],
    retrieved_chunk_ids: Sequence[str],
    k: int,
) -> float:
    _validate_k(k)

    relevant = set(relevant_chunk_ids)
    if not relevant:
        return 0.0

    retrieved = set(_unique_top_k(retrieved_chunk_ids, k))
    return 1.0 if relevant & retrieved else 0.0


@dataclass(frozen=True)
class EvaluationMetrics:
    recall_at_k: float
    precision_at_k: float
    hit_rate_at_k: float


def calculate_metrics(
    cases,
    retrieved_by_case: dict[str, Sequence[str]],
    k: int,
) -> EvaluationMetrics:
    if not cases:
        raise ValueError("cases must not be empty")

    _validate_k(k)

    recalls = []
    precisions = []
    hit_rates = []

    for case in cases:
        retrieved = retrieved_by_case.get(case.id, [])

        recalls.append(
            recall_at_k(
                case.relevant_chunk_ids,
                retrieved,
                k,
            )
        )
        precisions.append(
            precision_at_k(
                case.relevant_chunk_ids,
                retrieved,
                k,
            )
        )
        hit_rates.append(
            hit_rate_at_k(
                case.relevant_chunk_ids,
                retrieved,
                k,
            )
        )

    # Dataset aggregation is macro-averaged:
    # every evaluation case contributes equally.
    return EvaluationMetrics(
        recall_at_k=sum(recalls) / len(recalls),
        precision_at_k=sum(precisions) / len(precisions),
        hit_rate_at_k=sum(hit_rates) / len(hit_rates),
    )
