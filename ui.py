# ui.py
import streamlit as st

def inject_global_css():
    st.markdown(
        """
<style>
    /* ---------- THEME / BASICS ---------- */
    :root, .stApp {
        --gradient-1: linear-gradient(90deg, #5B8DEE 0%, #7C3AED 100%);
        --card-bg: rgba(255, 255, 255, 0.05);
        --card-border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .main { padding-top: 0.5rem; }
    .block-container { padding-bottom: 7.5rem; } /* keep space for pinned chat input */

    h1, h2, h3, h4 {
        background: var(--gradient-1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }

    section[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    .stButton > button {
        background: var(--gradient-1);
        color: white;
        border: none;
        padding: 0.5rem 1.25rem;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 15px rgba(91, 141, 238, 0.25);
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(91, 141, 238, 0.35);
    }
    .stDownloadButton > button {
        background: linear-gradient(90deg, #10B981 0%, #059669 100%);
        color: white;
        border: none;
        padding: 0.5rem 1.25rem;
        border-radius: 25px;
        font-weight: 600;
    }

    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea textarea,
    .stDateInput input {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stAlert { border-radius: 10px; border-left: 4px solid; }
    .stSpinner > div { border-top-color: #5B8DEE !important; }

    .stChatMessage {
        background-color: var(--card-bg);
        border-radius: 14px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        backdrop-filter: blur(10px);
        border: var(--card-border);
    }

    .status-dot {
        width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 8px;
    }
    .status-green { background: #10B981; }
    .status-yellow { background: #F59E0B; }
    .status-red { background: #EF4444; }
    hr {
        border: none; height: 1px; background: linear-gradient(90deg, transparent, #5B8DEE, transparent);
        margin: 1.25rem 0;
    }

    /* ---------- PIN CHAT INPUT TO THE BOTTOM ---------- */
    /* Streamlit 1.20+ uses data-testid="stChatInput" for the chat input container */
    [data-testid="stChatInput"] {
        position: sticky;
        bottom: 0;
        z-index: 1000;
        padding-top: 0.5rem;
        /* subtle fade to separate input from content */
        background: linear-gradient(180deg, rgba(11,11,13,0) 0%, rgba(11,11,13,0.75) 40%, rgba(11,11,13,0.9) 100%);
        backdrop-filter: blur(8px);
    }

    /* In case a theme overrides background, reinforce a card look */
    [data-testid="stChatInput"] > div {
        border-top: 1px solid rgba(255, 255, 255, 0.08);
    }
</style>
        """,
        unsafe_allow_html=True,
    )


def status_badge(ok: bool, label: str):
    color = "green" if ok else "red"
    st.markdown(
        f"""
<span class="status-dot status-{color}"></span>
<span style="opacity:0.85">{label}</span>
""",
        unsafe_allow_html=True,
    )
