# ui/styling.py - Updated with Apple-grade UX improvements
import streamlit as st

def apply_executive_styling():
    """Apply executive-grade CSS styling with Apple-inspired UX improvements"""
    st.markdown("""
    <style>
    /* Import premium fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* CSS Variables for consistent premium theming */
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        --warning-gradient: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);
        --neutral-gradient: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        
        --background-primary: #fafbfc;
        --background-secondary: #ffffff;
        --background-elevated: #ffffff;
        
        --text-primary: #1a202c;
        --text-secondary: #4a5568;
        --text-muted: #718096;
        --text-inverse: #ffffff;
        
        --border-light: #e2e8f0;
        --border-medium: #cbd5e0;
        --border-dark: #a0aec0;
        
        --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        
        --border-radius-sm: 6px;
        --border-radius-md: 8px;
        --border-radius-lg: 12px;
        --border-radius-xl: 16px;
        
        --spacing-xs: 0.25rem;
        --spacing-sm: 0.5rem;
        --spacing-md: 1rem;
        --spacing-lg: 1.5rem;
        --spacing-xl: 2rem;
        --spacing-2xl: 3rem;
        
        --transition-fast: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        --transition-normal: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        --transition-slow: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* Global typography and base styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        letter-spacing: -0.01em;
    }

    .stApp {
        background: var(--background-primary);
        color: var(--text-primary);
    }

    /* Premium sidebar styling */
    section[data-testid="stSidebar"] {
        background: var(--background-secondary);
        border-right: 1px solid var(--border-light);
        box-shadow: var(--shadow-lg);
        width: 320px !important;
        min-width: 320px !important;
    }

    section[data-testid="stSidebar"] > div {
        padding: var(--spacing-xl) var(--spacing-lg);
    }

    /* IMPROVED: Executive-grade sidebar buttons with perfect alignment */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 56px !important; /* Increased height for better text fit */
        margin-bottom: var(--spacing-sm);
        border: 1px solid var(--border-light);
        background: var(--background-secondary);
        color: var(--text-primary);
        padding: var(--spacing-md) var(--spacing-lg) !important;
        border-radius: var(--border-radius-lg);
        font-size: 16px !important; /* Increased font size */
        font-weight: 500;
        text-align: center !important; /* Center aligned text */
        transition: var(--transition-fast);
        box-shadow: var(--shadow-sm);
        display: flex !important;
        align-items: center !important;
        justify-content: center !important; /* Perfect center alignment */
        position: relative;
        overflow: hidden;
        line-height: 1.2 !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: var(--background-elevated);
        border-color: var(--border-medium);
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
        color: var(--text-primary);
    }

    section[data-testid="stSidebar"] .stButton > button:active {
        transform: translateY(0);
        box-shadow: var(--shadow-sm);
    }

    /* Primary buttons (active navigation) */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: var(--primary-gradient) !important;
        border: none !important;
        color: var(--text-inverse) !important;
        font-weight: 600 !important;
        box-shadow: var(--shadow-md) !important;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-lg) !important;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="primary"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
        pointer-events: none;
    }

    /* Sidebar typography */
    section[data-testid="stSidebar"] h3 {
        color: var(--text-primary);
        font-size: 24px;
        font-weight: 700;
        margin-bottom: var(--spacing-xs);
        text-align: center;
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    section[data-testid="stSidebar"] h4 {
        color: var(--text-primary);
        font-size: 16px;
        font-weight: 600;
        margin: var(--spacing-xl) 0 var(--spacing-md) 0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        opacity: 0.8;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] [data-testid="caption"] {
        color: var(--text-secondary);
        font-size: 14px;
        line-height: 1.5;
        margin-bottom: var(--spacing-md);
    }

    section[data-testid="stSidebar"] [data-testid="caption"] {
        text-align: center;
        font-weight: 400;
        opacity: 0.7;
    }

    /* Sidebar dividers */
    section[data-testid="stSidebar"] hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-light), transparent);
        margin: var(--spacing-xl) 0;
    }

    /* Main content area */
    .main .block-container {
        padding: var(--spacing-2xl) var(--spacing-2xl) var(--spacing-md) var(--spacing-2xl);
        max-width: 1400px;
    }

    /* Executive page headers */
    .executive-header {
        text-align: left;
        padding: 0 0 var(--spacing-2xl) 0;
        margin-bottom: var(--spacing-2xl);
        border-bottom: 1px solid var(--border-light);
        position: relative;
    }

    .executive-header h1 {
        font-size: 36px;
        font-weight: 800;
        line-height: 1.2;
        color: var(--text-primary);
        margin: 0 0 var(--spacing-sm) 0;
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .executive-header .subtitle {
        font-size: 18px;
        font-weight: 400;
        color: var(--text-secondary);
        margin: 0;
        line-height: 1.4;
    }

    .executive-header .status-indicator {
        position: absolute;
        top: 0;
        right: 0;
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        padding: var(--spacing-sm) var(--spacing-md);
        background: var(--success-gradient);
        color: var(--text-inverse);
        border-radius: var(--border-radius-lg);
        font-size: 14px;
        font-weight: 500;
        box-shadow: var(--shadow-sm);
    }

    /* Premium status indicators */
    .status-card {
        background: var(--background-elevated);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius-lg);
        padding: var(--spacing-md);
        margin-bottom: var(--spacing-sm);
        box-shadow: var(--shadow-sm);
        transition: var(--transition-fast);
    }

    .status-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }

    .status-success {
        border-left: 4px solid #10b981;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(16, 185, 129, 0.02) 100%);
    }

    .status-warning {
        border-left: 4px solid #f59e0b;
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.05) 0%, rgba(245, 158, 11, 0.02) 100%);
    }

    .status-error {
        border-left: 4px solid #ef4444;
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.05) 0%, rgba(239, 68, 68, 0.02) 100%);
    }

    /* IMPROVED: Professional chat message avatars */
    .stChatMessage[data-testid="user-message"] [data-testid="chatAvatarIcon-user"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }

    .stChatMessage[data-testid="user-message"] [data-testid="chatAvatarIcon-user"]::after {
        content: "You" !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stChatMessage[data-testid="assistant-message"] [data-testid="chatAvatarIcon-assistant"] {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }

    .stChatMessage[data-testid="assistant-message"] [data-testid="chatAvatarIcon-assistant"]::after {
        content: "AI" !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* IMPROVED: Chat messages with cleaner styling */
    .stChatMessage {
        background: var(--background-elevated);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius-xl);
        padding: var(--spacing-lg);
        margin-bottom: var(--spacing-lg);
        box-shadow: var(--shadow-sm);
        font-size: 15px;
        line-height: 1.6;
        transition: var(--transition-fast);
    }

    .stChatMessage:hover {
        box-shadow: var(--shadow-md);
    }

    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.02) 100%);
        border-left: 4px solid #667eea;
    }

    .stChatMessage[data-testid="assistant-message"] {
        background: var(--background-elevated);
        border-left: 4px solid var(--border-medium);
    }

    /* IMPROVED: Claude.ai-style chat input */
    [data-testid="stChatInput"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: var(--spacing-xl) 0 var(--spacing-lg) 0 !important;
        position: relative !important;
    }

    [data-testid="stChatInput"] > div {
        background: var(--background-elevated) !important;
        border: 2px solid var(--border-light) !important;
        border-radius: var(--border-radius-xl) !important;
        box-shadow: var(--shadow-lg) !important;
        transition: var(--transition-fast) !important;
        position: relative !important;
        overflow: visible !important;
    }

    [data-testid="stChatInput"] > div:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1), var(--shadow-lg) !important;
    }

    [data-testid="stChatInput"] input {
        background: transparent !important;
        border: none !important;
        padding: var(--spacing-lg) var(--spacing-xl) !important;
        font-size: 16px !important;
        color: var(--text-primary) !important;
        min-height: 24px !important;
        line-height: 1.5 !important;
        resize: none !important;
    }

    [data-testid="stChatInput"] input:focus {
        outline: none !important;
        box-shadow: none !important;
        border: none !important;
    }

    [data-testid="stChatInput"] input::placeholder {
        color: var(--text-muted) !important;
        font-weight: 400 !important;
    }

    /* Model indicator for chat input */
    .chat-model-indicator {
        position: absolute;
        bottom: -28px;
        left: var(--spacing-md);
        font-size: 12px;
        color: var(--text-muted);
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
    }

    .chat-model-indicator::before {
        content: "⚡";
        font-size: 10px;
    }

    /* Form elements */
    .stSelectbox > div > div {
        background: var(--background-elevated);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius-md);
        box-shadow: var(--shadow-sm);
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--background-elevated);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius-md);
        padding: var(--spacing-md);
        font-size: 15px;
        color: var(--text-primary);
        transition: var(--transition-fast);
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    .stNumberInput > div > div > input {
        background: var(--background-elevated);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius-md);
        padding: var(--spacing-md);
        font-size: 15px;
        color: var(--text-primary);
        transition: var(--transition-fast);
    }

    .stNumberInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* Toggle switches */
    .stToggle > div {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
    }

    /* Metrics */
    .stMetric {
        background: var(--background-elevated);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius-lg);
        padding: var(--spacing-lg);
        box-shadow: var(--shadow-sm);
        transition: var(--transition-fast);
    }

    .stMetric:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }

    .stMetric > div > div:first-child {
        font-size: 14px;
        font-weight: 500;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stMetric > div > div:nth-child(2) {
        font-size: 32px;
        font-weight: 700;
        color: var(--text-primary);
        margin: var(--spacing-xs) 0;
    }

    /* IMPROVED: Consistent button heights in history */
    .history-actions {
        display: flex;
        gap: var(--spacing-sm);
        align-items: stretch;
    }

    .history-actions .stButton > button,
    .history-actions .stDownloadButton > button {
        height: 40px !important;
        padding: 0 var(--spacing-md) !important;
        font-size: 14px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
        min-width: 80px !important;
    }

    /* Compact history item styling */
    .history-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--spacing-md);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius-md);
        margin-bottom: var(--spacing-sm);
        background: var(--background-elevated);
        transition: var(--transition-fast);
        cursor: pointer;
    }

    .history-item:hover {
        box-shadow: var(--shadow-md);
        border-color: var(--border-medium);
    }

    .history-item-main {
        flex: 1;
        display: flex;
        align-items: center;
        gap: var(--spacing-lg);
    }

    .history-item-title {
        font-weight: 600;
        color: var(--text-primary);
        font-size: 15px;
    }

    .history-item-meta {
        display: flex;
        gap: var(--spacing-md);
        font-size: 13px;
        color: var(--text-secondary);
    }

    .history-item-actions {
        display: flex;
        gap: var(--spacing-xs);
    }

    .history-item-actions button {
        padding: var(--spacing-xs) var(--spacing-sm) !important;
        font-size: 12px !important;
        height: 32px !important;
        min-width: auto !important;
    }

    /* Tables */
    .stDataFrame {
        border-radius: var(--border-radius-lg);
        overflow: hidden;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-light);
    }

    .stDataFrame table {
        background: var(--background-elevated);
        font-size: 14px;
    }

    .stDataFrame th {
        background: var(--background-primary);
        color: var(--text-primary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 12px;
        padding: var(--spacing-md);
        border-bottom: 2px solid var(--border-light);
    }

    .stDataFrame td {
        padding: var(--spacing-md);
        border-bottom: 1px solid var(--border-light);
        font-weight: 400;
    }

    /* Alerts */
    .stAlert {
        border-radius: var(--border-radius-lg);
        border: none;
        box-shadow: var(--shadow-sm);
        font-size: 14px;
        font-weight: 500;
    }

    /* Charts */
    .stPlotlyChart {
        background: var(--background-elevated);
        border-radius: var(--border-radius-lg);
        padding: var(--spacing-lg);
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-light);
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: var(--background-elevated);
        border-radius: var(--border-radius-md);
        border: 1px solid var(--border-light);
        font-weight: 500;
    }

    .streamlit-expanderContent {
        background: var(--background-elevated);
        border: 1px solid var(--border-light);
        border-top: none;
        border-radius: 0 0 var(--border-radius-md) var(--border-radius-md);
        padding: var(--spacing-md);
    }

    /* Download buttons */
    .stDownloadButton > button {
        background: var(--success-gradient) !important;
        color: var(--text-inverse) !important;
        border: none !important;
        border-radius: var(--border-radius-md) !important;
        padding: var(--spacing-md) var(--spacing-lg) !important;
        font-weight: 500 !important;
        transition: var(--transition-fast) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stDownloadButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-md) !important;
    }

    /* Loading states */
    .stSpinner > div {
        border-top-color: #667eea !important;
        border-left-color: #667eea !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: var(--spacing-sm);
    }

    .stTabs [data-baseweb="tab"] {
        background: var(--background-elevated);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius-md);
        padding: var(--spacing-sm) var(--spacing-md);
        font-weight: 500;
        transition: var(--transition-fast);
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: var(--background-primary);
        border-color: var(--border-medium);
    }

    .stTabs [aria-selected="true"] {
        background: var(--primary-gradient) !important;
        color: var(--text-inverse) !important;
        border-color: transparent !important;
    }

    /* Code blocks */
    .stCode {
        background: var(--background-elevated);
        border: 1px solid var(--border-light);
        border-radius: var(--border-radius-md);
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
    }

    /* Responsive design */
    @media (max-width: 1024px) {
        .main .block-container {
            padding: var(--spacing-lg);
        }
        
        .executive-header h1 {
            font-size: 28px;
        }
        
        .executive-header .subtitle {
            font-size: 16px;
        }
        
        section[data-testid="stSidebar"] {
            width: 280px !important;
            min-width: 280px !important;
        }
    }

    @media (max-width: 768px) {
        .executive-header h1 {
            font-size: 24px;
        }
        
        .executive-header .subtitle {
            font-size: 14px;
        }
        
        .executive-header .status-indicator {
            position: static;
            margin-top: var(--spacing-md);
            align-self: flex-start;
        }
        
        section[data-testid="stSidebar"] .stButton > button {
            height: 48px;
            font-size: 14px;
        }

        .history-item {
            flex-direction: column;
            align-items: flex-start;
            gap: var(--spacing-sm);
        }

        .history-item-actions {
            width: 100%;
            justify-content: flex-end;
        }
    }

    /* Dark mode support */
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

    /* Accessibility improvements */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }

    /* Focus indicators for keyboard navigation */
    button:focus-visible,
    input:focus-visible,
    select:focus-visible {
        outline: 2px solid #667eea;
        outline-offset: 2px;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--background-primary);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border-medium);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--border-dark);
    }
    </style>
    """, unsafe_allow_html=True)