from __future__ import annotations


def chunk_message(header: str, lines: list[str], *, limit: int = 4096) -> list[str]:
    """Split text on line boundaries without exceeding Telegram's limit."""

    if limit <= 0:
        raise ValueError("limit must be positive")

    pieces: list[str] = []
    normalized_header = header.strip()
    pieces.extend(
        normalized_header[index : index + limit]
        for index in range(0, len(normalized_header), limit)
    )
    for line in lines:
        if not line:
            pieces.append("")
            continue
        pieces.extend(line[index : index + limit] for index in range(0, len(line), limit))

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        separator = "\n" if current else ""
        if len(current) + len(separator) + len(piece) <= limit:
            current += separator + piece
            continue
        if current:
            chunks.append(current)
        current = piece
    if current:
        chunks.append(current)
    return chunks or ([header] if header else [])
