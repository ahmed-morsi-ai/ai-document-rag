from dataclasses import dataclass
import re
from typing import Sequence


class GroundingEvaluationError(ValueError):
    """Raised when grounding evaluation input is invalid."""


@dataclass(frozen=True)
class GroundingEvaluationResult:
    matched_count: int
    expected_count: int
    coverage: float


def normalize_evidence(text: str) -> str:
    if not isinstance(text, str):
        raise GroundingEvaluationError("evidence must be a string")

    return re.sub(r"\s+", " ", text.strip()).casefold()


def evaluate_grounding(
    expected_evidence: Sequence[str],
    source_texts: Sequence[str],
) -> GroundingEvaluationResult:
    normalized_expected: list[str] = []
    seen: set[str] = set()

    for evidence in expected_evidence:
        normalized = normalize_evidence(evidence)

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        normalized_expected.append(normalized)

    combined_sources = " ".join(
        normalize_evidence(source)
        for source in source_texts
        if isinstance(source, str)
    )

    if not normalized_expected:
        return GroundingEvaluationResult(
            matched_count=0,
            expected_count=0,
            coverage=1.0,
        )

    matched_count = sum(
        1
        for evidence in normalized_expected
        if evidence in combined_sources
    )

    return GroundingEvaluationResult(
        matched_count=matched_count,
        expected_count=len(normalized_expected),
        coverage=matched_count / len(normalized_expected),
    )
