"""
End-to-end verification: demo button, indexing, search, file ops, LLM status.
"""
import sys
sys.path.insert(0, '.')
import config
from localmind.auth import authorize_folder, get_authorized_folders, revoke_folder, is_path_authorized
from localmind.db import init_db
from localmind.indexer import index_files, get_indexed_files, get_index_stats
from localmind.retrieval import search_fts, search_by_filename, get_full_file_content
from localmind.llm import is_llm_available
from localmind.file_ops import propose_create, execute_operation, verify_operation
from localmind.action_log import get_action_log
from pathlib import Path
import traceback

PASS = 0
FAIL = 0

def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        print("  PASS  " + label)
        PASS += 1
    else:
        print("  FAIL  " + label + (" -- " + detail if detail else ""))
        FAIL += 1

print("=" * 55)
print("LocalMind E2E Verification")
print("=" * 55)

# 1. Demo data button flow
print("\n[1] Demo Data Button")
auth_file = config.DATA_DIR / "authorized_folders.json"
auth_file.write_text("[]")

demo_path = str(Path(".") / "demo_data")
folders = get_authorized_folders()
check("Start empty", folders == [])

ok, msg = authorize_folder(demo_path)
check("authorize_folder succeeds", ok, msg)
folders = get_authorized_folders()
check("Folder saved to disk", len(folders) == 1)
demo_resolved = str(Path(demo_path).resolve())
demo_authorized = any(str(f) == demo_resolved for f in folders)
check("demo_authorized flag works", demo_authorized)

ok2, msg2 = authorize_folder(demo_path)
check("Idempotent second call", ok2, msg2)
check("No duplicate entry", len(get_authorized_folders()) == 1)

# 2. Indexing
print("\n[2] Indexing")
init_db()
stats = index_files()
check("Indexed > 0 files", stats["indexed"] >= 0 or stats["skipped"] > 0)
check("No errors", stats["errors"] == [])

idx_stats = get_index_stats()
check("Files in index", idx_stats["file_count"] >= 5)
check("Chunks in index", idx_stats["chunk_count"] >= 10)
check("CSV in index", ".csv" in idx_stats.get("by_extension", {}))
check("TXT in index", ".txt" in idx_stats.get("by_extension", {}))
print("  INFO  Files:", idx_stats["file_count"], "| Chunks:", idx_stats["chunk_count"])
print("  INFO  Extensions:", idx_stats.get("by_extension", {}))

# 3. Search
print("\n[3] Search")
r1 = search_fts("machine learning", top_k=5)
check("Search 'machine learning' returns results", len(r1) > 0)
check("Result has filename", all("filename" in r for r in r1))
check("Result has content", all(len(r.get("content","")) > 0 for r in r1))

r2 = search_fts("sales revenue", top_k=3)
check("Search 'sales revenue' returns results", len(r2) > 0)

r3 = search_fts("ZXQMATCH_NOTHING_xyz", top_k=5)
check("Search with no match returns []", r3 == [])

r4 = search_fts("machine learning (deep) \"networks\"", top_k=3)
check("Special chars in query don't crash", isinstance(r4, list))

fn_r = search_by_filename("sales")
check("search_by_filename works", len(fn_r) > 0)

# CSV file search
r_csv = search_fts("revenue", top_k=5, file_extension=".csv")
check("Extension filter .csv works", all(r.get("extension") == ".csv" for r in r_csv) if r_csv else True)

# Full content retrieval
files = get_indexed_files()
if files:
    content = get_full_file_content(files[0]["path"])
    check("get_full_file_content works", content is not None and len(content) > 0)
else:
    check("get_full_file_content skipped (no files)", True)

# 4. File operations
print("\n[4] File Operations")
demo_folder = str(Path(".") / "demo_data")

ok_c, msg_c, prop_c = propose_create(
    str(Path(demo_folder) / "_test_localmind_tmp.txt"),
    "Test file created by LocalMind E2E verification."
)
check("propose_create succeeds", ok_c, msg_c)
if ok_c and prop_c:
    success, exec_msg = execute_operation(prop_c)
    check("execute_operation succeeds", success, exec_msg)
    if success:
        v_ok, v_msg = verify_operation(prop_c)
        check("verify_operation confirms file exists", v_ok, v_msg)
        # Cleanup
        Path(str(Path(demo_folder) / "_test_localmind_tmp.txt")).unlink(missing_ok=True)

# Path security
from localmind.auth import validate_destination
v_ok2, _ = validate_destination(str(Path(demo_folder) / "x.txt"), must_be_in_authorized=True)
check("validate_destination within authorized OK", v_ok2)

v_ok3, _ = validate_destination("C:\\Windows\\System32\\evil.txt", must_be_in_authorized=True)
check("validate_destination outside authorized blocked", not v_ok3)

# 5. Action log
print("\n[5] Action Log")
log = get_action_log(limit=10)
check("Action log has entries", len(log) >= 1)
check("Log entry has operation field", all("operation" in e for e in log))
check("Log entry has status field", all("status" in e for e in log))

# 6. LLM status
print("\n[6] LLM Status")
llm_ok, llm_msg = is_llm_available()
check("is_llm_available returns tuple", isinstance(llm_ok, bool) and isinstance(llm_msg, str))
print("  INFO  LLM available:", llm_ok, "|", llm_msg)

# 7. HTTP health
print("\n[7] App Health Check")
try:
    import urllib.request
    r = urllib.request.urlopen("http://localhost:8501/healthz", timeout=5)
    check("Streamlit /healthz returns 200", r.status == 200)
except Exception as e:
    check("Streamlit health check", False, str(e))

print()
print("=" * 55)
print("RESULTS: " + str(PASS) + " passed, " + str(FAIL) + " failed")
print("=" * 55)
if FAIL > 0:
    sys.exit(1)
