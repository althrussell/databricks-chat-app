# ui/styling.py
import streamlit as st

def apply_executive_styling():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --font-main: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        --font-mono: 'JetBrains Mono', monospace;

        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        --warning-gradient: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);
        --neutral-gradient: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);

        --background-primary: #f8fafc;
        --background-secondary: #ffffff;
        --background-elevated: #ffffff;

        --text-primary: #1a202c;
        --text-secondary: #4a5568;
        --text-muted: #718096;
        --text-inverse: #ffffff;

        --border-light: #e2e8f0;
        --border-medium: #cbd5e0;
        --border-dark: #a0aec0;

        --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

        --border-radius-sm: 6px;
        --border-radius-md: 8px;
        --border-radius-lg: 12px;
        --border-radius-xl: 16px;

        --spacing-xs: 0.25rem;
        --spacing-sm: 0.5rem;
        --spacing-md: 1rem;
        --spacing-lg: 1.5rem;
        --spacing-xl: 2rem;
    }

    html {
        scroll-behavior: smooth;
    }

    body {
        font-family: var(--font-main);
        -webkit-tap-highlight-color: transparent;
        touch-action: manipulation;
        font-size: 15px;
        color: var(--text-primary);
    }

    h1, h2, h3, h4, h5 {
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: var(--spacing-md);
    }

    h1 { font-size: 28px; }
    h2 { font-size: 22px; }
    h3 { font-size: 18px; }
    h4, h5 { font-size: 16px; }

    p, li, .stMarkdown {
        font-size: 15px;
        color: var(--text-secondary);
        line-height: 1.6;
    }

    .stApp {
        background: var(--background-primary);
        color: var(--text-primary);
    }

    .main .block-container {
        padding: var(--spacing-xl);
        max-width: 1400px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: var(--background-secondary);
        border-right: 1px solid var(--border-light);
        box-shadow: var(--shadow-sm);
        padding: var(--spacing-xl) var(--spacing-lg);
    }

    section[data-testid="stSidebar"] .stButton > button {
        width: 100%;
        padding: var(--spacing-md);
        border-radius: var(--border-radius-md);
        font-size: 14px;
        font-weight: 500;
        border: 1px solid var(--border-light);
        background: var(--background-secondary);
        color: var(--text-primary);
        transition: all 0.2s ease;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: var(--primary-gradient);
        color: var(--text-inverse);
        box-shadow: var(--shadow-sm);
        border: none;
    }

    /* Chat Bubbles */
    .stChatMessage {
        background: var(--background-elevated);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius-lg);
        padding: var(--spacing-md);
        margin-bottom: var(--spacing-md);
        box-shadow: var(--shadow-sm);
    }

    .stChatMessage[data-testid="user-message"] {
        border-left: 4px solid #667eea;
        background: linear-gradient(135deg, rgba(102,126,234,0.05), rgba(118,75,162,0.02));
    }

    .stChatMessage[data-testid="assistant-message"] {
        border-left: 4px solid var(--border-medium);
    }

    .stChatMessage [data-testid^="chatAvatarIcon"] {
        width: 30px;
        height: 30px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
    }

    [data-testid="chatAvatarIcon-user"] {
        background: var(--primary-gradient);
    }

    [data-testid="chatAvatarIcon-assistant"] {
        background: var(--neutral-gradient);
    }

    /* Chat Input Area */
    .chat-model-wrapper {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--spacing-sm);
    }

    .chat-model-indicator {
        font-size: 13px;
        color: var(--text-muted);
        font-weight: 500;
    }

    .custom-chat-input textarea {
        width: 100%;
        padding: var(--spacing-md);
        font-size: 15px;
        background: var(--background-elevated);
        border: 2px solid var(--border-light);
        border-radius: var(--border-radius-lg);
        resize: none;
        min-height: 80px;
    }

    .custom-chat-input textarea:focus {
        border-color: #667eea;
        outline: none;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
    }

    .sticky-bottom {
        position: sticky;
        bottom: 0;
        background: var(--background-elevated);
        padding: var(--spacing-md) var(--spacing-lg);
        box-shadow: var(--shadow-sm);
        z-index: 10;
    }

    /* History & Model Info */
    .history-card {
        background: var(--background-elevated);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius-md);
        padding: var(--spacing-md);
        margin-bottom: var(--spacing-md);
        box-shadow: var(--shadow-sm);
        font-size: 14px;
    }

    .stMarkdown h4, .stMarkdown h5 {
        font-size: 15px !important;
        font-weight: 600;
        color: var(--text-primary);
    }

    .stMarkdown p, .stMarkdown li {
        font-size: 14px;
        color: var(--text-secondary);
    }

    .stMarkdown small, .stMarkdown span, .stMarkdown div,
    .st-emotion-cache-1wivap2, .st-emotion-cache-ehvl34q1 {
        font-size: 13px !important;
        color: var(--text-muted);
    }

    .stMarkdown code {
        font-family: var(--font-mono);
        font-size: 12px;
        background: rgba(0,0,0,0.05);
        padding: 2px 6px;
        border-radius: 6px;
    }

    .st-expanderHeader {
        font-size: 14px;
        font-weight: 500;
        color: var(--text-muted);
    }

    .stTextInput input, .stSelectbox label, .stNumberInput input {
        font-size: 14px;
    }

    /* Mobile */
    @media (max-width: 768px) {
        .main .block-container {
            padding: var(--spacing-lg);
        }
        .chat-model-indicator {
            font-size: 12px;
        }
    }

    /* Dark Mode */
    @media (prefers-color-scheme: dark) {
        :root {
            --background-primary: #0f172a;
            --background-secondary: #1e293b;
            --background-elevated: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --border-light: #334155;
            --border-medium: #475569;
            --border-dark: #64748b;
        }
    }

    </style>
    """, unsafe_allow_html=True)
