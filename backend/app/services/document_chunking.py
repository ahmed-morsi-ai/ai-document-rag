def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> list[str]:
    """Split text into deterministic, overlapping character chunks."""

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0"
        )

    if chunk_overlap < 0:
        raise ValueError(
            "chunk_overlap must be greater than or equal to 0"
        )

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )

    if not text:
        return []

    step = chunk_size - chunk_overlap
    chunks = []
    start = 0

    while start < len(text):
        end = min(
            start + chunk_size,
            len(text),
        )

        chunks.append(text[start:end])

        if end == len(text):
            break

        start += step

    return chunks
