"""Tests for auth module."""
import sys
import os
from pathlib import Path
import tempfile
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# Override DB path for tests
_tmpdir = tempfile.mkdtemp()
config.DATA_DIR = Path(_tmpdir)
config.DB_PATH = config.DATA_DIR / "test.db"
config.ACTION_LOG_PATH = config.DATA_DIR / "test_actions.db"

from localmind.auth import (
    authorize_folder, revoke_folder, is_path_authorized,
    get_authorized_folders, validate_destination
)


@pytest.fixture(autouse=True)
def clean_auth(tmp_path):
    """Clean up authorized folders between tests."""
    # Override auth file location
    import localmind.auth as auth_module
    orig_file = auth_module._AUTH_FILE
    auth_module._AUTH_FILE = config.DATA_DIR / "test_auth.json"
    yield
    # Restore
    auth_module._AUTH_FILE = orig_file
    # Remove test auth file
    test_file = config.DATA_DIR / "test_auth.json"
    if test_file.exists():
        test_file.unlink()


def test_authorize_valid_folder(tmp_path):
    ok, msg = authorize_folder(str(tmp_path))
    assert ok, msg
    assert tmp_path.resolve() in get_authorized_folders()


def test_authorize_nonexistent_folder():
    ok, msg = authorize_folder("/nonexistent/path/that/does/not/exist")
    assert not ok


def test_authorize_file_not_folder(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("test")
    ok, msg = authorize_folder(str(f))
    assert not ok


def test_revoke_folder(tmp_path):
    authorize_folder(str(tmp_path))
    ok, msg = revoke_folder(str(tmp_path))
    assert ok
    assert tmp_path.resolve() not in get_authorized_folders()


def test_is_path_authorized(tmp_path):
    authorize_folder(str(tmp_path))
    file_in = tmp_path / "test.txt"
    file_in.write_text("hello")
    assert is_path_authorized(file_in)


def test_path_traversal_blocked(tmp_path):
    """Path traversal attack should be blocked."""
    authorize_folder(str(tmp_path))
    # Try to access parent via traversal
    traversal_path = tmp_path / ".." / "etc" / "passwd"
    # Should not be authorized
    assert not is_path_authorized(traversal_path)


def test_validate_destination_within_authorized(tmp_path):
    authorize_folder(str(tmp_path))
    valid, msg = validate_destination(str(tmp_path / "new_file.txt"))
    assert valid


def test_validate_destination_outside_authorized(tmp_path, tmp_path_factory):
    other = tmp_path_factory.mktemp("other")
    authorize_folder(str(tmp_path))
    valid, msg = validate_destination(str(other / "file.txt"), must_be_in_authorized=True)
    assert not valid
