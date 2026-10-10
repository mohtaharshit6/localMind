"""Tests for agentic file operations and LLM planning."""
import sys
import json
from pathlib import Path
import tempfile
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from localmind.auth import authorize_folder, revoke_folder
import localmind.llm as llm
from localmind.file_ops import (
    propose_move, propose_rename, propose_create, propose_create_folder,
    execute_operation, verify_operation
)
from localmind.action_log import init_db

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path):
    config.DATA_DIR = tmp_path / "data"
    config.DATA_DIR.mkdir()
    config.DB_PATH = config.DATA_DIR / "test.db"
    init_db()
    
    import localmind.auth as auth_module
    orig_file = auth_module._AUTH_FILE
    auth_module._AUTH_FILE = config.DATA_DIR / "auth.json"
    
    yield tmp_path
    
    auth_module._AUTH_FILE = orig_file

def test_plan_valid_move(monkeypatch, setup_test_env):
    auth_folder = setup_test_env / "workspace"
    auth_folder.mkdir()
    authorize_folder(str(auth_folder))
    
    src = auth_folder / "old.txt"
    src.write_text("content")
    dst = auth_folder / "Archive"
    
    def mock_generate(prompt):
        return json.dumps([{
            "operation": "move",
            "source": str(src),
            "destination_folder": str(dst)
        }])
    
    monkeypatch.setattr(llm, "generate", mock_generate)
    
    valid_ops, errors = llm.plan_file_operations("Move old.txt to Archive", [], [auth_folder])
    assert len(valid_ops) == 1
    assert len(errors) == 0
    assert valid_ops[0]["operation"] == "move"
    assert valid_ops[0]["source"] == str(src)

def test_plan_path_traversal_blocked(monkeypatch, setup_test_env):
    auth_folder = setup_test_env / "workspace"
    auth_folder.mkdir()
    authorize_folder(str(auth_folder))
    
    def mock_generate(prompt):
        return json.dumps([{
            "operation": "create",
            "destination": str(auth_folder / ".." / "evil.txt"),
            "content": "evil"
        }])
    
    monkeypatch.setattr(llm, "generate", mock_generate)
    
    valid_ops, errors = llm.plan_file_operations("Hack!", [], [auth_folder])
    assert len(valid_ops) == 0
    assert len(errors) == 1
    assert "Path traversal attempt" in errors[0]

def test_plan_unauthorized_path_blocked(monkeypatch, setup_test_env):
    auth_folder = setup_test_env / "workspace"
    auth_folder.mkdir()
    authorize_folder(str(auth_folder))
    
    unauthorized = setup_test_env / "secret"
    unauthorized.mkdir()
    
    def mock_generate(prompt):
        return json.dumps([{
            "operation": "create_folder",
            "destination": str(unauthorized / "new_folder")
        }])
    
    monkeypatch.setattr(llm, "generate", mock_generate)
    
    valid_ops, errors = llm.plan_file_operations("Create folder in secret", [], [auth_folder])
    assert len(valid_ops) == 0
    assert len(errors) == 1
    assert "outside authorized folders" in errors[0]

def test_execute_create_folder(setup_test_env):
    auth_folder = setup_test_env / "workspace"
    auth_folder.mkdir()
    authorize_folder(str(auth_folder))
    
    new_folder = auth_folder / "MyDocs"
    ok, msg, prop = propose_create_folder(str(new_folder))
    assert ok
    
    # Execute
    success, e_msg = execute_operation(prop)
    assert success
    assert new_folder.exists() and new_folder.is_dir()
    
    # Verify
    v_ok, v_msg = verify_operation(prop)
    assert v_ok
