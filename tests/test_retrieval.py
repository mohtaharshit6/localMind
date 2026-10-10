"""Tests for retrieval module."""
import sys
from pathlib import Path
import tempfile
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

_tmpdir = tempfile.mkdtemp()
config.DATA_DIR = Path(_tmpdir)
config.DB_PATH = config.DATA_DIR / "test_retrieval.db"
config.ACTION_LOG_PATH = config.DATA_DIR / "test_actions.db"
config.DATA_DIR.mkdir(parents=True, exist_ok=True)

from localmind.db import init_db
from localmind.indexer import index_files
from localmind.retrieval import search_fts, search_by_filename, get_full_file_content
from localmind.auth import authorize_folder


@pytest.fixture(scope="module")
def indexed_folder(tmp_path_factory):
    folder = tmp_path_factory.mktemp("search_test")
    (folder / "ml_notes.txt").write_text(
        "Neural networks are inspired by the human brain. "
        "Deep learning uses many layers of neurons. "
        "Gradient descent optimizes the loss function.",
        encoding="utf-8"
    )
    (folder / "sales.csv").write_text(
        "product,revenue\nLaptop,50000\nPhone,30000\nTablet,20000",
        encoding="utf-8"
    )
    authorize_folder(str(folder))
    init_db()
    index_files([folder])
    return folder


def test_search_finds_content(indexed_folder):
    results = search_fts("neural networks", top_k=5)
    assert len(results) > 0
    assert any("ml_notes.txt" in r["filename"] for r in results)


def test_search_returns_content(indexed_folder):
    results = search_fts("gradient descent", top_k=3)
    assert len(results) > 0
    for r in results:
        assert "content" in r
        assert len(r["content"]) > 0


def test_search_by_filename(indexed_folder):
    results = search_by_filename("ml_notes")
    assert len(results) > 0
    assert results[0]["filename"] == "ml_notes.txt"


def test_search_with_extension_filter(indexed_folder):
    csv_results = search_fts("laptop revenue", top_k=5, file_extension=".csv")
    for r in csv_results:
        assert r["extension"] == ".csv"


def test_get_full_content(indexed_folder):
    files = search_by_filename("ml_notes")
    if files:
        content = get_full_file_content(files[0]["path"])
        assert content is not None
        assert "neural" in content.lower()


def test_search_no_results(indexed_folder):
    results = search_fts("zxqjklmnopqrstuvwxyz_no_match_at_all", top_k=5)
    assert results == []


def test_search_special_chars(indexed_folder):
    """Special characters in query should not crash search."""
    results = search_fts('neural "networks" (deep)', top_k=5)
    # Should not raise, may return results or empty list
    assert isinstance(results, list)
