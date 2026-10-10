# 🧠 LocalMind — AI Personal Assistant for Local Files

> **Agentic AI assistant that understands your local documents. Search, summarize, compare, and safely manage your files — all locally, powered by Google Gemini.**

---

## ✨ Features

| Feature | Description |
|---|---|
| 📁 **Folder Authorization** | Authorize specific folders — LocalMind only accesses what you allow |
| 🔍 **Full-Text Search** | SQLite FTS5 with BM25 ranking over all indexed files |
| 💬 **Natural Language Q&A** | Ask questions, get answers with source citations |
| 📄 **Document Summarization** | One-click summaries and revision plans |
| ⚖️ **Document Comparison** | Side-by-side comparison of any two documents |
| 📊 **CSV Analysis** | Ask natural-language questions about your data |
| 🗂️ **Safe File Operations** | Create, rename, move files — with mandatory confirmation |
| ✅ **Operation Verification** | Every file operation is verified after execution |
| 📋 **Action Log** | Complete audit trail of all file operations |
| 🔒 **Security First** | Path traversal prevention, no unauthorized file access |

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/LocalMind.git
cd LocalMind
pip install -r requirements.txt
```

### 2. Configure (Optional — app works without API key)

```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

Get a free Gemini API key at [ai.google.dev](https://ai.google.dev)

### 3. Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

## 📖 Usage Guide

### Step 1: Authorize a Folder
- Click **"➕ Add Demo Data Folder"** in the sidebar to start with sample files
- Or enter any folder path to authorize it

### Step 2: Index Files
- Click **"📥 Index"** to discover and index all PDF, DOCX, TXT, CSV files
- Unchanged files are skipped automatically on subsequent indexing

### Step 3: Use the Features

**💬 Chat & Search:**
```
"What are the main machine learning algorithms?"
"Find files about sales data"
"What does the research paper say about deep learning?"
```

**📄 Summarize:** Select any indexed document and generate an AI summary

**⚖️ Compare:** Choose two documents to get a detailed comparison

**📊 CSV Analysis:**
```
"What is the best performing region?"
"Show me revenue trends over time"
"Which product has the highest profit margin?"
```

**🗂️ File Operations:**
1. Choose an operation (Move/Rename/Create)
2. Configure source and destination
3. Click "Propose" to see the plan
4. **Confirm** or **Cancel** — files are NEVER modified without confirmation

---

## 🏗️ Architecture

```
LocalMind/
├── app.py                    # Streamlit UI
├── config.py                 # Configuration & env vars
├── localmind/
│   ├── auth.py               # Folder authorization & path security
│   ├── parsers.py            # PDF/DOCX/TXT/CSV content extraction
│   ├── db.py                 # SQLite database setup
│   ├── indexer.py            # File discovery & FTS5 indexing
│   ├── retrieval.py          # Search engine (FTS5 + fallback)
│   ├── llm.py                # Gemini LLM abstraction
│   ├── file_ops.py           # Safe file operations with confirmation
│   └── action_log.py        # Operation audit logging
├── demo_data/                # Sample files for demo
└── tests/                    # Unit tests
```

### Key Design Decisions

- **SQLite FTS5**: Zero-dependency full-text search with BM25 ranking. Works offline, no vector server needed.
- **Graceful LLM fallback**: App fully functions without an API key. Search, indexing, and raw content display work without Gemini.
- **Security-first**: All paths resolved and validated against authorized folders. No path traversal possible.
- **Confirmation-required ops**: File modifications use a two-step proposal + confirmation workflow.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📋 Supported File Types

| Extension | Parser |
|---|---|
| `.pdf` | PyMuPDF (fitz) |
| `.docx` | python-docx |
| `.txt` | Native Python (UTF-8/Latin-1) |
| `.csv` | pandas |

---

## 🔒 Security

- Only folders you explicitly authorize are ever accessed
- All file paths are resolved and validated against the authorized list
- Path traversal attacks are blocked
- API keys are loaded from `.env`, never hardcoded
- No file is ever modified without explicit user confirmation
- Every operation is verified and logged

---

## ⚠️ Limitations

- No real-time file watching (manual re-index required after file changes)
- Large PDFs (>100MB) may take longer to parse
- LLM features require a valid Gemini API key
- No semantic/vector search in MVP (FTS5 provides good results for most queries)

---

## 🛠️ Tech Stack

- **UI**: Streamlit
- **Search**: SQLite FTS5 (built-in)
- **PDF**: PyMuPDF
- **DOCX**: python-docx
- **CSV**: pandas
- **LLM**: Google Gemini (via google-generativeai)
- **Config**: python-dotenv

---

*Built as a college project MVP demonstrating agentic AI for local file understanding.*
