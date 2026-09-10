from hb_bot.messages import chunk_message


def test_chunk_message_preserves_lines_and_limit():
    lines = [f"Сотрудник {index}: " + "я" * 80 for index in range(100)]
    chunks = chunk_message("🎂 Дни рождения", lines, limit=300)

    assert len(chunks) > 1
    assert all(len(chunk) <= 300 for chunk in chunks)
    assert chunks[0].startswith("🎂 Дни рождения")
    assert "\n".join(chunks).count("Сотрудник") == 100


def test_chunk_message_splits_single_oversized_line():
    chunks = chunk_message("", ["x" * 25], limit=10)
    assert chunks == ["x" * 10, "x" * 10, "x" * 5]


def test_chunk_message_splits_oversized_header():
    chunks = chunk_message("h" * 21, [], limit=10)
    assert chunks == ["h" * 10, "h" * 10, "h"]
