"""
File Authorization & Security
Manages which folders LocalMind is allowed to access.
Prevents path traversal attacks.
"""
import json
from pathlib import Path
from typing import List, Optional
import config

_AUTH_FILE = config.DATA_DIR / "authorized_folders.json"


def _load_authorized() -> List[str]:
    """Load list of authorized folder paths from persistent storage."""
    if _AUTH_FILE.exists():
        try:
            return json.loads(_AUTH_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_authorized(folders: List[str]) -> None:
    """Persist authorized folder list."""
    _AUTH_FILE.write_text(json.dumps(folders, indent=2), encoding="utf-8")


def get_authorized_folders() -> List[Path]:
    """Return list of authorized folders as resolved Path objects."""
    return [Path(p).resolve() for p in _load_authorized()]


def authorize_folder(folder_path: str) -> tuple[bool, str]:
    """
    Authorize a folder for LocalMind access.
    Returns (success, message).
    """
    try:
        # Strip all surrounding spaces and quotes robustly
        cleaned_path = str(folder_path).strip(' "\'')
        p = Path(cleaned_path)
        resolved = p.resolve()
    except (OSError, ValueError) as e:
        return False, f"Invalid path: {e}"

    if not resolved.exists():
        return False, f"Folder does not exist: {resolved}"
    if not resolved.is_dir():
        return False, f"Path is not a directory: {resolved}"

    current = _load_authorized()
    resolved_str = str(resolved)
    if resolved_str in current:
        return True, f"Folder already authorized: {resolved}"

    current.append(resolved_str)
    _save_authorized(current)
    return True, f"Authorized: {resolved}"


def revoke_folder(folder_path: str) -> tuple[bool, str]:
    """Remove a folder from the authorized list."""
    try:
        cleaned_path = str(folder_path).strip(' "\'')
        resolved = str(Path(cleaned_path).resolve())
    except (OSError, ValueError) as e:
        return False, f"Invalid path: {e}"

    current = _load_authorized()
    if resolved not in current:
        return False, f"Folder not in authorized list."
    current.remove(resolved)
    _save_authorized(current)
    return True, f"Revoked: {resolved}"


def is_path_authorized(file_path: str | Path) -> bool:
    """
    Check whether a given file/folder is within an authorized folder.
    Prevents path traversal attacks.
    """
    try:
        resolved = Path(file_path).resolve()
    except (OSError, ValueError):
        return False

    for auth_folder in get_authorized_folders():
        try:
            resolved.relative_to(auth_folder)
            return True
        except ValueError:
            continue
    return False


def validate_destination(dest: str | Path, must_be_in_authorized: bool = True) -> tuple[bool, str]:
    """
    Validate a destination path for file operations.
    Returns (valid, message).
    """
    try:
        resolved = Path(dest).resolve()
    except (OSError, ValueError) as e:
        return False, f"Invalid destination path: {e}"

    if must_be_in_authorized and not is_path_authorized(resolved):
        return False, f"Destination is outside authorized folders: {resolved}"

    # Check for path traversal attempt
    for auth_folder in get_authorized_folders():
        try:
            resolved.relative_to(auth_folder)
            return True, str(resolved)
        except ValueError:
            continue

    if not must_be_in_authorized:
        return True, str(resolved)

    return False, f"Destination {resolved} is not within any authorized folder."
