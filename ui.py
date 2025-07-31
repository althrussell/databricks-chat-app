# ui.py - Enhanced UI utilities with Anthropic-inspired design
import streamlit as st

def inject_global_css():
    """Inject global CSS styles for the application"""
    st.markdown("""
    <style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables for consistent theming */
    :root {
        --primary-color: #ff6b35;
        --primary-hover: #e55a2b;
        --secondary-color: #4a5568;
        --background-primary: #0f0f23;
        --background-secondary: #1a1a2e;
        --background-tertiary: #16213e;
        --text-primary: #ffffff;
        --text-secondary: #a0aec0;
        --text-muted: #718096;
        --border-color: #2d3748;
        --border-light: #4a5568;
        --success-color: #48bb78;
        --warning-color: #ed8936;
        --error-color: #f56565;
        --info-color: #4299e1;
        --card-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --transition: all 0.2s ease-in-out;
    }
    
    /* Global styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--background-primary) 0%, var(--background-secondary) 100%);
        color: var(--text-primary);
    }
    
    /* Main content area */
    .main {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    
    .block-container {
        padding-top: 1rem;
        max-width: 1200px;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        font-weight: 600;
        letter-spacing: -0.025em;
    }
    
    h1 {
        font-size: 2.25rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--primary-color), #4299e1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h3 {
        font-size: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid var(--border-color);
        padding-bottom: 0.5rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: var(--transition);
        box-shadow: var(--card-shadow);
        min-height: 2.5rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 15px -3px rgba(255, 107, 53, 0.3);
        background: linear-gradient(135deg, var(--primary-hover), var(--primary-color));
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Secondary buttons */
    .stButton > button[kind="secondary"] {
        background: var(--background-tertiary);
        border: 1px solid var(--border-light);
        color: var(--text-secondary);
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: var(--border-light);
        color: var(--text-primary);
        border-color: var(--primary-color);
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--success-color), #38a169);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: var(--transition);
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 15px -3px rgba(72, 187, 120, 0.3);
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        background-color: var(--background-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
        font-size: 0.875rem;
        transition: var(--transition);
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > div:focus-within,
    .stNumberInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.1);
    }
    
    /* Chat input styling */
    .stChatInput {
        background: var(--background-secondary);
        border-top: 1px solid var(--border-color);
        padding: 1rem;
        margin-top: 2rem;
    }
    
    .stChatInput > div > div > div > div > input {
        background: var(--background-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        color: var(--text-primary);
        font-size: 0.875rem;
        padding: 0.75rem 1rem;
    }
    
    .stChatInput > div > div > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.1);
    }
    
    /* Chat messages */
    .stChatMessage {
        background: var(--background-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: var(--card-shadow);
    }
    
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
        border-color: var(--primary-color);
    }
    
    .stChatMessage[data-testid="assistant-message"] {
        background: var(--background-tertiary);
        border-color: var(--border-light);
    }
    
    /* Containers and cards */
    .element-container[data-testid="element-container"] > div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background: var(--background-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: var(--card-shadow);
    }
    
    /* Metrics */
    .stMetric {
        background: var(--background-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        box-shadow: var(--card-shadow);
    }
    
    .stMetric > div > div {
        color: var(--text-primary);
    }
    
    .stMetric > div > div:first-child {
        font-weight: 500;
        color: var(--text-secondary);
        font-size: 0.875rem;
    }
    
    .stMetric > div > div:nth-child(2) {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    /* Alerts */
    .stAlert {
        border-radius: 8px;
        border: none;
        box-shadow: var(--card-shadow);
    }
    
    .stAlert[data-baseweb="notification-info"] {
        background: rgba(66, 153, 225, 0.1);
        border-left: 4px solid var(--info-color);
    }
    
    .stAlert[data-baseweb="notification-success"] {
        background: rgba(72, 187, 120, 0.1);
        border-left: 4px solid var(--success-color);
    }
    
    .stAlert[data-baseweb="notification-warning"] {
        background: rgba(237, 137, 54, 0.1);
        border-left: 4px solid var(--warning-color);
    }
    
    .stAlert[data-baseweb="notification-error"] {
        background: rgba(245, 101, 101, 0.1);
        border-left: 4px solid var(--error-color);
    }
    
    /* Dataframes */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: var(--card-shadow);
    }
    
    .stDataFrame table {
        background: var(--background-tertiary);
        color: var(--text-primary);
    }
    
    .stDataFrame th {
        background: var(--background-secondary);
        color: var(--text-primary);
        font-weight: 600;
        border-bottom: 1px solid var(--border-color);
    }
    
    .stDataFrame td {
        border-bottom: 1px solid var(--border-color);
    }
    
    /* Charts */
    .stPlotlyChart, .stPyplotChart {
        background: var(--background-tertiary);
        border-radius: 8px;
        padding: 1rem;
        box-shadow: var(--card-shadow);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: var(--primary-color) !important;
    }
    
    /* Toggle */
    .stCheckbox > label > div[data-testid="stWidgetLabel"] {
        color: var(--text-secondary);
        font-weight: 500;
    }
    
    /* Dividers */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        margin: 1.5rem 0;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        h1 {
            font-size: 1.875rem;
        }
        
        .stButton > button {
            font-size: 0.8rem;
            padding: 0.4rem 0.8rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def inject_sidebar_css():
    """Inject CSS specific to sidebar styling"""
    st.markdown("""
    <style>
    /* Sidebar styling */
    .css-1d391kg, .css-1lcbmhc, .css-17eq0hr, section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--background-secondary) 0%, var(--background-tertiary) 100%);
        border-right: 1px solid var(--border-color);
        box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Sidebar header */
    .css-1d391kg h2, .css-1lcbmhc h2 {
        color: var(--text-primary);
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100%;
        margin-bottom: 0.5rem;
        text-align: left;
        justify-content: flex-start;
        background: transparent;
        border: 1px solid var(--border-color);
        color: var(--text-secondary);
        font-weight: 500;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: var(--background-tertiary);
        border-color: var(--primary-color);
        color: var(--text-primary);
        transform: none;
        box-shadow: none;
    }
    
    /* Active navigation item */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
        border-color: var(--primary-color);
        color: white;
        font-weight: 600;
    }
    
    section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--primary-hover), var(--primary-color));
    }
    
    /* Sidebar metrics and info */
    section[data-testid="stSidebar"] .stMetric {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--border-color);
        margin-bottom: 0.5rem;
    }
    
    /* Sidebar text */
    section[data-testid="stSidebar"] .stMarkdown {
        color: var(--text-secondary);
        font-size: 0.875rem;
    }
    
    section[data-testid="stSidebar"] .stMarkdown strong {
        color: var(--text-primary);
    }
    
    /* Sidebar dividers */
    section[data-testid="stSidebar"] hr {
        background: var(--border-color);
    }
    
    /* Navigation section styling */
    .nav-section {
        margin-bottom: 1rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }
    
    .nav-section h4 {
        margin-bottom: 0.5rem;
        color: var(--text-primary);
        font-size: 1rem;
        font-weight: 600;
    }
    
    /* Status indicators in sidebar */
    .sidebar-status {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
        padding: 0.5rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 6px;
        border: 1px solid var(--border-color);
    }
    
    .sidebar-status .status-dot {
        margin-right: 0.5rem;
    }
    
    .sidebar-status .status-text {
        font-size: 0.8rem;
        color: var(--text-secondary);
    }
    </style>
    """, unsafe_allow_html=True)

def status_badge(is_ok: bool, label: str, variant: str = "default"):
    """
    Render a status badge with appropriate styling.
    
    Args:
        is_ok: Whether the status is positive/successful
        label: Text to display
        variant: Style variant ('default', 'sidebar', 'compact')
    """
    status_color = "var(--success-color)" if is_ok else "var(--error-color)"
    
    if variant == "sidebar":
        st.markdown(f"""
        <div class="sidebar-status">
            <div class="status-dot" style="
                width: 8px; 
                height: 8px; 
                border-radius: 50%; 
                background: {status_color};
                margin-right: 8px;
            "></div>
            <span class="status-text">{label}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Default inline badge
        st.markdown(f"""
        <div style="
            display: inline-flex; 
            align-items: center; 
            margin-bottom: 0.5rem;
            padding: 0.25rem 0.5rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            border: 1px solid var(--border-color);
        ">
            <div style="
                width: 8px; 
                height: 8px; 
                border-radius: 50%; 
                background: {status_color};
                margin-right: 8px;
            "></div>
            <span style="font-size: 0.875rem; color: var(--text-secondary);">{label}</span>
        </div>
        """, unsafe_allow_html=True)

def create_info_card(title: str, content: str, icon: str = "ℹ️", variant: str = "default"):
    """
    Create a styled information card.
    
    Args:
        title: Card title
        content: Card content
        icon: Icon to display
        variant: Style variant ('default', 'success', 'warning', 'error')
    """
    color_map = {
        "default": "var(--info-color)",
        "success": "var(--success-color)", 
        "warning": "var(--warning-color)",
        "error": "var(--error-color)"
    }
    
    border_color = color_map.get(variant, color_map["default"])
    
    st.markdown(f"""
    <div style="
        background: var(--background-tertiary);
        border: 1px solid var(--border-color);
        border-left: 4px solid {border_color};
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: var(--card-shadow);
    ">
        <div style="
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
        ">
            <span style="font-size: 1.2rem; margin-right: 0.5rem;">{icon}</span>
            <h4 style="
                margin: 0;
                color: var(--text-primary);
                font-weight: 600;
                font-size: 1rem;
            ">{title}</h4>
        </div>
        <p style="
            margin: 0;
            color: var(--text-secondary);
            font-size: 0.875rem;
            line-height: 1.5;
        ">{content}</p>
    </div>
    """, unsafe_allow_html=True)

def create_metric_card(title: str, value: str, delta: str = None, icon: str = "📊"):
    """
    Create a styled metric card.
    
    Args:
        title: Metric title
        value: Metric value
        delta: Optional delta/change value
        icon: Icon to display
    """
    delta_html = ""
    if delta:
        delta_color = "var(--success-color)" if not delta.startswith("-") else "var(--error-color)"
        delta_html = f"""
        <div style="
            color: {delta_color};
            font-size: 0.8rem;
            font-weight: 500;
            margin-top: 0.25rem;
        ">{delta}</div>
        """
    
    st.markdown(f"""
    <div style="
        background: var(--background-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        box-shadow: var(--card-shadow);
        text-align: center;
    ">
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
        <div style="
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.25rem;
        ">{title}</div>
        <div style="
            color: var(--text-primary);
            font-size: 1.5rem;
            font-weight: 700;
        ">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)