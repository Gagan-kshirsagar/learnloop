from app.modules.tutor.internal.chunker import MarkdownChunker, estimate_token_count


def test_estimate_token_count() -> None:
    assert estimate_token_count("") == 0
    assert estimate_token_count("Hello world") >= 2
    assert estimate_token_count("def is_palindrome(s: str) -> bool:\n    return s == s[::-1]") > 10


def test_chunker_short_text_single_chunk() -> None:
    chunker = MarkdownChunker(target_tokens=500, overlap_tokens=60)
    short_text = "# Introduction\n\nThis is a short lesson on Python functions."
    chunks = chunker.chunk_document(short_text)

    assert len(chunks) == 1
    assert chunks[0].ordinal == 0
    assert chunks[0].content == short_text
    assert chunks[0].token_count > 0


def test_chunker_long_text_splits_with_overlap() -> None:
    chunker = MarkdownChunker(target_tokens=50, overlap_tokens=15)
    long_paragraphs = [
        f"## Section {i}\n\nThis is a detailed paragraph for topic {i} explaining "
        "computational complexity and algorithm analysis in depth with multiple sentences."
        for i in range(10)
    ]
    full_text = "\n\n".join(long_paragraphs)
    chunks = chunker.chunk_document(full_text)

    assert len(chunks) > 1
    # Verify ordinals are sequential starting from 0
    for i, c in enumerate(chunks):
        assert c.ordinal == i
        assert len(c.content) > 0
        assert c.token_count > 0
