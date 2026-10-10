"""
Safe File Operations
Implements create, rename, and move operations with mandatory confirmation
and post-operation verification.

NEVER modifies files without explicit user confirmation.
"""
import shutil
from pathlib import Path
from typing import Optional
from localmind.auth import is_path_authorized, validate_destination
from localmind.action_log import log_action, update_action_status


class FileOperationProposal:
    """Represents a proposed file operation awaiting confirmation."""

    def __init__(
        self,
        operation: str,
        source: str,
        destination: Optional[str] = None,
        new_name: Optional[str] = None,
        content: Optional[str] = None,
    ):
        self.operation = operation  # "move", "rename", "create"
        self.source = source
        self.destination = destination
        self.new_name = new_name
        self.content = content
        self.log_id: Optional[int] = None

    def describe(self) -> str:
        """Human-readable description of the proposed operation."""
        if self.operation == "move":
            return f"Move `{Path(self.source).name}` → `{self.destination}`"
        elif self.operation == "rename":
            return f"Rename `{Path(self.source).name}` → `{self.new_name}`"
        elif self.operation == "create":
            preview = (self.content or "")[:100]
            return f"Create file `{self.destination}`\nContent preview: {preview}..."
        elif self.operation == "create_folder":
            return f"Create folder `{self.destination}`"
        return f"{self.operation}: {self.source}"


def propose_move(source: str, destination_folder: str) -> tuple[bool, str, Optional[FileOperationProposal]]:
    """
    Propose moving a file to a destination folder.
    Returns (valid, message, proposal).
    """
    src_path = Path(source)
    if not src_path.exists():
        return False, f"Source file does not exist: {source}", None
    if not is_path_authorized(src_path):
        return False, f"Source is not in an authorized folder: {source}", None

    valid, msg = validate_destination(destination_folder, must_be_in_authorized=True)
    if not valid:
        return False, msg, None

    dest_folder = Path(destination_folder)
    if not dest_folder.exists():
        return False, f"Destination folder does not exist: {destination_folder}", None

    dest_path = dest_folder / src_path.name
    if dest_path.exists():
        return False, f"A file with that name already exists at destination: {dest_path}", None

    proposal = FileOperationProposal(
        operation="move",
        source=str(src_path.resolve()),
        destination=str(dest_path),
    )
    return True, f"Ready to move `{src_path.name}` to `{dest_folder}`", proposal


def propose_rename(source: str, new_name: str) -> tuple[bool, str, Optional[FileOperationProposal]]:
    """
    Propose renaming a file.
    Returns (valid, message, proposal).
    """
    src_path = Path(source)
    if not src_path.exists():
        return False, f"Source file does not exist: {source}", None
    if not is_path_authorized(src_path):
        return False, f"Source is not in an authorized folder: {source}", None

    # Validate new name (no path separators)
    if "/" in new_name or "\\" in new_name:
        return False, "New name cannot contain path separators.", None

    dest_path = src_path.parent / new_name
    if dest_path.exists():
        return False, f"A file named '{new_name}' already exists in that folder.", None

    proposal = FileOperationProposal(
        operation="rename",
        source=str(src_path.resolve()),
        destination=str(dest_path),
        new_name=new_name,
    )
    return True, f"Ready to rename `{src_path.name}` → `{new_name}`", proposal


def propose_create(destination: str, content: str) -> tuple[bool, str, Optional[FileOperationProposal]]:
    """
    Propose creating a new file.
    Returns (valid, message, proposal).
    """
    valid, msg = validate_destination(destination, must_be_in_authorized=True)
    if not valid:
        return False, msg, None

    dest_path = Path(destination)
    if dest_path.exists():
        return False, f"File already exists: {destination}", None

    proposal = FileOperationProposal(
        operation="create",
        source="",
        destination=str(dest_path),
        content=content,
    )
    return True, f"Ready to create `{dest_path.name}`", proposal


def propose_create_folder(destination: str) -> tuple[bool, str, Optional[FileOperationProposal]]:
    """
    Propose creating a new folder.
    Returns (valid, message, proposal).
    """
    valid, msg = validate_destination(destination, must_be_in_authorized=True)
    if not valid:
        return False, msg, None

    dest_path = Path(destination)
    if dest_path.exists():
        return False, f"Path already exists: {destination}", None

    proposal = FileOperationProposal(
        operation="create_folder",
        source="",
        destination=str(dest_path),
    )
    return True, f"Ready to create folder `{dest_path.name}`", proposal



def execute_operation(proposal: FileOperationProposal) -> tuple[bool, str]:
    """
    Execute a confirmed file operation.
    Returns (success, message).
    """
    log_id = log_action(
        operation=proposal.operation,
        source_path=proposal.source,
        destination_path=proposal.destination,
        status="executing",
    )
    proposal.log_id = log_id

    try:
        if proposal.operation == "move":
            result = _execute_move(proposal)
        elif proposal.operation == "rename":
            result = _execute_rename(proposal)
        elif proposal.operation == "create":
            result = _execute_create(proposal)
        elif proposal.operation == "create_folder":
            result = _execute_create_folder(proposal)
        else:
            raise ValueError(f"Unknown operation: {proposal.operation}")

        success, message = result
        status = "completed" if success else "failed"
        update_action_status(log_id, status, message)
        return success, message

    except Exception as e:
        msg = f"Operation failed: {e}"
        update_action_status(log_id, "error", msg)
        return False, msg


def _execute_move(proposal: FileOperationProposal) -> tuple[bool, str]:
    """Execute a move operation."""
    src = Path(proposal.source)
    dest = Path(proposal.destination)

    if not src.exists():
        return False, f"Source no longer exists: {src}"

    shutil.move(str(src), str(dest))

    # Verify
    if dest.exists() and not src.exists():
        return True, f"✅ Moved successfully: `{src.name}` → `{dest.parent}`"
    else:
        return False, f"Verification failed: move may not have completed correctly."


def _execute_rename(proposal: FileOperationProposal) -> tuple[bool, str]:
    """Execute a rename operation."""
    src = Path(proposal.source)
    dest = Path(proposal.destination)

    if not src.exists():
        return False, f"Source no longer exists: {src}"

    src.rename(dest)

    # Verify
    if dest.exists() and not src.exists():
        return True, f"✅ Renamed successfully: `{src.name}` → `{dest.name}`"
    else:
        return False, "Verification failed: rename may not have completed correctly."


def _execute_create(proposal: FileOperationProposal) -> tuple[bool, str]:
    """Execute a file creation operation."""
    dest = Path(proposal.destination)

    # Ensure parent directory exists
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(proposal.content or "", encoding="utf-8")

    # Verify
    if dest.exists():
        return True, f"✅ Created successfully: `{dest.name}`"
    else:
        return False, "Verification failed: file creation may not have completed."


def _execute_create_folder(proposal: FileOperationProposal) -> tuple[bool, str]:
    """Execute a folder creation operation."""
    dest = Path(proposal.destination)

    dest.mkdir(parents=True, exist_ok=True)

    # Verify
    if dest.exists() and dest.is_dir():
        return True, f"✅ Folder created successfully: `{dest.name}`"
    else:
        return False, "Verification failed: folder creation may not have completed."


def verify_operation(proposal: FileOperationProposal) -> tuple[bool, str]:
    """Post-hoc verification of a completed operation."""
    if proposal.operation in ("move", "rename"):
        dest = Path(proposal.destination)
        if dest.exists():
            return True, f"Verified: `{dest.name}` exists at `{dest.parent}`"
        return False, f"Verification failed: `{proposal.destination}` not found."
    elif proposal.operation in ("create", "create_folder"):
        dest = Path(proposal.destination)
        if dest.exists():
            return True, f"Verified: `{dest.name}` exists."
        return False, f"Verification failed: `{proposal.destination}` not found."
    return False, "Unknown operation type for verification."
