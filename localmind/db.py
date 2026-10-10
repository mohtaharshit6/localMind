"""
SQLite Database Setup
Initializes all database tables for LocalMind.
"""
import sqlite3
from pathlib import Path
import config


def get_connection(db_path: Path = None) -> sqlite3.Connection:
    """Get a SQLite connection with WAL mode and row factory."""
    db_path = db_path or config.DB_PATH
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path = None) -> None:
    """Initialize all LocalMind database tables."""
    conn = get_connection(db_path)
    c = conn.cursor()

    # Files registry
    c.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            extension TEXT NOT NULL,
            size_bytes INTEGER,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            chunk_count INTEGER DEFAULT 0
        )
    """)

    # Full-text search table (FTS5)
    c.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            content,
            filename,
            file_path,
            chunk_index,
            content='',
            tokenize='porter unicode61'
        )
    """)

    # Chunks storage (for retrieving actual content)
    c.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
        )
    """)

    # Action log
    c.execute("""
        CREATE TABLE IF NOT EXISTS action_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            operation TEXT NOT NULL,
            source_path TEXT,
            destination_path TEXT,
            status TEXT NOT NULL,
            details TEXT
        )
    """)

    conn.commit()
    conn.close()
