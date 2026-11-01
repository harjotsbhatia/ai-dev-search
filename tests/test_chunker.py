import pytest

from app.rag.chunker import chunk_text


def test_empty_text_gives_no_chunks():
    assert chunk_text("   ") == []


def test_short_text_is_one_chunk():
    assert chunk_text("hello world") == ["hello world"]


def test_long_text_is_split_with_overlap():
    text = "".join(str(i % 10) for i in range(2000))
    chunks = chunk_text(text, chunk_size=800, overlap=100)
    assert all(len(c) <= 800 for c in chunks)
    assert chunks[0][-100:] == chunks[1][:100]
    # Every character is covered
    assert chunks[-1].endswith(text[-50:])


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=10, overlap=10)
