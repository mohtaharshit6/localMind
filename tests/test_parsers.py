"""Tests for parsers module."""
import sys
from pathlib import Path
import tempfile
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from localmind.parsers import parse_file, chunk_text


def test_parse_txt(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Hello World\nThis is a test file.", encoding="utf-8")
    result = parse_file(f)
    assert result is not None
    assert "Hello World" in result
    assert "test file" in result


def test_parse_csv(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("name,age,score\nAlice,25,95\nBob,30,82", encoding="utf-8")
    result = parse_file(f)
    assert result is not None
    assert "name" in result.lower() or "alice" in result.lower()


def test_parse_unsupported():
    result = parse_file("/fake/path/file.xyz")
    assert result is None


def test_chunk_text_small():
    text = "Short text."
    chunks = chunk_text(text, chunk_size=800, overlap=100)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_large():
    text = "Word " * 500  # 2500 chars
    chunks = chunk_text(text, chunk_size=800, overlap=100)
    assert len(chunks) > 1
    # No chunk should be empty
    for chunk in chunks:
        assert chunk.strip()


def test_chunk_text_overlap():
    """Chunks should overlap to preserve context."""
    text = "A" * 400 + "\n\n" + "B" * 400 + "\n\n" + "C" * 400
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) >= 2


def test_parse_pdf_missing_file():
    """Non-existent PDF should return error message not None."""
    result = parse_file("/nonexistent/file.pdf")
    # Should return parse error string (not None) because .pdf is supported
    assert result is not None
    assert "error" in result.lower() or "Error" in result
