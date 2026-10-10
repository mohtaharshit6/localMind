"""
LLM Provider Abstraction
Supports Google Gemini with graceful fallback when unavailable.
"""
import config
from typing import Optional


class LLMUnavailableError(Exception):
    pass


def _get_gemini_model():
    """Initialize and return Gemini model."""
    import os
    import streamlit as st
    from pathlib import Path
    from dotenv import load_dotenv

    # Dynamically load .env so changes take effect without server restart (Local)
    _project_root = Path(config.__file__).parent
    load_dotenv(_project_root / ".env", override=True)
    
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    
    # Check Streamlit Cloud Secrets (Deployed)
    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
        except Exception:
            pass

    if not api_key:
        raise LLMUnavailableError("GEMINI_API_KEY not set in environment or secrets.")
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        return model
    except ImportError:
        raise LLMUnavailableError("google-generativeai package not installed.")
    except Exception as e:
        raise LLMUnavailableError(f"Failed to initialize Gemini: {e}")


def is_llm_available() -> tuple[bool, str]:
    """Check if LLM is available. Returns (available, message)."""
    try:
        _get_gemini_model()
        return True, f"Gemini ({config.GEMINI_MODEL}) ready."
    except LLMUnavailableError as e:
        return False, str(e)


def generate(prompt: str, system_prompt: Optional[str] = None) -> str:
    """
    Generate text using the configured LLM.
    Raises LLMUnavailableError if LLM is not configured.
    """
    model = _get_gemini_model()

    full_prompt = ""
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"
    else:
        full_prompt = prompt

    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        import logging
        logging.error(f"Gemini API Error: {e}")
        raise LLMUnavailableError("AI features are currently unavailable. Please check your Gemini API configuration.")


def answer_question(question: str, context_chunks: list[dict]) -> str:
    """
    Answer a question using retrieved context chunks.
    context_chunks: list of {content, filename, file_path, ...}
    """
    if not context_chunks:
        try:
            return generate(
                f"Answer this question based on your knowledge (no local documents found):\n\n{question}"
            )
        except LLMUnavailableError:
            return "No relevant documents found and no LLM is configured. Please index some files and/or configure your GEMINI_API_KEY."

    # Build context
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        context_parts.append(
            f"[Source {i}: {chunk['filename']}]\n{chunk['content']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are LocalMind, an AI assistant that answers questions based on the user's local files.

Context from local files:
{context}

Question: {question}

Instructions:
- Answer based primarily on the provided context.
- Cite sources by mentioning the filename.
- If the context doesn't fully answer the question, say so clearly.
- Be concise and helpful.

Answer:"""

    return generate(prompt)


def summarize_document(content: str, filename: str) -> str:
    """Generate a summary of a document."""
    # Truncate if too long
    max_chars = 8000
    truncated = content[:max_chars]
    if len(content) > max_chars:
        truncated += f"\n\n[... truncated {len(content) - max_chars} characters ...]"

    prompt = f"""Summarize the following document in a clear, structured way.

Document: {filename}

Content:
{truncated}

Provide:
1. A brief overview (2-3 sentences)
2. Key topics covered
3. Main findings or conclusions (if applicable)
4. Notable details

Summary:"""

    return generate(prompt)


def compare_documents(
    content1: str, filename1: str, content2: str, filename2: str
) -> str:
    """Compare two documents and highlight similarities/differences."""
    max_per_doc = 4000
    c1 = content1[:max_per_doc]
    c2 = content2[:max_per_doc]

    prompt = f"""Compare these two documents and provide a detailed analysis.

Document 1: {filename1}
{c1}

---

Document 2: {filename2}
{c2}

Provide:
1. **Overview**: What each document is about
2. **Similarities**: Key themes, topics, or information they share
3. **Differences**: What makes them distinct (scope, perspective, conclusions, etc.)
4. **Unique to Doc 1**: Information only in {filename1}
5. **Unique to Doc 2**: Information only in {filename2}

Comparison:"""

    return generate(prompt)


def analyze_csv(content: str, filename: str, question: str) -> str:
    """Answer a natural-language question about a CSV file."""
    max_chars = 6000
    truncated_content = content[:max_chars]

    prompt = f"""You are a data analyst. Analyze the following CSV data and answer the question.

File: {filename}
Data:
{truncated_content}

Question: {question}

Provide:
- A direct answer to the question
- Relevant statistics or patterns observed
- Any notable insights from the data

Analysis:"""

    return generate(prompt)


def suggest_revision_plan(content: str, filename: str) -> str:
    """Generate a study/revision plan from notes."""
    max_chars = 6000
    truncated = content[:max_chars]

    prompt = f"""Based on these notes, create a structured revision plan.

Notes from: {filename}

Content:
{truncated}

Create a revision plan including:
1. **Key Topics to Review** (prioritized)
2. **Suggested Study Schedule** (day-by-day if applicable)
3. **Practice Areas** (what to focus on)
4. **Quick Reference Summary** (key points to remember)

Revision Plan:"""

    return generate(prompt)


# ── Supported operations and required fields ───────────────────────────────────
_SUPPORTED_OPS = {"move", "rename", "create", "create_folder"}

_REQUIRED_FIELDS: dict[str, list[str]] = {
    "move":          ["operation", "source", "destination_folder"],
    "rename":        ["operation", "source", "new_name"],
    "create":        ["operation", "destination", "content"],
    "create_folder": ["operation", "destination"],
}

def _validate_plan_item(item: dict, auth_folders: list) -> tuple[bool, str]:
    """
    Validate a single LLM-proposed operation item.
    Returns (valid, reason).
    NEVER trust LLM output — check everything.
    """
    from pathlib import Path
    from localmind.auth import is_path_authorized

    # 1. Must be a dict
    if not isinstance(item, dict):
        return False, "Operation item is not a dict."

    # 2. Must have 'operation' field and it must be supported
    op = item.get("operation", "")
    if op not in _SUPPORTED_OPS:
        return False, f"Unsupported operation: '{op}'. Supported: {sorted(_SUPPORTED_OPS)}"

    # 3. Must have all required fields for this operation
    for field in _REQUIRED_FIELDS[op]:
        if field not in item or item[field] is None:
            return False, f"Missing required field '{field}' for operation '{op}'."

    # 4. Path traversal and authorization checks
    if op in ("move", "rename"):
        src = str(item["source"]).strip()
        # Reject path traversal sequences
        if ".." in src:
            return False, f"Path traversal attempt in source: {src}"
        if not is_path_authorized(src):
            return False, f"Source path is outside authorized folders: {src}"
        # Source must exist
        if not Path(src).exists():
            return False, f"Source file does not exist: {src}"

    if op == "move":
        dst = str(item["destination_folder"]).strip()
        if ".." in dst:
            return False, f"Path traversal attempt in destination: {dst}"
        if not is_path_authorized(dst):
            return False, f"Destination folder is outside authorized folders: {dst}"

    if op == "rename":
        new_name = str(item["new_name"]).strip()
        if "/" in new_name or "\\" in new_name:
            return False, f"new_name cannot contain path separators: {new_name}"
        if ".." in new_name:
            return False, f"Path traversal attempt in new_name: {new_name}"

    if op in ("create", "create_folder"):
        dst = str(item["destination"]).strip()
        if ".." in dst:
            return False, f"Path traversal attempt in destination: {dst}"
        if not is_path_authorized(dst):
            return False, f"Destination is outside authorized folders: {dst}"

    return True, "ok"


def plan_file_operations(
    prompt: str,
    indexed_files: list,
    auth_folders: list,
) -> tuple[list[dict], list[str]]:
    """
    Ask Gemini to interpret a natural-language file-operation request
    and return a list of structured, validated operation dicts.

    Returns:
        (valid_ops, errors)
        valid_ops  - list of validated operation dicts
        errors     - list of human-readable validation error strings
    """
    import json
    import re
    from pathlib import Path

    file_list_text = "(no files indexed yet)"
    if indexed_files:
        lines = []
        for f in indexed_files:
            lines.append(f"  - {f.get('path', '')}  [{f.get('extension', '')}]")
        file_list_text = "\n".join(lines)

    auth_text = "(no authorized folders)"
    if auth_folders:
        auth_text = "\n".join(f"  - {str(a)}" for a in auth_folders)

    system_instructions = f"""You are a file-operation planner for LocalMind, a secure local-file AI assistant.

Your task is to interpret the user's natural-language file-operation request and output a JSON array of structured file operations.

RULES:
1. Output ONLY a valid JSON array — no markdown fences, no explanation text, no commentary.
2. Each element must be one of these operation types:
   - move:          {{"operation": "move",          "source": "<absolute path>", "destination_folder": "<absolute folder path>"}}
   - rename:        {{"operation": "rename",        "source": "<absolute path>", "new_name": "<filename only, no path>"}}
   - create:        {{"operation": "create",        "destination": "<absolute file path>", "content": "<initial text content>"}}
   - create_folder: {{"operation": "create_folder", "destination": "<absolute folder path>"}}
3. Use ONLY paths from the indexed files list and authorized folders below.
4. If you cannot confidently determine a source file's exact path from the indexed list, skip it.
5. If the request is impossible or unclear, return an empty array: []
6. Never invent paths that are not in the indexed files or authorized folders.
7. Never include path traversal sequences (..).

AUTHORIZED FOLDERS:
{auth_text}

INDEXED FILES:
{file_list_text}
"""

    full_prompt = f"{system_instructions}\n\nUSER REQUEST: {prompt}\n\nJSON array:"

    # Call the LLM (raises LLMUnavailableError if unavailable)
    raw = generate(full_prompt)

    # Clean JSON
    cleaned = raw.strip()
    cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\n\nRaw output:\n{raw[:500]}")

    if not isinstance(parsed, list):
        raise ValueError(f"LLM returned non-list JSON (got {type(parsed).__name__})")

    valid_ops: list[dict] = []
    errors: list[str] = []
    seen_sources: set[str] = set()

    for i, item in enumerate(parsed):
        ok, reason = _validate_plan_item(item, auth_folders)
        if not ok:
            errors.append(f"Operation {i+1}: {reason}")
            continue

        src_key = str(item.get("source", "")).lower()
        if src_key and src_key in seen_sources:
            errors.append(f"Operation {i+1}: duplicate source path '{item.get('source')}' — skipped.")
            continue
        if src_key:
            seen_sources.add(src_key)

        valid_ops.append(item)

    return valid_ops, errors
