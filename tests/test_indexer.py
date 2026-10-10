"""Tests for indexer module."""
import sys
from pathlib import Path
import tempfile
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# Use temp DB for tests
_tmpdir = tempfile.mkdtemp()
config.DATA_DIR = Path(_tmpdir)
config.DB_PATH = config.DATA_DIR / "test_index.db"
config.ACTION_LOG_PATH = config.DATA_DIR / "test_actions.db"
config.DATA_DIR.mkdir(parents=True, exist_ok=True)

from localmind.db import init_db
from localmind.indexer import index_files, get_indexed_files, get_index_stats, discover_files
from localmind.auth import authorize_folder


@pytest.fixture
def demo_folder(tmp_path):
    """Create a temp folder with sample files."""
    (tmp_path / "notes.txt").write_text(
        "Machine learning is a subset of artificial intelligence. "
        "It enables systems to learn from data.", encoding="utf-8"
    )
    (tmp_path / "data.csv").write_text(
        "name,score\nAlice,95\nBob,82\nCarol,88", encoding="utf-8"
    )
    (tmp_path / "hidden.xyz").write_text("ignored", encoding="utf-8")
    authorize_folder(str(tmp_path))
    return tmp_path


def test_discover_files(demo_folder):
    files = list(discover_files([demo_folder]))
    names = [f.name for f in files]
    assert "notes.txt" in names
    assert "data.csv" in names
    assert "hidden.xyz" not in names  # Unsupported extension


def test_index_files(demo_folder):
    init_db()
    stats = index_files([demo_folder])
    assert stats["indexed"] >= 2
    assert stats["errors"] == []


def test_get_indexed_files(demo_folder):
    init_db()
    index_files([demo_folder])
    files = get_indexed_files()
    assert len(files) >= 2
    names = [f["filename"] for f in files]
    assert "notes.txt" in names


def test_get_index_stats(demo_folder):
    init_db()
    index_files([demo_folder])
    stats = get_index_stats()
    assert stats["file_count"] >= 2
    assert stats["chunk_count"] >= 2


def test_skip_unchanged(demo_folder):
    init_db()
    stats1 = index_files([demo_folder])
    stats2 = index_files([demo_folder])  # Second run should skip unchanged files
    assert stats2["skipped"] >= 2
    assert stats2["indexed"] == 0
