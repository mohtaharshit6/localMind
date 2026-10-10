"""
File Indexer
Discovers and indexes files in authorized folders using SQLite FTS5.
"""
import os
import time
from pathlib import Path
from typing import Iterator, Callable, Optional
import config
from localmind.db import get_connection, init_db
from localmind.parsers import parse_file, chunk_text
from localmind.auth import get_authorized_folders, is_path_authorized


def discover_files(folders: list[Path] = None) -> Iterator[Path]:
    """Yield all supported files in authorized (or given) folders."""
    folders = folders or get_authorized_folders()
    for folder in folders:
        if not folder.exists():
            continue
        for root, dirs, files in os.walk(folder):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in files:
                fpath = Path(root) / fname
                if fpath.suffix.lower() in config.SUPPORTED_EXTENSIONS:
                    if is_path_authorized(fpath):
                        yield fpath


def index_files(
    folders: list[Path] = None,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    force_reindex: bool = False,
) -> dict:
    """
    Index all files in authorized folders.
    Returns stats dict.
    """
    init_db()
    conn = get_connection()
    c = conn.cursor()

    files = list(discover_files(folders))
    total = len(files)
    indexed = 0
    skipped = 0
    errors = []

    for i, fpath in enumerate(files):
        if progress_callback:
            progress_callback(str(fpath.name), i + 1, total)

        try:
            stat = fpath.stat()
            size = stat.st_size

            # Check if already indexed and unchanged (by size)
            if not force_reindex:
                row = c.execute(
                    "SELECT id, size_bytes FROM files WHERE path = ?", (str(fpath),)
                ).fetchone()
                if row and row["size_bytes"] == size:
                    skipped += 1
                    continue

            # Parse file content
            content = parse_file(fpath)
            if content is None:
                errors.append(f"Unsupported: {fpath.name}")
                continue

            # Remove old entry
            c.execute("DELETE FROM files WHERE path = ?", (str(fpath),))

            # Insert file record
            c.execute(
                """INSERT INTO files (path, filename, extension, size_bytes)
                   VALUES (?, ?, ?, ?)""",
                (str(fpath), fpath.name, fpath.suffix.lower(), size),
            )
            file_id = c.lastrowid

            # Chunk and index
            chunks = chunk_text(content)
            for chunk_idx, chunk in enumerate(chunks):
                # Store chunk
                c.execute(
                    "INSERT INTO chunks (file_id, chunk_index, content) VALUES (?, ?, ?)",
                    (file_id, chunk_idx, chunk),
                )
                # Index in FTS
                c.execute(
                    "INSERT INTO chunks_fts (content, filename, file_path, chunk_index) VALUES (?, ?, ?, ?)",
                    (chunk, fpath.name, str(fpath), chunk_idx),
                )

            # Update chunk count
            c.execute(
                "UPDATE files SET chunk_count = ? WHERE id = ?",
                (len(chunks), file_id),
            )

            conn.commit()
            indexed += 1

        except Exception as e:
            errors.append(f"{fpath.name}: {e}")
            conn.rollback()

    conn.close()
    return {"total": total, "indexed": indexed, "skipped": skipped, "errors": errors}


def get_indexed_files() -> list[dict]:
    """Return all indexed files as list of dicts."""
    init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT path, filename, extension, size_bytes, indexed_at, chunk_count FROM files ORDER BY filename"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def remove_file_from_index(file_path: str) -> bool:
    """Remove a file from the index."""
    conn = get_connection()
    c = conn.cursor()
    row = c.execute("SELECT id FROM files WHERE path = ?", (file_path,)).fetchone()
    if row:
        c.execute("DELETE FROM files WHERE id = ?", (row["id"],))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def get_index_stats() -> dict:
    """Return index statistics."""
    init_db()
    conn = get_connection()
    file_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    ext_counts = conn.execute(
        "SELECT extension, COUNT(*) as cnt FROM files GROUP BY extension"
    ).fetchall()
    conn.close()
    return {
        "file_count": file_count,
        "chunk_count": chunk_count,
        "by_extension": {r["extension"]: r["cnt"] for r in ext_counts},
    }
