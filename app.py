"""
LocalMind — Main Streamlit Application
Design inspired by the Magic Patterns reference (void/surface/jade palette, Inter+JetBrains Mono,
sidebar-main-context layout, staged file-op flow, source cards).
All Python backend functionality preserved unchanged.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path
import sys, time

sys.path.insert(0, str(Path(__file__).parent))

import config
from localmind.auth import get_authorized_folders, authorize_folder, revoke_folder
from localmind.indexer import index_files, get_indexed_files, get_index_stats
from localmind.retrieval import search_fts, search_by_filename, get_full_file_content
from localmind.llm import (
    is_llm_available, answer_question, summarize_document,
    compare_documents, analyze_csv, suggest_revision_plan, LLMUnavailableError,
    plan_file_operations,
)
from localmind.file_ops import (
    propose_move, propose_rename, propose_create, propose_create_folder,
    execute_operation, verify_operation,
)
from localmind.action_log import get_action_log, clear_action_log

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LocalMind",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Design tokens (faithful to tailwind.config.js) ─────────────────────────
# Surfaces
VOID        = "#08090A"
SURFACE     = "#0E1011"
SURFACE_R   = "#14171A"   # raised
SURFACE_H   = "#1B1F23"   # high
SURFACE_HV  = "#22272C"   # hover
# Ink
INK         = "#E9ECEF"
INK_DIM     = "#9AA1A9"
INK_FAINT   = "#6A7178"
INK_GHOST   = "#484E55"
# Jade (primary accent)
JADE_100    = "#D3F7EA"
JADE_300    = "#6EE7BE"
JADE_400    = "#35D6A4"
JADE_500    = "#16C08C"
JADE_700    = "#0A6E51"
JADE_900    = "#093428"
# Semantic
DANGER_400  = "#FF8078"
DANGER_500  = "#F4655B"
DANGER_900  = "#3A1614"
WARN_400    = "#EFBB63"
WARN_500    = "#E3A94B"
WARN_900    = "#3A2A11"
INFO_400    = "#7FB4F7"
INFO_500    = "#6BA8F5"
INFO_900    = "#152538"

# ─── Full CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300..700;1,14..32,300..700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset ── */
html, body, [class*="css"] {{
  font-family: 'Inter', ui-sans-serif, system-ui, sans-serif !important;
  font-size: 13.5px;
  line-height: 21px;
  color: {INK};
}}

/* ── App wash ── */
.stApp {{
  background-color: {SURFACE};
  background-image:
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(22,192,140,0.055) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 100%, rgba(22,192,140,0.025) 0%, transparent 50%);
  min-height: 100vh;
}}

/* ── Hide chrome: do NOT hide the header element itself —
   it controls sidebar layout in Streamlit 1.55.
   Instead surgically hide only the children we don't want. ── */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
.stDeployButton {{ display: none !important; }}

/* Hide the running/stop indicator and share button inside the toolbar,
   but NOT the sidebar toggle button */
[data-testid="stToolbar"] {{
  /* Make the toolbar itself invisible but keep it in the layout
     so the sidebar toggle still works */
  visibility: hidden;
}}
/* Un-hide the sidebar collapse/toggle button inside the toolbar */
[data-testid="stToolbar"] [data-testid="stSidebarNavToggle"],
[data-testid="stToolbar"] button[kind="header"],
[data-testid="collapsedControl"] {{
  visibility: visible !important;
  display: flex !important;
}}

/* ── Sidebar — always visible, correct width ── */
[data-testid="stSidebar"] {{
  background-color: {SURFACE_R} !important;
  border-right: 1px solid rgba(255,255,255,0.06) !important;
  /* Fixed width — override Streamlit's dynamic sizing */
  min-width: 260px !important;
  max-width: 260px !important;
  /* Force it to always be visible (expanded state) */
  transform: none !important;
  visibility: visible !important;
  display: flex !important;
  flex-shrink: 0 !important;
}}
/* Inner scroll container */
[data-testid="stSidebar"] > div:first-child {{
  padding: 0 !important;
  min-width: 260px !important;
  max-width: 260px !important;
}}
/* The collapsed-control — keep visible so user can reopen the sidebar.
   JS will restyle it to look like a hamburger ☰. */
[data-testid="collapsedControl"] {{
  display: flex !important;
}}

/* Sidebar nav section (page links) — hide since we use tabs */
[data-testid="stSidebarNav"] {{
  display: none !important;
}}

/* ── Tabs as topbar nav ── */
[data-testid="stTabs"] [role="tablist"] {{
  background: {SURFACE_R};
  border-bottom: 1px solid rgba(255,255,255,0.06);
  padding: 0 1.5rem;
  gap: 0;
  overflow-x: auto;
}}
[data-testid="stTabs"] [role="tab"] {{
  color: {INK_FAINT} !important;
  font-size: 11.5px !important;
  font-weight: 500 !important;
  letter-spacing: 0.01em !important;
  padding: 0.65rem 1rem !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  border-radius: 0 !important;
  background: transparent !important;
  transition: color 0.15s, border-color 0.15s !important;
  white-space: nowrap;
}}
[data-testid="stTabs"] [role="tab"]:hover {{
  color: {INK_DIM} !important;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
  color: {INK} !important;
  border-bottom-color: {JADE_400} !important;
  background: transparent !important;
}}
[data-testid="stTabs"] [role="tabpanel"] {{
  padding: 0 !important;
}}

/* ── Inputs ── */
[data-testid="stTextInput"] > div > div > input,
[data-testid="stTextArea"] textarea {{
  background-color: {SURFACE_H} !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  border-radius: 8px !important;
  color: {INK} !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 13.5px !important;
  padding: 0.55rem 2.2rem 0.55rem 0.85rem !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.03) !important;
  transition: border-color 0.15s, box-shadow 0.15s !important;
}}
[data-testid="stTextInput"] > div > div > input:focus,
[data-testid="stTextArea"] textarea:focus {{
  border-color: {JADE_500}60 !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.03), 0 0 0 2px {JADE_500}22 !important;
  outline: none !important;
}}
[data-testid="stTextInput"] > div > div > input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {{
  color: {INK_GHOST} !important;
}}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {{
  background-color: {SURFACE_H} !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  border-radius: 8px !important;
  color: {INK} !important;
  font-size: 13.5px !important;
}}
[data-testid="stSelectbox"] svg {{ color: {INK_FAINT} !important; }}

/* ── Buttons ── */
.stButton > button {{
  background-color: {SURFACE_H} !important;
  border: none !important;
  border-radius: 8px !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08) !important;
  color: {INK} !important;
  font-size: 12.5px !important;
  font-weight: 500 !important;
  font-family: 'Inter', sans-serif !important;
  height: 2.25rem !important;
  padding: 0 0.875rem !important;
  transition: background-color 0.15s, color 0.15s, box-shadow 0.15s !important;
}}
.stButton > button:hover {{
  background-color: {SURFACE_HV} !important;
  color: {INK} !important;
}}
.stButton > button:active {{
  transform: translateY(1px) !important;
}}
.stButton > button[kind="primary"] {{
  background-color: {JADE_500} !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.16), 0 6px 18px -8px rgba(22,192,140,0.65) !important;
  color: {VOID} !important;
  font-weight: 600 !important;
}}
.stButton > button[kind="primary"]:hover {{
  background-color: {JADE_400} !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.16), 0 8px 24px -8px rgba(22,192,140,0.75) !important;
}}

/* ── Expanders ── */
[data-testid="stExpander"] {{
  background-color: {SURFACE_R} !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 10px !important;
  overflow: hidden;
}}
[data-testid="stExpander"] details > summary {{
  color: {INK_DIM} !important;
  font-size: 12.5px !important;
  font-weight: 500 !important;
  padding: 0.6rem 0.85rem !important;
}}
[data-testid="stExpander"] details > summary:hover {{
  color: {INK} !important;
}}
[data-testid="stExpander"] details[open] > summary {{
  border-bottom: 1px solid rgba(255,255,255,0.05);
}}

/* ── Metrics ── */
[data-testid="stMetric"] {{
  background-color: {SURFACE_R};
  border-radius: 10px;
  padding: 0.9rem 1.1rem !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06);
}}
[data-testid="stMetricLabel"] {{
  color: {INK_GHOST} !important;
  font-size: 10px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
}}
[data-testid="stMetricValue"] {{
  color: {INK} !important;
  font-size: 22px !important;
  font-weight: 600 !important;
  letter-spacing: -0.02em !important;
}}

/* ── Alerts ── */
.stAlert {{
  border-radius: 8px !important;
}}
.stSuccess > div {{
  background: rgba(22,192,140,0.08) !important;
  border: 1px solid rgba(22,192,140,0.2) !important;
  border-radius: 8px !important;
  color: {JADE_300} !important;
}}
.stWarning > div {{
  background: rgba(227,169,75,0.08) !important;
  border: 1px solid rgba(227,169,75,0.2) !important;
  border-radius: 8px !important;
  color: {WARN_400} !important;
}}
.stError > div {{
  background: rgba(244,101,91,0.08) !important;
  border: 1px solid rgba(244,101,91,0.2) !important;
  border-radius: 8px !important;
  color: {DANGER_400} !important;
}}
.stInfo > div {{
  background: rgba(107,168,245,0.08) !important;
  border: 1px solid rgba(107,168,245,0.18) !important;
  border-radius: 8px !important;
  color: {INFO_400} !important;
}}

/* ── Progress ── */
[data-testid="stProgress"] > div {{
  background: rgba(255,255,255,0.06) !important;
  border-radius: 100px;
  height: 3px !important;
}}
[data-testid="stProgress"] > div > div {{
  background: {JADE_400} !important;
  border-radius: 100px;
  transition: width 0.3s cubic-bezier(0.23,1,0.32,1);
}}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
  border-radius: 10px !important;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.06) !important;
}}

/* ── Slider ── */
[data-testid="stSlider"] > div > div > div {{
  background-color: {JADE_500} !important;
}}
[data-testid="stSlider"] [role="slider"] {{
  background-color: {JADE_400} !important;
  border-color: {JADE_400} !important;
  box-shadow: 0 0 0 3px {JADE_900} !important;
}}

/* ── Radio / Checkbox ── */
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label {{
  color: {INK_DIM} !important;
  font-size: 12.5px !important;
}}

/* ── Multiselect ── */
[data-testid="stMultiSelect"] > div {{
  background: {SURFACE_H} !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  border-radius: 8px !important;
}}
.stMultiSelect [data-baseweb="tag"] {{
  background: {JADE_900} !important;
  color: {JADE_300} !important;
}}

/* ── Labels ── */
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label {{
  color: {INK_GHOST} !important;
  font-size: 10px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  margin-bottom: 0.3rem !important;
}}

/* ── Caption ── */
.stCaption, [data-testid="stCaptionContainer"] p {{
  color: {INK_GHOST} !important;
  font-size: 11px !important;
}}

/* ── Divider ── */
hr {{
  border: none !important;
  border-top: 1px solid rgba(255,255,255,0.06) !important;
  margin: 0.85rem 0 !important;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.18); }}

/* ═══════════════════════════════════════════════
   LocalMind Custom Components
   ═══════════════════════════════════════════════ */

/* ── Sidebar wrapper ── */
.lm-sidebar-wrap {{
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0;
}}

/* ── Logo ── */
.lm-logo {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 1.25rem 1rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  margin-bottom: 0;
}}
.lm-logo-mark {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  border-radius: 8px;
  background: {JADE_900};
  box-shadow: inset 0 0 0 1px rgba(53,214,164,0.24);
  color: {JADE_300};
  flex-shrink: 0;
}}
.lm-logo-mark svg {{
  width: 16px; height: 16px;
}}
.lm-logo-text {{ display: flex; flex-direction: column; line-height: 1; }}
.lm-logo-name {{
  font-size: 14.5px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: {INK};
}}
.lm-logo-sub {{
  margin-top: 2px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: {INK_GHOST};
}}

/* ── Sidebar nav ── */
.lm-nav {{
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 0.6rem 0.6rem;
}}
.lm-nav-item {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0.4rem 0.7rem;
  border-radius: 7px;
  font-size: 12.5px;
  font-weight: 500;
  color: {INK_FAINT};
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
  text-decoration: none;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  line-height: 1;
}}
.lm-nav-item:hover {{ background: rgba(255,255,255,0.04); color: {INK_DIM}; }}
.lm-nav-item.active {{
  background: rgba(53,214,164,0.08);
  color: {JADE_300};
  box-shadow: inset 1px 0 0 0 {JADE_400}60;
}}
.lm-nav-dot {{
  width: 6px; height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.55;
  flex-shrink: 0;
}}

/* ── Sidebar section label ── */
.lm-sec {{
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: {INK_GHOST};
  padding: 0 1rem;
  margin: 0.85rem 0 0.4rem;
}}

/* ── Folder item ── */
.lm-folder {{
  display: flex;
  align-items: flex-start;
  gap: 7px;
  padding: 0.45rem 0.7rem;
  border-radius: 7px;
  margin: 0 0.35rem 0.25rem;
  background: rgba(255,255,255,0.02);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.05);
}}
.lm-folder-icon {{ font-size: 12px; margin-top: 1px; flex-shrink: 0; }}
.lm-folder-body {{ min-width: 0; flex: 1; }}
.lm-folder-name {{
  font-size: 12px; font-weight: 500; color: {INK_DIM};
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.lm-folder-path {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px; color: {INK_GHOST};
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin-top: 1px;
}}
.lm-folder-badge {{
  display: inline-block;
  font-size: 9px; font-weight: 600;
  background: {JADE_900}; color: {JADE_400};
  border-radius: 3px; padding: 1px 4px;
  margin-left: 4px; vertical-align: middle;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase; letter-spacing: 0.06em;
}}

/* ── Index stat box ── */
.lm-stat-box {{
  background: rgba(255,255,255,0.02);
  border-radius: 8px;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.05);
  padding: 0.65rem 0.85rem;
  margin: 0 0.6rem;
}}
.lm-stat-row {{
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.22rem 0;
}}
.lm-stat-label {{ font-size: 11px; color: {INK_GHOST}; }}
.lm-stat-val {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px; font-weight: 500; color: {INK_DIM};
}}
.lm-ext-pills {{ display: flex; flex-wrap: wrap; gap: 3px; margin-top: 0.45rem; }}
.lm-ext-pill {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px; text-transform: uppercase;
  background: {JADE_900}; color: {JADE_400};
  border-radius: 3px; padding: 1px 5px;
  letter-spacing: 0.05em;
}}

/* ── LLM status ── */
.lm-llm-row {{
  display: flex; align-items: center; gap: 6px;
  padding: 0 1rem 0.5rem;
  font-size: 11.5px;
}}
.lm-dot {{
  width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
}}
.lm-dot-jade {{ background: {JADE_400}; box-shadow: 0 0 5px {JADE_400}; }}
.lm-dot-ghost {{ background: {INK_GHOST}; }}
.lm-dot-warn {{ background: {WARN_400}; }}
.lm-llm-name {{ color: {INK_DIM}; }}
.lm-llm-sub {{ color: {INK_GHOST}; font-size: 10px; font-family: 'JetBrains Mono', monospace; }}

/* ── Add folder button in sidebar ── */
.lm-add-folder-btn button {{
  background: transparent !important;
  border: 1px dashed rgba(255,255,255,0.1) !important;
  border-radius: 7px !important;
  box-shadow: none !important;
  color: {INK_GHOST} !important;
  font-size: 11.5px !important;
  height: 2rem !important;
  justify-content: flex-start !important;
  padding: 0 0.7rem !important;
  width: 100% !important;
}}
.lm-add-folder-btn button:hover {{
  border-color: {JADE_500}50 !important;
  color: {JADE_300} !important;
  background: {JADE_900}40 !important;
}}

/* ── Sidebar index buttons — two equal-width buttons side by side ── */
.lm-index-btn-row {{
  display: flex;
  gap: 6px;
  padding: 0 0.6rem;
  margin-top: 0.4rem;
}}
.lm-index-btn-row button {{
  flex: 1 1 0 !important;
  height: 32px !important;
  min-height: 32px !important;
  max-height: 32px !important;
  padding: 0 0.5rem !important;
  font-size: 12px !important;
  justify-content: center !important;
  border-radius: 7px !important;
  white-space: nowrap;
}}


/* ── Hamburger toggle buttons — only elements JS has stamped data-lm-ham="1" ── */
/* JS sets this attribute ONLY on the native Streamlit collapse/expand buttons. */
button[data-lm-ham="1"] {{
  width: 34px !important;
  height: 34px !important;
  min-width: 34px !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  background: {SURFACE_H} !important;
  border: 1px solid rgba(255,255,255,0.09) !important;
  border-radius: 8px !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.35) !important;
  color: {INK_DIM} !important;
  padding: 0 !important;
  cursor: pointer !important;
  outline: none !important;
  transition: background 0.15s !important;
}}
button[data-lm-ham="1"]:hover {{
  background: {SURFACE_HV} !important;
  color: {INK} !important;
}}
/* collapsedControl wrapper positioning */
[data-testid="collapsedControl"] {{
  padding: 8px !important;
}}




/* ── Top area / page header ── */
.lm-page-header {{
  padding: 1.5rem 2rem 0.75rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  margin-bottom: 0;
}}
.lm-page-title {{
  font-size: 21px;
  font-weight: 600;
  letter-spacing: -0.015em;
  color: {INK};
  margin: 0;
}}
.lm-page-sub {{
  font-size: 13px;
  color: {INK_FAINT};
  margin-top: 2px;
}}

/* ── Content padding ── */
.lm-content {{
  padding: 1.5rem 2rem;
  max-width: 900px;
}}
.lm-content-wide {{
  padding: 1.5rem 2rem;
}}

/* ── Chat / ask area ── */
.lm-messages {{
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding: 1.5rem 2rem;
  max-width: 840px;
  margin: 0 auto;
  width: 100%;
}}

/* User message ── right aligned */
.lm-msg-user {{
  display: flex;
  justify-content: flex-end;
}}
.lm-msg-user-bubble {{
  background: {SURFACE_H};
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
  border-radius: 16px 16px 4px 16px;
  padding: 0.6rem 1rem;
  max-width: 76%;
  font-size: 14px;
  line-height: 1.6;
  color: {INK};
}}

/* Assistant message ── left with brain mark */
.lm-msg-ai {{
  display: flex;
  gap: 10px;
  align-items: flex-start;
}}
.lm-brain-mark {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  border-radius: 8px;
  background: {JADE_900};
  box-shadow: inset 0 0 0 1px rgba(53,214,164,0.2);
  color: {JADE_300};
  flex-shrink: 0;
  margin-top: 1px;
}}
.lm-brain-mark svg {{ width: 15px; height: 15px; }}
.lm-msg-ai-body {{ flex: 1; min-width: 0; }}
.lm-msg-ai-text {{
  font-size: 14px; line-height: 1.7;
  color: {INK_DIM};
}}
.lm-msg-ai-text p {{ margin: 0 0 0.6rem; color: {INK}; }}
.lm-msg-ai-text p:last-child {{ margin-bottom: 0; color: {INK_DIM}; }}

/* ── Source section header ── */
.lm-src-header {{
  display: flex; align-items: center; gap: 8px;
  margin: 1rem 0 0.5rem;
}}
.lm-src-label {{
  font-size: 10px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: {INK_FAINT};
}}
.lm-src-line {{
  flex: 1; height: 1px;
  background: rgba(255,255,255,0.06);
}}

/* ── Source card ── */
.lm-source-card {{
  background: {SURFACE_R};
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 6px;
  transition: background 0.15s;
}}
.lm-source-card:hover {{ background: {SURFACE_H}; }}
.lm-source-card-header {{
  display: flex; align-items: center; gap: 8px;
  padding: 0.5rem 0.65rem;
  cursor: pointer;
}}
.lm-src-num {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; color: {INK_GHOST};
  width: 14px; text-align: center; flex-shrink: 0;
}}
.lm-file-icon {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 20px; height: 20px; border-radius: 5px; flex-shrink: 0;
  font-size: 9px; font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
}}
.lm-file-icon-pdf   {{ background: {DANGER_900}; color: {DANGER_400}; }}
.lm-file-icon-docx  {{ background: {INFO_900}; color: {INFO_400}; }}
.lm-file-icon-csv   {{ background: {JADE_900}70; color: {JADE_300}; }}
.lm-file-icon-txt   {{ background: rgba(255,255,255,0.05); color: {INK_DIM}; }}
.lm-src-name {{
  flex: 1; min-width: 0;
}}
.lm-src-fname {{
  font-size: 12px; font-weight: 500; color: {INK_DIM};
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.lm-src-path {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px; color: {INK_GHOST};
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.lm-src-evidence {{
  background: {VOID}90;
  margin: 0 0.4rem 0.4rem;
  border-radius: 6px;
  padding: 0.5rem 0.65rem;
  display: flex; gap: 6px;
}}
.lm-quote-icon {{ color: {JADE_700}; font-size: 10px; margin-top: 1px; flex-shrink: 0; }}
.lm-src-excerpt {{
  font-size: 11.5px; line-height: 1.55; color: {INK_DIM};
  font-style: italic;
}}

/* ── Empty state ── */
.lm-empty {{
  background: {SURFACE_R}60;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06);
  border-radius: 12px;
  padding: 1.75rem 1.5rem;
  display: flex; flex-direction: column;
  align-items: flex-start; gap: 6px;
}}
.lm-empty-icon {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: 8px;
  background: rgba(255,255,255,0.04); color: {INK_FAINT};
  font-size: 15px; margin-bottom: 4px;
}}
.lm-empty-title {{
  font-size: 14.5px; font-weight: 500; color: {INK};
}}
.lm-empty-body {{
  font-size: 13px; color: {INK_FAINT};
  max-width: 400px; line-height: 1.6;
}}

/* ── Composer box ── */
.lm-composer {{
  background: {SURFACE_R};
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 0.1rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3), inset 0 0 0 1px rgba(255,255,255,0.04);
}}
.lm-composer-hint {{
  text-align: center;
  font-size: 11px; color: {INK_GHOST};
  margin-top: 0.5rem;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.03em;
}}

/* ── Prompt suggestion chips ── */
.lm-chips {{
  display: flex; flex-wrap: wrap; gap: 6px;
  margin-top: 0.5rem;
}}
.lm-chip {{
  display: inline-flex; align-items: center;
  background: {SURFACE_R};
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.07);
  border-radius: 7px;
  padding: 0.3rem 0.7rem;
  font-size: 12px; color: {INK_DIM};
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}}
.lm-chip:hover {{ background: {SURFACE_H}; color: {INK}; }}

/* ── Section label ── */
.lm-section-label {{
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 0.6rem;
}}
.lm-section-label h3 {{
  font-size: 10px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: {INK_FAINT}; margin: 0;
}}

/* ── Panel / card ── */
.lm-panel {{
  background: {SURFACE_R};
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06);
  border-radius: 12px;
  padding: 1.1rem 1.25rem;
  margin-bottom: 0.75rem;
}}
.lm-panel-title {{
  font-size: 10px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: {INK_GHOST}; margin-bottom: 0.75rem;
}}

/* ── Proposal / file-op stage card ── */
.lm-stage-card {{
  background: {SURFACE_R};
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.07);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  margin: 1rem 0;
}}
.lm-stage-header {{
  display: flex; align-items: center; gap: 8px; margin-bottom: 1rem;
}}
.lm-stage-title {{
  font-size: 14.5px; font-weight: 600; color: {INK};
}}
/* Stage steps */
.lm-steps {{ display: flex; align-items: center; gap: 0; margin-bottom: 1.25rem; }}
.lm-step {{
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; font-weight: 500; color: {INK_GHOST};
}}
.lm-step.active {{ color: {JADE_300}; }}
.lm-step.done {{ color: {JADE_500}; }}
.lm-step-num {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px;
  border-radius: 50%;
  background: rgba(255,255,255,0.05);
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px; font-weight: 600;
}}
.lm-step.active .lm-step-num {{
  background: {JADE_900}; color: {JADE_300};
  box-shadow: inset 0 0 0 1px {JADE_500}40;
}}
.lm-step.done .lm-step-num {{
  background: {JADE_900}; color: {JADE_400};
}}
.lm-step-arrow {{
  width: 24px; height: 1px;
  background: rgba(255,255,255,0.08);
  margin: 0 2px;
}}
/* Change row */
.lm-change-row {{
  display: flex; align-items: flex-start; gap: 10px;
  padding: 0.65rem 0.85rem;
  background: {VOID}60; border-radius: 8px; margin-bottom: 0.4rem;
  font-size: 12px;
}}
.lm-change-from {{
  color: {INK_GHOST}; text-decoration: line-through;
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  flex: 1; min-width: 0; word-break: break-all;
}}
.lm-change-arrow {{ color: {INK_GHOST}; flex-shrink: 0; margin-top: 1px; }}
.lm-change-to {{
  color: {INK_DIM};
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  flex: 1; min-width: 0; word-break: break-all;
}}
/* Verified card */
.lm-verified {{
  background: rgba(22,192,140,0.06);
  box-shadow: inset 0 0 0 1px rgba(22,192,140,0.18);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin: 0.75rem 0;
}}
.lm-verified-title {{
  font-size: 13.5px; font-weight: 500; color: {JADE_300};
}}
.lm-verified-sub {{
  font-size: 12.5px; color: {INK_DIM}; margin-top: 4px;
}}

/* ── Activity / log timeline ── */
.lm-timeline {{
  position: relative;
  padding-left: 0;
  list-style: none; margin: 0;
}}
.lm-timeline::before {{
  content: '';
  position: absolute;
  left: 13px; top: 8px;
  height: calc(100% - 1.5rem);
  width: 1px;
  background: rgba(255,255,255,0.06);
}}
.lm-tl-item {{
  display: flex; align-items: flex-start; gap: 12px;
  padding: 0.6rem 0.5rem;
  border-radius: 8px;
  transition: background 0.12s;
  position: relative;
}}
.lm-tl-item:hover {{ background: rgba(255,255,255,0.025); }}
.lm-tl-icon {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 27px; height: 27px; border-radius: 8px;
  flex-shrink: 0;
  position: relative; z-index: 1;
  font-size: 12px;
}}
.lm-tl-icon-idx  {{ background: {INFO_900}; color: {INFO_400}; }}
.lm-tl-icon-move {{ background: {WARN_900}; color: {WARN_400}; }}
.lm-tl-icon-ren  {{ background: {WARN_900}; color: {WARN_400}; }}
.lm-tl-icon-create {{ background: {WARN_900}; color: {WARN_400}; }}
.lm-tl-icon-ok   {{ background: {JADE_900}70; color: {JADE_300}; }}
.lm-tl-icon-err  {{ background: {DANGER_900}; color: {DANGER_400}; }}
.lm-tl-body {{ flex: 1; min-width: 0; }}
.lm-tl-title {{
  font-size: 13.5px; font-weight: 500; color: {INK};
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.lm-tl-detail {{
  font-size: 12.5px; color: {INK_FAINT}; margin-top: 1px;
  word-break: break-all;
}}
.lm-tl-time {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 10.5px; color: {INK_GHOST};
  flex-shrink: 0; margin-top: 3px;
}}
.lm-badge {{
  display: inline-flex; align-items: center;
  height: 20px; border-radius: 5px;
  padding: 0 6px;
  font-size: 11px; font-weight: 500;
  vertical-align: middle;
}}
.lm-badge-neutral  {{ background: rgba(255,255,255,0.05); color: {INK_DIM}; }}
.lm-badge-jade     {{ background: {JADE_900}70; color: {JADE_300}; }}
.lm-badge-warn     {{ background: {WARN_900}; color: {WARN_400}; }}
.lm-badge-danger   {{ background: {DANGER_900}; color: {DANGER_400}; }}
.lm-badge-info     {{ background: {INFO_900}; color: {INFO_400}; }}
</style>
""", unsafe_allow_html=True)


# ─── Brain mark SVG ─────────────────────────────────────────────────────────
BRAIN_SVG = """<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M12 4.2v15.6M12 4.2c-1.1-1.3-3.1-1.5-4.4-.4-.9.8-1.2 2-.8 3.1-1.4.3-2.4 1.5-2.4 3 0 .9.4 1.8 1 2.4-.7.6-1.1 1.5-1.1 2.5 0 1.9 1.6 3.4 3.5 3.4.6 0 1.2-.2 1.7-.5.5.8 1.4 1.3 2.5 1.3M12 4.2c1.1-1.3 3.1-1.5 4.4-.4.9.8 1.2 2 .8 3.1 1.4.3 2.4 1.5 2.4 3 0 .9-.4 1.8-1 2.4.7.6 1.1 1.5 1.1 2.5 0 1.9-1.6 3.4-3.5 3.4-.6 0-1.2-.2-1.7-.5-.5.8-1.4 1.3-2.5 1.3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
  <path d="M9 8.4h1.6M9 12h1.6M9.4 15.6H11M13 9.6h1.8M13.4 13.2H15" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" opacity="0.55"/>
</svg>"""


# ─── Session state ───────────────────────────────────────────────────────────
def _init():
    for k, v in {
        "chat_history": [],
        "pending_proposal": None,
        "sidebar_msg": None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v
_init()


# ─── Hamburger: restyle Streamlit's native collapse buttons as ☰ ─────────────
# Streamlit already has working collapse/expand buttons (the << and >>).
# We just replace their inner SVG with 3 plain horizontal bars.
# CSS (above) hides the native SVG; this JS injects the bar spans.
# window.parent is required — components.html() runs inside an iframe.
components.html("""
<script>
(function () {
  var doc = window.parent.document;
  var win = window.parent;

  /* Three horizontal bars ☰ */
  var BARS =
    '<span style="display:block;width:15px;height:1.8px;background:currentColor;' +
           'border-radius:1px;margin:2.6px auto;pointer-events:none"></span>' +
    '<span style="display:block;width:15px;height:1.8px;background:currentColor;' +
           'border-radius:1px;margin:2.6px auto;pointer-events:none"></span>' +
    '<span style="display:block;width:15px;height:1.8px;background:currentColor;' +
           'border-radius:1px;margin:2.6px auto;pointer-events:none"></span>';

  function applyHamburger() {
    /* ── 1. The << collapse button inside the open sidebar ── */
    var sidebar = doc.querySelector('[data-testid="stSidebar"]');
    if (sidebar) {
      sidebar.querySelectorAll('button').forEach(function (btn) {
        if (btn.getAttribute('data-lm-ham') === '1') return;

        /* CRITICAL: only touch buttons that contain an SVG.
           Streamlit's collapse arrow is SVG-only.
           User buttons (Index, Add folder, etc.) contain TEXT — skip them. */
        if (!btn.querySelector('svg')) return;

        btn.innerHTML = BARS;
        btn.setAttribute('data-lm-ham', '1');
      });
    }

    /* ── 2. The >> expand button shown when sidebar is collapsed ── */
    var ctrl = doc.querySelector('[data-testid="collapsedControl"]');
    if (ctrl) {
      ctrl.querySelectorAll('button').forEach(function (btn) {
        if (btn.getAttribute('data-lm-ham') === '1') return;
        if (!btn.querySelector('svg')) return;
        btn.innerHTML = BARS;
        btn.setAttribute('data-lm-ham', '1');
      });
    }
  }

  /* Run after Streamlit has painted */
  setTimeout(applyHamburger, 300);
  setTimeout(applyHamburger, 800);   /* second pass in case of slow render */

  /* Re-apply after any DOM change (Streamlit rerenders reset button content) */
  new win.MutationObserver(applyHamburger)
    .observe(doc.body, { childList: true, subtree: true });
})();
</script>
""", height=0, scrolling=False)



# ─── LLM status ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=2)
def _llm():
    return is_llm_available()


# ─── Helper: file icon HTML ──────────────────────────────────────────────────
def _ficon(ext: str) -> str:
    ext = ext.lstrip(".").lower()
    cls = {"pdf": "lm-file-icon-pdf", "docx": "lm-file-icon-docx",
           "csv": "lm-file-icon-csv"}.get(ext, "lm-file-icon-txt")
    return f'<span class="lm-file-icon {cls}">{ext}</span>'


# ─── Helper: empty state ─────────────────────────────────────────────────────
def _empty(icon: str, title: str, body: str):
    st.markdown(f"""
<div class="lm-empty">
  <div class="lm-empty-icon">{icon}</div>
  <div class="lm-empty-title">{title}</div>
  <div class="lm-empty-body">{body}</div>
</div>""", unsafe_allow_html=True)


# ─── Helper: page header ─────────────────────────────────────────────────────
def _page_hdr(title: str, sub: str = ""):
    st.markdown(f"""
<div class="lm-page-header">
  <h1 class="lm-page-title">{title}</h1>
  {"" if not sub else f'<p class="lm-page-sub">{sub}</p>'}
</div>""", unsafe_allow_html=True)
    st.write("")


# ─── Helper: section label ────────────────────────────────────────────────────
def _sec(label: str, action_html: str = ""):
    st.markdown(f"""
<div class="lm-section-label">
  <h3>{label}</h3>
  {action_html}
</div>""", unsafe_allow_html=True)


# ─── Helper: panel wrapper ────────────────────────────────────────────────────
def _panel_open(title: str = ""):
    t = f'<div class="lm-panel-title">{title}</div>' if title else ""
    st.markdown(f'<div class="lm-panel">{t}', unsafe_allow_html=True)

def _panel_close():
    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    # ── Logo ────────────────────────────────────────────────────
    st.markdown(f"""
<div class="lm-logo">
  <span class="lm-logo-mark">{BRAIN_SVG}</span>
  <span class="lm-logo-text">
    <span class="lm-logo-name">LocalMind</span>
    <span class="lm-logo-sub">on-device</span>
  </span>
</div>""", unsafe_allow_html=True)

    # ── Folders section ─────────────────────────────────────────
    st.markdown('<div class="lm-sec">Workspace</div>', unsafe_allow_html=True)

    auth_folders = get_authorized_folders()
    demo_path = str(Path(__file__).parent / "demo_data")
    demo_authorized = any(str(f) == str(Path(demo_path).resolve()) for f in auth_folders)

    # Render connected folders
    for folder in auth_folders:
        is_demo = str(folder) == str(Path(demo_path).resolve())
        badge = '<span class="lm-folder-badge">demo</span>' if is_demo else ""
        col_f, col_x = st.columns([6, 1])
        with col_f:
            st.markdown(f"""
<div class="lm-folder">
  <span class="lm-folder-icon">📂</span>
  <div class="lm-folder-body">
    <div class="lm-folder-name">{folder.name}{badge}</div>
    <div class="lm-folder-path">{str(folder)}</div>
  </div>
</div>""", unsafe_allow_html=True)
        with col_x:
            st.write("")
            if st.button("✕", key=f"revoke_{folder}", help=f"Disconnect {folder.name}"):
                ok, msg = revoke_folder(str(folder))
                st.session_state.sidebar_msg = ("ok" if ok else "err", msg)
                st.rerun()

    # Empty workspace state
    if not auth_folders:
        st.markdown(f"""
<div style="margin:0 0.6rem 0.5rem;padding:0.75rem 0.85rem;
            background:rgba(255,255,255,0.015);border-radius:8px;
            box-shadow:inset 0 0 0 1px rgba(255,255,255,0.05);
            font-size:11.5px;color:{INK_GHOST};text-align:center;">
  No folders connected
</div>""", unsafe_allow_html=True)

    # Demo data button (only when not yet added)
    st.write("")
    if not demo_authorized:
        st.markdown('<div class="lm-add-folder-btn">', unsafe_allow_html=True)
        if st.button("＋  Add demo workspace", key="add_demo_btn", use_container_width=True):
            with st.spinner("Authorizing and indexing..."):
                ok, msg = authorize_folder(demo_path)
                if ok:
                    index_files(force_reindex=False)
                    st.session_state.sidebar_msg = ("ok", f"Demo workspace connected and indexed — {Path(demo_path).name}")
                else:
                    st.session_state.sidebar_msg = ("err", msg)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div style="padding:0 1rem 0.25rem;font-size:11px;color:{JADE_400};
            display:flex;align-items:center;gap:5px;">
  <span style="width:5px;height:5px;border-radius:50%;background:{JADE_400};
               display:inline-block;"></span>
  Demo workspace connected
</div>""", unsafe_allow_html=True)

    # Add custom folder
    if "picker_path" not in st.session_state:
        st.session_state.picker_path = ""

    with st.expander("+  Add folder"):
        st.markdown(
            "<div style='font-size: 11px; color: #8B949E; margin-bottom: 8px;'>"
            "<strong>Tip:</strong> Hold <code>Shift</code> + Right-Click any folder in Windows and select "
            "<em>'Copy as path'</em>, then paste it below."
            "</div>", unsafe_allow_html=True
        )
        nf = st.text_input("Enter folder path", value=st.session_state.picker_path, key="manual_path_input", 
                           placeholder="C:\\Users\\...", label_visibility="collapsed")
                           
        if st.button("Connect", key="auth_btn", use_container_width=True):
            if nf and nf.strip():
                with st.spinner("Authorizing and indexing..."):
                    ok, msg = authorize_folder(nf.strip())
                    if ok:
                        index_files(force_reindex=False)
                        st.session_state.sidebar_msg = ("ok", f"{msg} and indexed successfully.")
                        st.session_state.picker_path = ""
                    else:
                        st.session_state.sidebar_msg = ("err", msg)
                st.rerun()
            else:
                st.warning("Enter a folder path.")

    # Sidebar feedback message
    if st.session_state.sidebar_msg:
        kind, msg = st.session_state.sidebar_msg
        if kind == "ok":
            st.success(msg)
        else:
            st.error(msg)
        st.session_state.sidebar_msg = None

    st.divider()

    # ── Index stats ──────────────────────────────────────────────
    st.markdown('<div class="lm-sec">Index</div>', unsafe_allow_html=True)

    try:
        idx = get_index_stats()
        fc = idx["file_count"]; cc = idx["chunk_count"]; be = idx.get("by_extension", {})
    except Exception:
        fc = cc = 0; be = {}

    ext_pills = "".join(
        f'<span class="lm-ext-pill">{e.lstrip(".")}</span>' for e in be
    )
    st.markdown(f"""
<div class="lm-stat-box">
  <div class="lm-stat-row">
    <span class="lm-stat-label">Files indexed</span>
    <span class="lm-stat-val">{fc}</span>
  </div>
  <div class="lm-stat-row">
    <span class="lm-stat-label">Chunks stored</span>
    <span class="lm-stat-val">{cc}</span>
  </div>
  <div class="lm-stat-row">
    <span class="lm-stat-label">Folders</span>
    <span class="lm-stat-val">{len(auth_folders)}</span>
  </div>
  {"" if not ext_pills else f'<div class="lm-ext-pills">{ext_pills}</div>'}
</div>""", unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="lm-index-btn-row">', unsafe_allow_html=True)
    ci, cr = st.columns(2)
    with ci:
        run_idx = st.button("Index", key="idx_btn", type="primary", use_container_width=True)
    with cr:
        run_reidx = st.button("Re-index", key="reidx_btn", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if run_idx or run_reidx:
        if not auth_folders:
            st.error("Connect a folder first.")
        else:
            prog = st.progress(0, text="Preparing…")
            def _cb(fname, cur, tot):
                prog.progress(int(cur/tot*100) if tot else 0,
                              text=f"Indexing {fname}")
            with st.spinner("Indexing…"):
                res = index_files(force_reindex=bool(run_reidx), progress_callback=_cb)
            prog.empty()
            n, sk, errs = res["indexed"], res["skipped"], res["errors"]
            msg = f"{n} indexed · {sk} unchanged"
            if errs:
                st.warning(msg + f" · {len(errs)} error(s)")
            else:
                st.success(msg)
            st.rerun()

    st.divider()

    # ── LLM status ───────────────────────────────────────────────
    st.markdown('<div class="lm-sec">AI Engine</div>', unsafe_allow_html=True)
    llm_ok, llm_msg = _llm()
    if llm_ok:
        model_name = config.GEMINI_MODEL
        st.markdown(f"""
<div class="lm-llm-row">
  <span class="lm-dot lm-dot-jade"></span>
  <span class="lm-llm-name">{model_name}</span>
  <span class="lm-llm-sub">ready</span>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div class="lm-llm-row">
  <span class="lm-dot lm-dot-ghost"></span>
  <span class="lm-llm-name" style="color:{INK_GHOST};">LLM offline</span>
</div>""", unsafe_allow_html=True)
        with st.expander("Configure"):
            st.markdown(f"""
<div style="font-size:12px;color:{INK_FAINT};line-height:1.65;">
Add to <code style="color:{JADE_300};background:{JADE_900};padding:1px 4px;border-radius:3px;">.env</code>:<br><br>
<code style="display:block;background:{VOID};padding:0.5rem 0.6rem;border-radius:6px;color:{JADE_300};font-size:11px;">GEMINI_API_KEY=your_key</code><br>
Search &amp; indexing work without a key.<br>
<a href="https://ai.google.dev" style="color:{JADE_400};">Get a key → ai.google.dev</a>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# MAIN AREA — tab navigation (mimics TopBar)
# ══════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "Ask",
    "Summarize",
    "Compare",
    "CSV",
    "File Ops",
    "Activity",
    "Files",
])


# ══════════════════════════════════════════════════════════════════
# TAB 1 — Ask / Chat
# ══════════════════════════════════════════════════════════════════
with tabs[0]:
    _page_hdr("Ask", "Natural-language questions over your indexed files")

    # Messages
    msgs_html_parts = []
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                msgs_html_parts.append(f"""
<div class="lm-msg-user">
  <div class="lm-msg-user-bubble">{msg["content"]}</div>
</div>""")
            else:
                body_html = ""
                # Render text as paragraphs
                for i, para in enumerate(msg["content"].split("\n\n")):
                    if para.strip():
                        body_html += f'<p style="margin:0 0 0.55rem;color:{"#E9ECEF" if i==0 else INK_DIM};">{para.strip()}</p>'

                # Source section
                src_html = ""
                sources = msg.get("sources") or []
                if sources:
                    src_cards = ""
                    for si, src in enumerate(sources, 1):
                        ext = src.get("extension", Path(src["filename"]).suffix)
                        icon = _ficon(ext)
                        excerpt = src["content"][:260].replace("<","&lt;").replace(">","&gt;")
                        src_cards += f"""
<div class="lm-source-card">
  <div class="lm-source-card-header">
    <span class="lm-src-num">{si}</span>
    {icon}
    <span class="lm-src-name">
      <span class="lm-src-fname">{src["filename"]}</span>
      <span class="lm-src-path">{src.get("file_path","")}</span>
    </span>
  </div>
  <div class="lm-src-evidence">
    <span class="lm-quote-icon">❝</span>
    <span class="lm-src-excerpt">{excerpt}{"…" if len(src["content"])>260 else ""}</span>
  </div>
</div>"""
                    src_html = f"""
<div class="lm-src-header">
  <span class="lm-src-label">Sources · {len(sources)}</span>
  <span class="lm-src-line"></span>
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">{src_cards}</div>"""

                msgs_html_parts.append(f"""
<div class="lm-msg-ai">
  <span class="lm-brain-mark">{BRAIN_SVG}</span>
  <div class="lm-msg-ai-body">
    <div class="lm-msg-ai-text">{body_html}</div>
    {src_html}
  </div>
</div>""")

        full_html = '<div class="lm-messages">' + "\n".join(msgs_html_parts) + "</div>"
        st.markdown(full_html, unsafe_allow_html=True)

    else:
        # Hero empty state
        st.markdown(f"""
<div class="lm-messages">
  <div class="lm-empty" style="margin-top:1rem;">
    <div class="lm-empty-icon">{BRAIN_SVG}</div>
    <div class="lm-empty-title">Ask anything about your files</div>
    <div class="lm-empty-body">
      Connect a folder, index your files, then ask questions in plain English.
      LocalMind retrieves the most relevant content and shows you exactly where it came from.
    </div>
  </div>
  <div class="lm-chips">
    <span class="lm-chip">What are the main findings in the research paper?</span>
    <span class="lm-chip">Summarize the study notes</span>
    <span class="lm-chip">Which product has the highest revenue?</span>
    <span class="lm-chip">Find files about machine learning</span>
    <span class="lm-chip">What algorithms are covered?</span>
  </div>
</div>""", unsafe_allow_html=True)

    st.divider()

    # ── Composer ────────────────────────────────────────────────
    st.markdown('<div style="padding:0 2rem;">', unsafe_allow_html=True)
    col_i, col_s = st.columns([10, 1])
    with col_i:
        q = st.text_input(
            "message",
            key="ask_input",
            placeholder="Ask a question or describe what you're looking for…",
            label_visibility="collapsed",
        )
    with col_s:
        send = st.button("↑", type="primary", key="ask_send", use_container_width=True)

    # Options row
    with st.expander("Options"):
        oc1, oc2, oc3 = st.columns(3)
        with oc1:
            top_k = st.slider("Results", 1, 10, 5, key="ask_topk")
        with oc2:
            ext_f = st.selectbox("File type", ["All",".pdf",".docx",".txt",".csv"], key="ask_ext")
        with oc3:
            mode_opts = ["Q&A (LLM)", "Search only"]
            mode = st.radio("Mode", mode_opts, index=0 if llm_ok else 1, key="ask_mode")

    if st.session_state.chat_history:
        if st.button("Clear conversation", key="ask_clear"):
            st.session_state.chat_history = []
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(f'<p class="lm-composer-hint">Enter to send · answers cite the files they came from</p>',
                unsafe_allow_html=True)

    # ── Process ─────────────────────────────────────────────────
    if send and q.strip():
        query = q.strip()
        st.session_state.chat_history.append({"role": "user", "content": query})

        with st.spinner("Searching…"):
            ext = None if ext_f == "All" else ext_f
            results = search_fts(query, top_k=top_k, file_extension=ext)

            use_llm = (mode == "Q&A (LLM)") and llm_ok
            if use_llm:
                try:
                    answer = answer_question(query, results)
                    reply = {"role": "assistant", "content": answer, "sources": results}
                except LLMUnavailableError as e:
                    reply = {"role": "assistant", "content": f"LLM error: {e}", "sources": results}
            else:
                if results:
                    lines = [f"**Found {len(results)} result(s)** for `{query}`\n"]
                    for i, r in enumerate(results, 1):
                        lines.append(f"**{i}. {r['filename']}** `{r.get('extension','')}`")
                        lines.append(f"> {r['content'][:280]}{'…' if len(r['content'])>280 else ''}")
                        lines.append("")
                    fname_r = search_by_filename(query)
                    if fname_r:
                        lines.append(f"**Files matching `{query}`:**")
                        for fr in fname_r[:5]:
                            lines.append(f"- `{fr['filename']}`")
                    reply = {"role": "assistant", "content": "\n".join(lines), "sources": results}
                else:
                    reply = {
                        "role": "assistant",
                        "content": "No matching content found in indexed files. Try different keywords or index more files.",
                        "sources": [],
                    }

        st.session_state.chat_history.append(reply)
        st.rerun()


# ══════════════════════════════════════════════════════════════════
# TAB 2 — Summarize
# ══════════════════════════════════════════════════════════════════
with tabs[1]:
    _page_hdr("Summarize", "AI-generated summaries and revision plans")
    st.markdown('<div class="lm-content">', unsafe_allow_html=True)

    indexed = get_indexed_files()
    if not indexed:
        _empty("📄", "No files indexed", "Connect a folder and click Index to get started.")
    else:
        file_map = {f["filename"]: f["path"] for f in indexed}
        c1, c2 = st.columns([3, 1])
        with c1:
            sel = st.selectbox("Document", list(file_map.keys()), key="sum_sel")
        with c2:
            do_plan = st.checkbox("Revision plan", key="sum_plan")

        do_sum = st.button("Generate summary", type="primary", key="do_sum")

        if do_sum:
            path = file_map[sel]
            with st.spinner(f"Reading {sel}…"):
                content = get_full_file_content(path)
            if not content:
                st.error("Could not retrieve file content. Try re-indexing.")
            elif not llm_ok:
                st.warning("LLM not available — showing raw content:")
                st.markdown(f"""
<div class="lm-panel" style="font-family:'JetBrains Mono',monospace;font-size:11.5px;
color:{INK_DIM};white-space:pre-wrap;max-height:360px;overflow-y:auto;">{content[:3000]}</div>
""", unsafe_allow_html=True)
            else:
                with st.spinner("Summarizing…"):
                    try:
                        summary = summarize_document(content, sel)
                    except LLMUnavailableError as e:
                        st.error(str(e)); summary = None
                if summary:
                    _panel_open(f"Summary · {sel}")
                    st.markdown(summary)
                    _panel_close()
                if do_plan and summary:
                    with st.spinner("Generating revision plan…"):
                        try:
                            plan = suggest_revision_plan(content, sel)
                        except LLMUnavailableError as e:
                            st.error(str(e)); plan = None
                    if plan:
                        st.write("")
                        _panel_open(f"Revision plan · {sel}")
                        st.markdown(plan)
                        _panel_close()

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 3 — Compare
# ══════════════════════════════════════════════════════════════════
with tabs[2]:
    _page_hdr("Document comparison", "Similarities, differences, and key evidence")
    st.markdown('<div class="lm-content">', unsafe_allow_html=True)

    indexed = get_indexed_files()
    if len(indexed) < 2:
        _empty("⚖️", "Need at least 2 files", "Index more files to enable comparison.")
    else:
        file_map = {f["filename"]: f["path"] for f in indexed}
        names = list(file_map.keys())
        ca, cb = st.columns(2)
        with ca:
            d1 = st.selectbox("Document A", names, key="cmp_a")
        with cb:
            d2 = st.selectbox("Document B", [n for n in names if n != d1], key="cmp_b")

        do_cmp = st.button("Compare documents", type="primary", key="do_cmp")

        if do_cmp:
            with st.spinner("Loading documents…"):
                c1 = get_full_file_content(file_map[d1])
                c2 = get_full_file_content(file_map[d2])
            if not c1 or not c2:
                st.error("Could not load one or both documents.")
            elif not llm_ok:
                st.warning("LLM not available — showing documents side by side:")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**{d1}**")
                    st.text_area("", c1[:2000], height=320, key="raw1")
                with col2:
                    st.markdown(f"**{d2}**")
                    st.text_area("", c2[:2000], height=320, key="raw2")
            else:
                with st.spinner("Comparing…"):
                    try:
                        result = compare_documents(c1, d1, c2, d2)
                    except LLMUnavailableError as e:
                        result = None; st.error(str(e))
                if result:
                    # Doc headers
                    dh1, dh_arrow, dh2 = st.columns([5, 1, 5])
                    ext1 = Path(file_map[d1]).suffix
                    ext2 = Path(file_map[d2]).suffix
                    with dh1:
                        st.markdown(f"""
<div class="lm-panel">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.4rem;">
    {_ficon(ext1)}
    <span style="font-size:13px;font-weight:600;color:{INK};">{d1}</span>
  </div>
  <div style="font-size:11px;color:{INK_GHOST};font-family:'JetBrains Mono',monospace;">Document A</div>
</div>""", unsafe_allow_html=True)
                    with dh_arrow:
                        st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:center;padding-top:1rem;">
  <span style="display:inline-flex;width:28px;height:28px;align-items:center;justify-content:center;
               border-radius:50%;background:{SURFACE_H};box-shadow:inset 0 0 0 1px rgba(255,255,255,0.07);
               font-size:12px;color:{INK_FAINT};">→</span>
</div>""", unsafe_allow_html=True)
                    with dh2:
                        st.markdown(f"""
<div class="lm-panel">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.4rem;">
    {_ficon(ext2)}
    <span style="font-size:13px;font-weight:600;color:{JADE_300};">{d2}</span>
  </div>
  <div style="font-size:11px;color:{INK_GHOST};font-family:'JetBrains Mono',monospace;">Document B</div>
</div>""", unsafe_allow_html=True)

                    st.write("")
                    _panel_open("Analysis")
                    st.markdown(result)
                    _panel_close()

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 4 — CSV
# ══════════════════════════════════════════════════════════════════
with tabs[3]:
    _page_hdr("CSV Analysis", "Natural-language analysis of structured data")
    st.markdown('<div class="lm-content">', unsafe_allow_html=True)

    indexed = get_indexed_files()
    csvs = [f for f in indexed if f["extension"] == ".csv"]

    if not csvs:
        _empty("📊", "No CSV files indexed", "Add a folder with .csv files and index it.")
    else:
        csv_map = {f["filename"]: f["path"] for f in csvs}
        sel_csv = st.selectbox("Dataset", list(csv_map.keys()), key="csv_sel")
        csv_path = csv_map[sel_csv]

        with st.expander("Preview data"):
            try:
                df = pd.read_csv(csv_path)
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Rows", len(df))
                mc2.metric("Columns", len(df.columns))
                mc3.metric("Numeric cols", len(df.select_dtypes(include="number").columns))
                st.dataframe(df.head(12), use_container_width=True)
            except Exception as e:
                st.error(f"Preview error: {e}")

        sugg = [
            "What are the top 5 rows by revenue?",
            "Which region has the highest average profit?",
            "Show revenue trends over time",
            "Which product has the most returns?",
            "What is the average customer satisfaction?",
        ]
        sq = st.selectbox("Suggested questions", ["— type your own —"] + sugg, key="csv_sq")
        csv_q = st.text_input(
            "Your question",
            value="" if sq.startswith("—") else sq,
            key="csv_q",
            placeholder="e.g. What is the best performing region?",
        )

        do_csv = st.button("Analyze", type="primary", key="do_csv")

        if do_csv:
            if not csv_q.strip():
                st.warning("Enter a question.")
            else:
                content = get_full_file_content(csv_path)
                if not content:
                    st.error("Could not retrieve CSV content.")
                elif not llm_ok:
                    st.warning("LLM not available — showing statistics:")
                    try:
                        df = pd.read_csv(csv_path)
                        st.dataframe(df.describe(), use_container_width=True)
                        nc = df.select_dtypes(include="number").columns.tolist()
                        if nc and len(nc) <= 5:
                            st.bar_chart(df[nc].head(20))
                    except Exception as e:
                        st.error(str(e))
                else:
                    with st.spinner("Analyzing…"):
                        try:
                            analysis = analyze_csv(content, sel_csv, csv_q)
                        except LLMUnavailableError as e:
                            analysis = None; st.error(str(e))
                    if analysis:
                        _panel_open(f"Analysis · {sel_csv}")
                        st.markdown(analysis)
                        _panel_close()
                        try:
                            df = pd.read_csv(csv_path)
                            nc = df.select_dtypes(include="number").columns.tolist()
                            if nc and len(nc) <= 6:
                                st.write("")
                                st.bar_chart(df[nc].head(20))
                        except Exception:
                            pass

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 5 — File Operations (staged: proposed → review → confirm → executing → verified)
# ══════════════════════════════════════════════════════════════════
with tabs[4]:
    _page_hdr("File Operations", "Safely create, rename, and move files — always with your confirmation")
    st.markdown('<div class="lm-content">', unsafe_allow_html=True)

    auth_folders = get_authorized_folders()
    if not auth_folders:
        _empty("🔒", "No folders connected",
               "Connect at least one folder to enable file operations.")
    else:
        # Security notice
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:8px;padding:0.6rem 0.85rem;
            background:rgba(22,192,140,0.05);border-radius:8px;
            box-shadow:inset 0 0 0 1px rgba(22,192,140,0.15);
            font-size:12.5px;color:{JADE_300};margin-bottom:1.25rem;">
  <span style="width:6px;height:6px;border-radius:50%;background:{JADE_400};flex-shrink:0;"></span>
  LocalMind never modifies your files without your explicit confirmation.
</div>""", unsafe_allow_html=True)

        indexed_files = get_indexed_files()

        # Initialize session state for batch operations
        if "pending_proposals" not in st.session_state:
            st.session_state.pending_proposals = None
        if "op_results" not in st.session_state:
            st.session_state.op_results = None

        # ── Agentic Natural Language Input ──
        _sec("What would you like to do with your files?")
        nl_prompt = st.text_area(
            "Natural Language Request",
            label_visibility="collapsed",
            placeholder="e.g. Find all my .txt files and move them to the Archive folder.",
            height=100
        )

        if st.button("Plan Operations", type="primary"):
            if not nl_prompt.strip():
                st.warning("Please describe what you want to do.")
            else:
                st.session_state.pending_proposals = None
                st.session_state.op_results = None
                with st.spinner("AI is planning operations..."):
                    try:
                        valid_ops, errors = plan_file_operations(nl_prompt, indexed_files, auth_folders)
                        if errors:
                            for err in errors:
                                st.warning(err)
                        
                        if valid_ops:
                            proposals = []
                            for op in valid_ops:
                                otype = op["operation"]
                                if otype == "move":
                                    ok, msg, prop = propose_move(op["source"], op["destination_folder"])
                                elif otype == "rename":
                                    ok, msg, prop = propose_rename(op["source"], op["new_name"])
                                elif otype == "create":
                                    ok, msg, prop = propose_create(op["destination"], op.get("content", ""))
                                elif otype == "create_folder":
                                    ok, msg, prop = propose_create_folder(op["destination"])
                                
                                if ok and prop:
                                    proposals.append(prop)
                                else:
                                    st.error(f"Proposal failed: {msg}")
                            
                            if proposals:
                                st.session_state.pending_proposals = proposals
                        elif not errors:
                            st.info("The AI couldn't formulate any valid operations from that request.")
                    except LLMUnavailableError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Failed to plan operations: {e}")

        # ── Staged Confirmation Card ──
        proposals = st.session_state.get("pending_proposals")
        if proposals:
            st.write("")
            stages = ["Proposed", "Review", "Confirm", "Executing", "Verified"]
            active = 2  # "Confirm"
            steps_html = ""
            for si, s in enumerate(stages):
                cls = "done" if si < active else ("active" if si == active else "")
                num_inner = "✓" if si < active else str(si + 1)
                steps_html += f'<span class="lm-step {cls}"><span class="lm-step-num">{num_inner}</span>{s}</span>'
                if si < len(stages) - 1:
                    steps_html += '<span class="lm-step-arrow"></span>'

            st.markdown(f"""
<div class="lm-stage-card">
  <div class="lm-stage-header">
    <span class="lm-badge lm-badge-warn">{len(proposals)} Operations</span>
    <span class="lm-stage-title">Confirm before executing</span>
  </div>
  <div class="lm-steps">{steps_html}</div>
""", unsafe_allow_html=True)

            for prop in proposals:
                op = prop.operation.upper()
                src_val = prop.source or ""
                dst_val = prop.destination or ""
                
                st.markdown(f"""
  <div class="lm-change-row" style="margin-top: 8px;">
    <span class="lm-badge" style="font-size: 10px; padding: 2px 6px;">{op}</span>
    <span class="lm-change-from">{src_val}</span>
    <span class="lm-change-arrow">→</span>
    <span class="lm-change-to">{dst_val}</span>
  </div>
""", unsafe_allow_html=True)

            st.markdown(f"""
  <div style="font-size:12px;color:{INK_GHOST};margin-top:1.2rem;">
    This action modifies your filesystem. Confirm only if correct.
  </div>
</div>""", unsafe_allow_html=True)

            cc1, cc2, _ = st.columns([3, 2, 4])
            with cc1:
                if st.button("Confirm & Execute All", type="primary", key="conf_op"):
                    results = []
                    with st.spinner("Executing operations..."):
                        for prop in proposals:
                            success, message = execute_operation(prop)
                            v_msg = ""
                            if success:
                                v_ok, v_msg = verify_operation(prop)
                            results.append({"success": success, "message": message, "verify": v_msg})
                    st.session_state.pending_proposals = None
                    st.session_state.op_results = results
                    st.rerun()
            with cc2:
                if st.button("Cancel", key="cancel_op"):
                    st.session_state.pending_proposals = None
                    st.info("Operations cancelled.")
                    st.rerun()

        # ── Results view ──
        results = st.session_state.get("op_results")
        if results:
            st.write("")
            _sec("Execution Results")
            for res in results:
                if res["success"]:
                    st.markdown(f"""
<div class="lm-verified" style="margin-bottom: 8px;">
  <div class="lm-verified-title">✓ {res['message']}</div>
  <div class="lm-verified-sub">Verified: {res['verify']}</div>
</div>""", unsafe_allow_html=True)
                else:
                    st.error(res["message"])
            
            if st.button("Dismiss"):
                st.session_state.op_results = None
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 6 — Activity / Action Log
# ══════════════════════════════════════════════════════════════════
with tabs[5]:
    _page_hdr("Activity",
              "Every read and write LocalMind performed on your authorized folders")
    st.markdown('<div class="lm-content-wide">', unsafe_allow_html=True)

    log = get_action_log(limit=100)

    ch, cb_col = st.columns([6, 1])
    with cb_col:
        if log and st.button("Clear", key="clr_log"):
            clear_action_log()
            st.rerun()

    if not log:
        _empty("📋", "No activity yet",
               "File operations you perform will appear here as a timestamped audit trail.")
    else:
        # Group by day
        from collections import defaultdict
        days: dict = defaultdict(list)
        for e in log:
            ts = str(e.get("timestamp", ""))
            day = ts[:10] if ts else "Unknown"
            days[day].append(e)

        op_icons = {
            "move": ("🗂", "lm-tl-icon-move"),
            "rename": ("✏️", "lm-tl-icon-ren"),
            "create": ("➕", "lm-tl-icon-create"),
        }
        status_cls = {
            "completed": "lm-badge-jade",
            "failed": "lm-badge-danger",
            "error": "lm-badge-danger",
            "executing": "lm-badge-info",
            "pending": "lm-badge-neutral",
        }

        for day, events in days.items():
            st.markdown(f"""
<div class="lm-section-label" style="margin-top:1.25rem;">
  <h3>{day}</h3>
  <span style="font-family:'JetBrains Mono',monospace;font-size:10px;color:{INK_GHOST};">
    {len(events)} event{"s" if len(events)!=1 else ""}
  </span>
</div>""", unsafe_allow_html=True)

            items_html = ""
            for e in events:
                op = e.get("operation", "")
                icon_char, icon_cls = op_icons.get(op, ("⬡", "lm-tl-icon-idx"))
                status = e.get("status", "")
                badge_cls = status_cls.get(status, "lm-badge-neutral")
                ts = str(e.get("timestamp", ""))
                time_str = ts[11:16] if len(ts) >= 16 else ts
                src = (e.get("source_path") or "—")
                dst = e.get("destination_path") or ""
                detail = dst if dst else (e.get("details") or "")

                items_html += f"""
<li class="lm-tl-item">
  <span class="lm-tl-icon {icon_cls}">{icon_char}</span>
  <div class="lm-tl-body">
    <div style="display:flex;align-items:center;gap:6px;">
      <span class="lm-tl-title">{op.capitalize()} · {Path(src).name if src != "—" else "—"}</span>
      <span class="lm-badge {badge_cls}">{status}</span>
    </div>
    <div class="lm-tl-detail">{src}</div>
    {"" if not detail else f'<div class="lm-tl-detail" style="color:{INK_GHOST};">{detail}</div>'}
  </div>
  <span class="lm-tl-time">{time_str}</span>
</li>"""

            st.markdown(f'<ol class="lm-timeline">{items_html}</ol>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 7 — Indexed Files
# ══════════════════════════════════════════════════════════════════
with tabs[6]:
    _page_hdr("Indexed Files", "All files currently in the LocalMind index")
    st.markdown('<div class="lm-content-wide">', unsafe_allow_html=True)

    indexed = get_indexed_files()
    if not indexed:
        _empty("🗄️", "Index is empty",
               "Connect a folder and click Index in the sidebar.")
    else:
        total_size = sum(f.get("size_bytes", 0) or 0 for f in indexed)
        ext_counts: dict = {}
        for f in indexed:
            ext_counts[f["extension"]] = ext_counts.get(f["extension"], 0) + 1

        mm1, mm2, mm3, mm4 = st.columns(4)
        mm1.metric("Files", len(indexed))
        mm2.metric("Size", f"{total_size/1024:.1f} KB")
        try:
            mm3.metric("Chunks", get_index_stats().get("chunk_count", 0))
        except Exception:
            mm3.metric("Chunks", "–")
        mm4.metric("Types", len(ext_counts))

        st.write("")

        all_exts = list(ext_counts.keys())
        filter_exts = st.multiselect("Filter", all_exts, default=all_exts, key="file_filter")
        filtered = [f for f in indexed if f["extension"] in filter_exts]

        if filtered:
            df = pd.DataFrame(filtered)
            df["size_kb"] = (df["size_bytes"].fillna(0) / 1024).round(1)
            disp = df[["filename","extension","size_kb","chunk_count","indexed_at"]].copy()
            disp.columns = ["Filename","Type","Size (KB)","Chunks","Indexed At"]
            st.dataframe(
                disp, use_container_width=True,
                height=min(450, 45 + len(disp) * 36),
                column_config={
                    "Filename": st.column_config.TextColumn(width="large"),
                    "Type": st.column_config.TextColumn(width="small"),
                    "Size (KB)": st.column_config.NumberColumn(format="%.1f", width="small"),
                    "Chunks": st.column_config.NumberColumn(width="small"),
                    "Indexed At": st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm", width="medium"),
                },
            )

    st.markdown("</div>", unsafe_allow_html=True)


# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="border-top:1px solid rgba(255,255,255,0.05);margin-top:2rem;
            padding:1rem 2rem;text-align:center;">
  <span style="font-family:'JetBrains Mono',monospace;font-size:10px;
               color:{INK_GHOST};letter-spacing:0.05em;">
    LOCALMIND · on-device · all data stays local
  </span>
</div>""", unsafe_allow_html=True)
