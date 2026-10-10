"""
Retrieval Engine
Hybrid search: SQLite FTS5 (primary) + optional future vector search.
"""
import re
from pathlib import Path
from typing import Optional
import config
from localmind.db import get_connection, init_db


def _sanitize_fts_query(query: str) -> str:
    """
    Sanitize user input for FTS5.
    Converts natural language queries into an FTS keyword search.
    """
    clean = re.sub(r'["\*\(\)\[\]\{\}\^~\?:\\\/\|]', ' ', query)
    clean = ' '.join(clean.split())
    if not clean:
        return '""'
        
    terms = clean.split()
    
    # Filter out common stop words to improve FTS matching
    stop_words = {"a", "an", "the", "is", "are", "was", "were", "of", "in", "on", "at", 
                  "to", "for", "with", "about", "me", "tell", "give", "i", "have", "what", 
                  "how", "why", "can", "you", "summarize", "summary", "read"}
    meaningful_terms = [t for t in terms if t.lower() not in stop_words]
    
    if not meaningful_terms:
        meaningful_terms = terms
        
    # Search for documents containing ANY of the meaningful keywords
    return " OR ".join([f'"{t}"*' for t in meaningful_terms])


def search_fts(
    query: str,
    top_k: int = None,
    file_extension: Optional[str] = None,
) -> list[dict]:
    """
    Search indexed content using SQLite FTS5.
    Returns list of result dicts with content, filename, file_path, score.
    """
    top_k = top_k or config.MAX_CONTEXT_CHUNKS
    init_db()
    conn = get_connection()
    c = conn.cursor()

    results = []

    try:
        fts_query = _sanitize_fts_query(query)

        sql = """
            SELECT
                c.content,
                f.filename,
                f.path as file_path,
                f.extension,
                bm25(chunks_fts) as score
            FROM chunks_fts
            JOIN chunks ON chunks.file_id = (
                SELECT id FROM files WHERE path = chunks_fts.file_path LIMIT 1
            ) AND chunks.chunk_index = CAST(chunks_fts.chunk_index AS INTEGER)
            JOIN files f ON f.path = chunks_fts.file_path
            WHERE chunks_fts MATCH ?
        """
        params = [fts_query]

        if file_extension:
            ext = file_extension if file_extension.startswith(".") else f".{file_extension}"
            sql += " AND f.extension = ?"
            params.append(ext.lower())

        sql += " ORDER BY score LIMIT ?"
        params.append(top_k)

        rows = c.execute(sql, params).fetchall()
        results = [dict(r) for r in rows]

    except Exception as e:
        # Fall back to simpler LIKE search if FTS fails
        results = _fallback_search(query, top_k, file_extension, c)

    conn.close()
    return results


def _fallback_search(
    query: str,
    top_k: int,
    file_extension: Optional[str],
    cursor,
) -> list[dict]:
    """LIKE-based fallback search when FTS query fails."""
    try:
        terms = query.lower().split()
        conditions = " AND ".join(["LOWER(c.content) LIKE ?" for _ in terms])
        params = [f"%{t}%" for t in terms]

        sql = f"""
            SELECT c.content, f.filename, f.path as file_path, f.extension,
                   0 as score
            FROM chunks c
            JOIN files f ON f.id = c.file_id
            WHERE {conditions}
        """
        if file_extension:
            ext = file_extension if file_extension.startswith(".") else f".{file_extension}"
            sql += f" AND f.extension = '{ext.lower()}'"
        sql += f" LIMIT {top_k}"

        rows = cursor.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def search_by_filename(filename_pattern: str) -> list[dict]:
    """Search for files by filename pattern."""
    init_db()
    conn = get_connection()
    pattern = f"%{filename_pattern}%"
    rows = conn.execute(
        "SELECT path, filename, extension, size_bytes, indexed_at FROM files WHERE filename LIKE ?",
        (pattern,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_file_chunks(file_path: str) -> list[str]:
    """Get all chunks for a specific file."""
    init_db()
    conn = get_connection()
    rows = conn.execute(
        """SELECT c.content FROM chunks c
           JOIN files f ON f.id = c.file_id
           WHERE f.path = ?
           ORDER BY c.chunk_index""",
        (file_path,),
    ).fetchall()
    conn.close()
    return [r["content"] for r in rows]


def get_full_file_content(file_path: str) -> Optional[str]:
    """Retrieve full indexed content for a file by joining chunks."""
    chunks = get_file_chunks(file_path)
    if not chunks:
        return None
    return "\n\n".join(chunks)
