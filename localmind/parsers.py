"""
Document Parsers
Extracts text content from PDF, DOCX, TXT, and CSV files.
"""
import io
import csv as csv_module
from pathlib import Path
from typing import Optional
import config


def parse_file(file_path: str | Path) -> Optional[str]:
    """
    Parse a file and return its text content.
    Returns None if the file type is unsupported or parsing fails.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    parsers = {
        ".pdf": _parse_pdf,
        ".docx": _parse_docx,
        ".txt": _parse_txt,
        ".csv": _parse_csv,
    }

    parser = parsers.get(suffix)
    if parser is None:
        return None

    try:
        return parser(path)
    except Exception as e:
        return f"[Parse error: {e}]"


def _parse_pdf(path: Path) -> str:
    """Extract text from PDF using PyMuPDF."""
    import fitz  # PyMuPDF
    doc = fitz.open(str(path))
    pages = []
    for page_num, page in enumerate(doc, 1):
        text = page.get_text("text")
        if text.strip():
            pages.append(f"[Page {page_num}]\n{text.strip()}")
    doc.close()
    return "\n\n".join(pages) if pages else "[Empty PDF]"


def _parse_docx(path: Path) -> str:
    """Extract text from DOCX using python-docx."""
    from docx import Document
    doc = Document(str(path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    # Also extract table content
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                paragraphs.append(row_text)
    return "\n\n".join(paragraphs) if paragraphs else "[Empty DOCX]"


def _parse_txt(path: Path) -> str:
    """Read plain text file with encoding detection."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return "[Could not decode text file]"


def _parse_csv(path: Path) -> str:
    """Parse CSV and return a structured text representation."""
    import pandas as pd
    try:
        df = pd.read_csv(str(path))
        lines = []
        lines.append(f"CSV File: {path.name}")
        lines.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
        lines.append(f"Columns: {', '.join(str(c) for c in df.columns)}")
        lines.append("")
        # Include first 50 rows as text
        lines.append(df.head(50).to_string(index=False))
        # Add basic stats for numeric columns
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            lines.append("\nNumeric Summary:")
            lines.append(df[numeric_cols].describe().to_string())
        return "\n".join(lines)
    except Exception as e:
        return f"[CSV parse error: {e}]"


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list[str]:
    """
    Split text into overlapping chunks for indexing.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        # Try to break at a paragraph/sentence boundary
        if end < len(text):
            last_para = chunk.rfind("\n\n")
            last_newline = chunk.rfind("\n")
            last_period = chunk.rfind(". ")
            boundary = max(last_para, last_newline, last_period)
            if boundary > chunk_size // 2:
                end = start + boundary + 1
                chunk = text[start:end]

        chunks.append(chunk.strip())
        start = end - overlap

    return [c for c in chunks if c.strip()]
