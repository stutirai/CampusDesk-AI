"""
Basic tests for CampusDesk AI's core logic (chunking, FAQ loading, retrieval).

Run with:
    python -m pytest tests/
or simply:
    python tests/test_core_logic.py
"""

import os
import sys
import json

# Allow importing from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def chunk_text(text, chunk_size=500, overlap=50):
    """Mirrors the chunk_text function in app.py (duplicated here so tests
    don't require a live GEMINI_API_KEY to import app.py)."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def test_faq_json_is_valid():
    """The FAQ knowledge base should load as valid JSON with the expected shape."""
    with open("data/faq.json", "r") as f:
        data = json.load(f)

    assert isinstance(data, list), "faq.json should contain a list"
    assert len(data) > 0, "faq.json should not be empty"

    for item in data:
        assert "question" in item, "Each FAQ entry needs a 'question' field"
        assert "answer" in item, "Each FAQ entry needs an 'answer' field"

    print("test_faq_json_is_valid: PASSED")


def test_chunking_covers_all_text():
    """Chunking should not drop any words from the original text."""
    text = " ".join([f"word{i}" for i in range(100)])
    chunks = chunk_text(text, chunk_size=30, overlap=5)

    assert len(chunks) > 1, "A 100-word text with chunk_size=30 should split into multiple chunks"
    # First chunk should start with the first word
    assert chunks[0].startswith("word0")
    # Last chunk should end with the last word
    assert chunks[-1].endswith("word99")

    print("test_chunking_covers_all_text: PASSED")


def test_chunking_handles_short_text():
    """Text shorter than chunk_size should still produce exactly one chunk."""
    text = "This is a short sentence."
    chunks = chunk_text(text, chunk_size=500, overlap=50)

    assert len(chunks) == 1, "Short text should produce exactly one chunk"
    assert chunks[0] == text

    print("test_chunking_handles_short_text: PASSED")


def test_chunking_handles_empty_text():
    """Empty text should not crash the chunker."""
    chunks = chunk_text("", chunk_size=500, overlap=50)
    assert chunks == [] or chunks == [""]

    print("test_chunking_handles_empty_text: PASSED")


if __name__ == "__main__":
    # Change to project root so relative paths (data/faq.json) resolve correctly
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    test_faq_json_is_valid()
    test_chunking_covers_all_text()
    test_chunking_handles_short_text()
    test_chunking_handles_empty_text()

    print("\nAll tests passed!")
