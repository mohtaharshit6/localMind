"""
Action Log
Records all file operations (create, rename, move) with status tracking.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
import config
from localmind.db import get_connection, init_db


def log_action(
    operation: str,
    source_path: str,
    destination_path: str = None,
    status: str = "pending",
    details: str = None,
) -> int:
    """
    Log a file operation. Returns the log entry ID.
    """
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO action_log (operation, source_path, destination_path, status, details)
           VALUES (?, ?, ?, ?, ?)""",
        (operation, source_path, destination_path, status, details),
    )
    log_id = c.lastrowid
    conn.commit()
    conn.close()
    return log_id


def update_action_status(log_id: int, status: str, details: str = None) -> None:
    """Update the status of a logged action."""
    init_db()
    conn = get_connection()
    conn.execute(
        "UPDATE action_log SET status = ?, details = ? WHERE id = ?",
        (status, details, log_id),
    )
    conn.commit()
    conn.close()


def get_action_log(limit: int = 100) -> list[dict]:
    """Retrieve the action log."""
    init_db()
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, timestamp, operation, source_path, destination_path, status, details
           FROM action_log
           ORDER BY timestamp DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_action_log() -> None:
    """Clear all action log entries."""
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM action_log")
    conn.commit()
    conn.close()
