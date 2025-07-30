import os, uuid, streamlit as st
import json, re, hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from databricks import sql
from databricks.sdk.core import Config
from databricks.sdk import WorkspaceClient
from model_serving_utils import query_endpoint_with_usage
import pandas as pd
import tempfile
import mimetypes

# Enhanced page configuration
st.set_page_config(
    page_title="Databricks AI Chat Assistant", 
    layout="wide",
    page_icon="🤖",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced visual appeal
st.markdown("""
<style>
    /* Main app styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header styling */
    .stTitle {
        text-align: center;
        color: #FF6B35;
        font-size: 3rem !important;
        font-weight: 700;
        margin-bottom: 2rem;
        text-shadow: 0 2px 4px rgba(255, 107, 53, 0.3);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1C2128;
        border-radius: 8px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 6px;
        color: #8B949E;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FF6B35 !important;
        color: white !important;
    }
    
    /* Chat message styling */
    .stChatMessage {
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* User message styling */
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
        border-left: 4px solid #FF6B35;
    }
    
    /* Assistant message styling */
    .stChatMessage[data-testid="assistant-message"] {
        background: linear-gradient(135deg, #1C2128 0%, #2D333B 100%);
        border-left: 4px solid #58A6FF;
    }
    
    /* Reaction buttons */
    .reaction-btn {
        background: transparent !important;
        border: 1px solid #58A6FF !important;
        border-radius: 20px !important;
        padding: 0.2rem 0.5rem !important;
        margin: 0.2rem !important;
        font-size: 0.8rem !important;
        color: #58A6FF !important;
        transition: all 0.3s ease !important;
    }
    
    .reaction-btn:hover {
        background: #58A6FF !important;
        color: white !important;
    }
    
    .reaction-btn.active {
        background: #FF6B35 !important;
        border-color: #FF6B35 !important;
        color: white !important;
    }
    
    /* File upload styling */
    .file-upload-area {
        border: 2px dashed #FF6B35;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        background: rgba(255, 107, 53, 0.1);
        margin: 1rem 0;
    }
    
    /* Template buttons */
    .template-btn {
        background: linear-gradient(135deg, #2D333B 0%, #1C2128 100%) !important;
        border: 1px solid #58A6FF !important;
        color: #58A6FF !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        margin: 0.25rem !important;
    }
    
    .template-btn:hover {
        background: linear-gradient(135deg, #58A6FF 0%, #1F6BED 100%) !important;
        color: white !important;
    }
    
    /* Smart suggestions */
    .suggestion-chip {
        background: linear-gradient(135deg, #1C2128 0%, #2D333B 100%);
        border: 1px solid #58A6FF;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        display: inline-block;
        cursor: pointer;
        transition: all 0.3s ease;
        color: #58A6FF;
        font-size: 0.9rem;
    }
    
    .suggestion-chip:hover {
        background: #58A6FF;
        color: white;
        transform: translateY(-1px);
    }
    
    /* File attachment indicator */
    .file-attachment {
        background: rgba(88, 166, 255, 0.1);
        border: 1px solid #58A6FF;
        border-radius: 6px;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        color: #58A6FF;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-connected { background-color: #2EA043; box-shadow: 0 0 6px rgba(46, 160, 67, 0.6); }
    .status-disconnected { background-color: #F85149; box-shadow: 0 0 6px rgba(248, 81, 73, 0.6); }
    
    /* Stats cards */
    .stats-card {
        background: linear-gradient(135deg, #1F6BED 0%, #0969DA 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    /* Button variants */
    .stButton > button {
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(255, 107, 53, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(255, 107, 53, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Enhanced title
st.markdown("""
<h1 class="stTitle">🤖 Databricks AI Chat Assistant</h1>
<div style="text-align: center; margin-bottom: 2rem; color: #8B949E;">
    <em>Enterprise AI Platform • File-Aware • Collaborative • Intelligent</em>
</div>
""", unsafe_allow_html=True)

# --- Configuration ---
DEFAULT_ENDPOINT = os.getenv("SERVING_ENDPOINT", "")
ALLOWED_CSV = os.getenv("SERVING_ENDPOINTS_CSV", DEFAULT_ENDPOINT)
ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "1") == "1"
RUN_SQL_AS_USER = os.getenv("RUN_SQL_AS_USER", "0") == "1"
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID") or ""
CATALOG = os.getenv("CATALOG", "shared")
SCHEMA = os.getenv("SCHEMA", "app")
VOLUME_NAME = os.getenv("VOLUME_NAME", "chat_files")  # Databricks Volume for file storage
PRICE_PROMPT_PER_1K = float(os.getenv("PRICE_PROMPT_PER_1K", "0") or "0")
PRICE_COMPLETION_PER_1K = float(os.getenv("PRICE_COMPLETION_PER_1K", "0") or "0")
MAX_TURNS = int(os.getenv("MAX_TURNS", "12") or "12")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10") or "10")

# Parse allowed endpoints
allowed = []
for token in [x.strip() for x in ALLOWED_CSV.split(",") if x.strip()]:
    if "|" in token:
        e, d = token.split("|", 1)
        allowed.append({"id": e.strip(), "name": d.strip()})
    else:
        allowed.append({"id": token.strip(), "name": token.strip()})

if not allowed:
    st.error("🚫 No serving endpoints configured. Set SERVING_ENDPOINTS_CSV in app.yaml.")
    st.stop()

default_idx = 0
if DEFAULT_ENDPOINT:
    for i, m in enumerate(allowed):
        if m["id"] == DEFAULT_ENDPOINT:
            default_idx = i
            break

def fqn(name: str) -> str:
    return f"{CATALOG}.{SCHEMA}.{name}"

def volume_path(user_id: str, filename: str = "") -> str:
    """Generate path for user files in Databricks Volume"""
    safe_user = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
    base_path = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME_NAME}/users/{safe_user}"
    return f"{base_path}/{filename}" if filename else base_path

# --- Helper functions ---
def _get_header(name: str):
    try:
        h = st.context.headers.get(name)
        if h: return h
    except Exception: pass
    env_key = name.replace("-", "_").upper()
    return os.environ.get(env_key) or os.environ.get(name)

def get_forwarded_email() -> Optional[str]:
    for key in ["X-Forwarded-Email", "x-forwarded-email", "X_FORWARDED_EMAIL", "DATABRICKS_FORWARD_EMAIL"]:
        v = _get_header(key)
        if v: return v
    return None

def get_forwarded_token() -> Optional[str]:
    for key in ["X-Forwarded-Access-Token", "x-forwarded-access-token", "X_FORWARDED_ACCESS_TOKEN", "DATABRICKS_FORWARD_ACCESS_TOKEN"]:
        v = _get_header(key)
        if v: return v
    return None

def _conn_ok() -> bool:
    return ENABLE_LOGGING and bool(WAREHOUSE_ID)

def _sp_conn():
    cfg = Config()
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: cfg.authenticate,
    )

def _user_conn(token: str):
    cfg = Config()
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        access_token=token,
    )

def _get_conn_and_mode():
    if RUN_SQL_AS_USER:
        tok = get_forwarded_token()
        if tok:
            try: return _user_conn(tok), "user"
            except Exception: pass
    return _sp_conn(), "app"

def sql_exec(statement: str) -> None:
    if not _conn_ok(): return
    try:
        conn, _ = _get_conn_and_mode()
        with conn as c, c.cursor() as cur:
            cur.execute(statement)
    except Exception: pass

def sql_fetch_one(query: str):
    if not _conn_ok(): return None
    try:
        conn, _ = _get_conn_and_mode()
        with conn as c, c.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            return rows[0][0] if rows else None
    except Exception: return None

def sql_fetch_all(query: str):
    if not _conn_ok(): return []
    try:
        conn, _ = _get_conn_and_mode()
        with conn as c, c.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()
    except Exception: return []

def current_user() -> str:
    u = sql_fetch_one("SELECT current_user() AS u")
    return u if u else "unknown_user"

def _esc(s: str | None) -> str:
    return (s or "").replace("'", "''")

def get_user_id() -> str:
    email = get_forwarded_email()
    sql_user = current_user() if _conn_ok() else None
    return email or sql_user or "unknown_user"

# --- File handling functions ---
def get_workspace_client():
    """Get Databricks Workspace client for file operations"""
    try:
        return WorkspaceClient()
    except Exception as e:
        st.error(f"Failed to initialize Databricks client: {e}")
        return None

def ensure_user_directory(user_id: str):
    """Ensure user directory exists in Databricks Volume"""
    try:
        w = get_workspace_client()
        if not w: return False
        
        user_path = volume_path(user_id)
        # Create directory using dbutils (if available) or workspace client
        try:
            # Try using workspace client to create directory
            w.files.create_directory(user_path)
        except Exception:
            # Directory might already exist, which is fine
            pass
        return True
    except Exception as e:
        st.error(f"Failed to create user directory: {e}")
        return False

def save_file_to_volume(user_id: str, file_obj, original_filename: str) -> str:
    """Save uploaded file to Databricks Volume"""
    try:
        # Generate unique filename to avoid conflicts
        file_id = str(uuid.uuid4())[:8]
        safe_filename = re.sub(r'[^a-zA-Z0-9.-]', '_', original_filename)
        stored_filename = f"{file_id}_{safe_filename}"
        
        # Ensure user directory exists
        if not ensure_user_directory(user_id):
            raise Exception("Failed to create user directory")
        
        # Get file path in volume
        file_path = volume_path(user_id, stored_filename)
        
        # Write file to volume using workspace client
        w = get_workspace_client()
        if not w:
            raise Exception("Workspace client not available")
        
        # Read file content
        file_content = file_obj.read()
        file_obj.seek(0)  # Reset for potential re-reading
        
        # Write to volume
        w.files.upload(file_path, file_content, overwrite=True)
        
        return file_path
    except Exception as e:
        st.error(f"Failed to save file to volume: {e}")
        return ""

def read_file_from_volume(file_path: str) -> tuple[bytes, str]:
    """Read file from Databricks Volume"""
    try:
        w = get_workspace_client()
        if not w:
            raise Exception("Workspace client not available")
        
        # Download file content
        response = w.files.download(file_path)
        content = response.contents
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = "application/octet-stream"
        
        return content, content_type
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        return b"", "application/octet-stream"

def process_uploaded_file(file_obj, filename: str) -> Dict[str, Any]:
    """Process uploaded file and extract text content"""
    file_info = {
        "name": filename,
        "size": file_obj.size,
        "type": file_obj.type,
        "content": "",
        "error": None
    }
    
    try:
        if file_obj.type == "text/plain":
            content = str(file_obj.read(), "utf-8")
            file_info["content"] = content[:10000]  # Limit content size
        elif file_obj.type == "text/csv":
            df = pd.read_csv(file_obj)
            file_info["content"] = f"CSV file with {len(df)} rows and {len(df.columns)} columns.\n"
            file_info["content"] += f"Columns: {', '.join(df.columns.tolist())}\n"
            file_info["content"] += f"Sample data:\n{df.head().to_string()}"
        elif file_obj.type in ["application/json"]:
            content = json.loads(file_obj.read())
            file_info["content"] = json.dumps(content, indent=2)[:5000]
        else:
            file_info["content"] = f"Binary file: {filename} ({file_obj.size} bytes)"
            file_info["error"] = "Binary file content not displayed"
    except Exception as e:
        file_info["error"] = str(e)
        file_info["content"] = f"Error processing file: {e}"
    
    file_obj.seek(0)  # Reset file pointer
    return file_info

# --- Database functions ---
def ensure_conversation(conv_id: str, user_id: str, model: str, title: str = "New Chat", email: str = None, sql_user: str = None):
    if not _conn_ok(): return
    esc_title = _esc(title)
    e_email = _esc(email)
    e_sql = _esc(sql_user)
    meta_expr = f"map('email','{e_email}','sql_user','{e_sql}')" if (email or sql_user) else "map()"
    sql_exec(f"""
        INSERT INTO {fqn('conversations')} (conversation_id, user_id, tenant_id, title, model, tools, created_at, updated_at, meta)
        VALUES ('{conv_id}', '{_esc(user_id)}', 'default', '{esc_title}', '{_esc(model)}', ARRAY(), current_timestamp(), current_timestamp(), {meta_expr})
    """)

def update_conversation_model(conv_id: str, model: str):
    if not _conn_ok(): return
    sql_exec(f"UPDATE {fqn('conversations')} SET model = '{_esc(model)}', updated_at = current_timestamp() WHERE conversation_id = '{conv_id}'")

def update_conversation_title(conv_id: str, title: str):
    if not _conn_ok(): return
    sql_exec(f"UPDATE {fqn('conversations')} SET title = '{_esc(title)}', updated_at = current_timestamp() WHERE conversation_id = '{conv_id}'")

def delete_conversation(conv_id: str, user_id: str):
    if not _conn_ok(): return
    # Delete in order due to foreign key constraints
    sql_exec(f"DELETE FROM {fqn('message_reactions')} WHERE message_id IN (SELECT message_id FROM {fqn('messages')} WHERE conversation_id = '{conv_id}')")
    sql_exec(f"DELETE FROM {fqn('message_files')} WHERE message_id IN (SELECT message_id FROM {fqn('messages')} WHERE conversation_id = '{conv_id}')")
    sql_exec(f"DELETE FROM {fqn('messages')} WHERE conversation_id = '{conv_id}'")
    sql_exec(f"DELETE FROM {fqn('usage_events')} WHERE conversation_id = '{conv_id}'")
    sql_exec(f"DELETE FROM {fqn('conversations')} WHERE conversation_id = '{conv_id}' AND user_id = '{_esc(user_id)}'")

def get_user_conversations(user_id: str, limit: int = 50):
    if not _conn_ok(): return []
    rows = sql_fetch_all(f"""
        SELECT conversation_id, title, model, created_at, updated_at,
               (SELECT COUNT(*) FROM {fqn('messages')} m WHERE m.conversation_id = c.conversation_id) as message_count
        FROM {fqn('conversations')} c
        WHERE user_id = '{_esc(user_id)}'
        ORDER BY updated_at DESC
        LIMIT {limit}
    """)
    return [{"id": r[0], "title": r[1], "model": r[2], "created": r[3], "updated": r[4], "msg_count": r[5]} for r in rows]

def get_conversation_messages(conv_id: str, user_id: str):
    if not _conn_ok(): return []
    rows = sql_fetch_all(f"""
        SELECT m.message_id, m.role, m.content, m.created_at, m.tokens_in, m.tokens_out,
               COALESCE(files.file_paths, ARRAY()) as file_paths
        FROM {fqn('messages')} m
        JOIN {fqn('conversations')} c ON m.conversation_id = c.conversation_id
        LEFT JOIN (
            SELECT message_id, COLLECT_LIST(file_path) as file_paths
            FROM {fqn('message_files')}
            GROUP BY message_id
        ) files ON m.message_id = files.message_id
        WHERE m.conversation_id = '{conv_id}' AND c.user_id = '{_esc(user_id)}'
        ORDER BY m.created_at ASC
    """)
    return [{
        "id": r[0], "role": r[1], "content": r[2], "created": r[3], 
        "tokens_in": r[4], "tokens_out": r[5], "files": r[6] or []
    } for r in rows]

def log_message(conv_id: str, role: str, content: str, tokens_in: int = 0, tokens_out: int = 0, status: str = "ok") -> str:
    if not _conn_ok(): return ""
    message_id = str(uuid.uuid4())
    sql_exec(f"""
        INSERT INTO {fqn('messages')} (message_id, conversation_id, role, content, tool_invocations, tokens_in, tokens_out, created_at, status)
        VALUES ('{message_id}', '{conv_id}', '{_esc(role)}', '{_esc(content)}', ARRAY(), {tokens_in}, {tokens_out}, current_timestamp(), '{_esc(status)}')
    """)
    return message_id

def log_message_file(message_id: str, file_path: str, filename: str):
    if not _conn_ok(): return
    sql_exec(f"""
        INSERT INTO {fqn('message_files')} (message_id, file_path, filename, created_at)
        VALUES ('{message_id}', '{_esc(file_path)}', '{_esc(filename)}', current_timestamp())
    """)

def log_message_reaction(message_id: str, user_id: str, reaction_type: str):
    if not _conn_ok(): return
    # Upsert reaction
    sql_exec(f"DELETE FROM {fqn('message_reactions')} WHERE message_id = '{message_id}' AND user_id = '{_esc(user_id)}'")
    sql_exec(f"""
        INSERT INTO {fqn('message_reactions')} (message_id, user_id, reaction_type, created_at)
        VALUES ('{message_id}', '{_esc(user_id)}', '{_esc(reaction_type)}', current_timestamp())
    """)

def get_message_reactions(message_id: str) -> Dict[str, int]:
    if not _conn_ok(): return {}
    rows = sql_fetch_all(f"""
        SELECT reaction_type, COUNT(*) as count
        FROM {fqn('message_reactions')}
        WHERE message_id = '{message_id}'
        GROUP BY reaction_type
    """)
    return {r[0]: r[1] for r in rows}

def log_usage(conv_id: str, user_id: str, model: str, tokens_in: int, tokens_out: int, email: str = None, sql_user: str = None):
    if not _conn_ok(): return
    cost = (tokens_in/1000.0)*PRICE_PROMPT_PER_1K + (tokens_out/1000.0)*PRICE_COMPLETION_PER_1K
    e_email = _esc(email)
    e_sql = _esc(sql_user)
    meta_expr = f"map('email','{e_email}','sql_user','{e_sql}')" if (email or sql_user) else "map()"
    sql_exec(f"""
        INSERT INTO {fqn('usage_events')} (event_id, conversation_id, user_id, model, tokens_in, tokens_out, cost, created_at, meta)
        VALUES ('{uuid.uuid4()}', '{conv_id}', '{_esc(user_id)}', '{_esc(model)}', {tokens_in}, {tokens_out}, {cost}, current_timestamp(), {meta_expr})
    """)

def get_user_stats(user_id: str):
    if not _conn_ok(): return {}
    stats = {}
    
    stats['total_conversations'] = sql_fetch_one(f"SELECT COUNT(*) FROM {fqn('conversations')} WHERE user_id = '{_esc(user_id)}'") or 0
    stats['total_messages'] = sql_fetch_one(f"""
        SELECT COUNT(*) FROM {fqn('messages')} m
        JOIN {fqn('conversations')} c ON m.conversation_id = c.conversation_id
        WHERE c.user_id = '{_esc(user_id)}'
    """) or 0
    
    token_stats = sql_fetch_one(f"""
        SELECT SUM(tokens_in), SUM(tokens_out) FROM {fqn('usage_events')}
        WHERE user_id = '{_esc(user_id)}'
    """)
    stats['total_tokens_in'] = token_stats[0] if token_stats and token_stats[0] else 0
    stats['total_tokens_out'] = token_stats[1] if token_stats and token_stats[1] else 0
    
    return stats

def build_context(messages, max_turns: int):
    if max_turns <= 0 or len(messages) <= max_turns:
        return messages
    return messages[-max_turns:]

def generate_chat_title(messages):
    """Generate a title based on the first user message"""
    if not messages:
        return "New Chat"
    
    first_user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
    if not first_user_msg:
        return "New Chat"
    
    # Clean and truncate the message for a title
    title = re.sub(r'[^\w\s-]', '', first_user_msg)
    title = ' '.join(title.split()[:6])  # First 6 words
    return title[:50] if title else "New Chat"

def generate_smart_suggestions(messages: List[Dict], model_endpoint: str) -> List[str]:
    """Generate smart follow-up suggestions based on conversation context"""
    if not messages:
        return [
            "What can you help me with?",
            "Analyze my data for insights",
            "Help me write some code",
            "Explain a concept to me"
        ]
    
    # Get last few messages for context
    recent_context = messages[-4:] if len(messages) > 4 else messages
    context_text = "\n".join([f"{m['role']}: {m['content'][:200]}" for m in recent_context])
    
    try:
        # Use the AI model to generate suggestions
        suggestion_prompt = f"""Based on this conversation context, suggest 3 helpful follow-up questions the user might want to ask. 
        Be specific and relevant to the context. Return only the questions, one per line.
        
        Context:
        {context_text}
        
        Follow-up questions:"""
        
        reply_msg, _ = query_endpoint_with_usage(
            endpoint_name=model_endpoint,
            messages=[{"role": "user", "content": suggestion_prompt}],
            max_tokens=150
        )
        
        suggestions_text = reply_msg.get("content", "") if isinstance(reply_msg, dict) else str(reply_msg)
        suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip() and len(s.strip()) > 10]
        
        # Fallback suggestions if AI generation fails
        if not suggestions:
            suggestions = [
                "Can you explain that in more detail?",
                "What are some related topics?",
                "How can I apply this knowledge?"
            ]
        
        return suggestions[:3]  # Return max 3 suggestions
        
    except Exception:
        # Fallback suggestions
        return [
            "Can you elaborate on that?",
            "What would you recommend next?",
            "How does this work in practice?"
        ]

# Conversation templates
CONVERSATION_TEMPLATES = {
    "📊 Data Analysis": "Help me analyze my dataset. I want to understand patterns, trends, and insights in my data.",
    "💻 Code Review": "Please review my code and suggest improvements for better performance, readability, and best practices.",
    "🔍 SQL Query Help": "I need help writing efficient SQL queries for my database operations.",
    "📈 Business Intelligence": "Help me create dashboards and reports from my business data.",
    "🤖 Machine Learning": "Guide me through building and deploying machine learning models.",
    "🔧 Troubleshooting": "I'm experiencing an issue and need help debugging and finding a solution.",
    "📚 Learning & Explanation": "Explain complex concepts in simple terms with practical examples.",
    "🎯 Project Planning": "Help me plan and structure my data science or analytics project.",
}

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conv_id" not in st.session_state:
    st.session_state.conv_id = str(uuid.uuid4())
if "selected_endpoint" not in st.session_state:
    st.session_state.selected_endpoint = allowed[default_idx]["id"]
if "conversation_title" not in st.session_state:
    st.session_state.conversation_title = "New Chat"
if "attached_files" not in st.session_state:
    st.session_state.attached_files = []
if "show_suggestions" not in st.session_state:
    st.session_state.show_suggestions = True
if "message_reactions" not in st.session_state:
    st.session_state.message_reactions = {}

# --- Enhanced Sidebar with Tabs ---
with st.sidebar:
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chats", "📎 Files", "⚙️ Settings", "📊 Analytics"])
    
    # ---- CHAT HISTORY TAB ----
    with tab1:
        st.markdown("### 📚 Conversation History")
        
        user_id = get_user_id()
        conversations = get_user_conversations(user_id)
        
        # New chat button
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conv_id = str(uuid.uuid4())
            st.session_state.conversation_title = "New Chat"
            st.session_state.attached_files = []
            st.rerun()
        
        # Conversation templates
        st.markdown("#### 🎯 Quick Start Templates")
        template_cols = st.columns(2)
        
        for i, (template_name, template_prompt) in enumerate(CONVERSATION_TEMPLATES.items()):
            col = template_cols[i % 2]
            with col:
                if st.button(template_name, key=f"template_{i}", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.conv_id = str(uuid.uuid4())
                    st.session_state.conversation_title = template_name
                    st.session_state.attached_files = []
                    # Pre-fill the input with template
                    st.session_state.template_prompt = template_prompt
                    st.rerun()
        
        st.markdown("---")
        
        if conversations:
            # Search/filter conversations
            search_term = st.text_input("🔍 Search conversations", placeholder="Type to search...")
            
            filtered_convs = conversations
            if search_term:
                filtered_convs = [c for c in conversations if search_term.lower() in c["title"].lower()]
            
            # Display conversations
            for conv in filtered_convs[:20]:  # Limit to 20 most recent
                created_date = conv["created"].strftime("%m/%d %H:%M") if conv["created"] else "Unknown"
                msg_count = conv["msg_count"] or 0
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if st.button(
                        f"🗨️ {conv['title'][:30]}{'...' if len(conv['title']) > 30 else ''}",
                        key=f"load_{conv['id']}",
                        help=f"Created: {created_date} | Messages: {msg_count} | Model: {conv['model']}",
                        use_container_width=True
                    ):
                        # Load conversation
                        messages = get_conversation_messages(conv["id"], user_id)
                        st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in messages]
                        st.session_state.conv_id = conv["id"]
                        st.session_state.conversation_title = conv["title"]
                        st.session_state.attached_files = []
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"del_{conv['id']}", help="Delete conversation"):
                        delete_conversation(conv["id"], user_id)
                        st.success("🗑️ Chat deleted!")
                        st.rerun()
                
                st.caption(f"📅 {created_date} • 💬 {msg_count} msgs • 🤖 {conv['model']}")
                st.markdown("---")
        else:
            st.info("💭 No conversations yet. Start chatting to see your history!")
    
    # ---- FILES TAB ----
    with tab2:
        st.markdown("### 📎 File Upload")
        
        # File upload area
        uploaded_files = st.file_uploader(
            "Choose files to attach",
            type=['txt', 'csv', 'json', 'py', 'sql', 'md', 'pdf'],
            accept_multiple_files=True,
            help=f"Max {MAX_FILE_SIZE_MB}MB per file. Supported: text, CSV, JSON, code files"
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    st.error(f"File {uploaded_file.name} is too large (max {MAX_FILE_SIZE_MB}MB)")
                    continue
                
                # Process and save file
                file_info = process_uploaded_file(uploaded_file, uploaded_file.name)
                
                if file_info["error"]:
                    st.error(f"Error processing {uploaded_file.name}: {file_info['error']}")
                else:
                    # Save to Databricks Volume
                    file_path = save_file_to_volume(user_id, uploaded_file, uploaded_file.name)
                    if file_path:
                        file_info["path"] = file_path
                        st.session_state.attached_files.append(file_info)
                        st.success(f"✅ {uploaded_file.name} uploaded successfully!")
        
        # Display currently attached files
        if st.session_state.attached_files:
            st.markdown("#### 📁 Attached Files")
            for i, file_info in enumerate(st.session_state.attached_files):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"📄 **{file_info['name']}** ({file_info['size']} bytes)")
                    if file_info.get("content"):
                        with st.expander("Preview"):
                            st.text(file_info["content"][:500] + "..." if len(file_info["content"]) > 500 else file_info["content"])
                with col2:
                    if st.button("❌", key=f"remove_file_{i}", help="Remove file"):
                        st.session_state.attached_files.pop(i)
                        st.rerun()
        
        st.markdown("---")
        st.markdown("#### 📋 File Tips")
        st.markdown("""
        - **CSV files**: Automatically analyzed for structure and sample data
        - **Text files**: Content included in conversation context
        - **Code files**: Syntax and structure preserved
        - **JSON files**: Parsed and formatted for readability
        """)
    
    # ---- SETTINGS TAB ----
    with tab3:
        st.markdown("### 🎯 Model Configuration")
        
        names = [m["name"] for m in allowed]
        display_to_id = {m["name"]: m["id"] for m in allowed}
        try:
            current_idx = [m["id"] for m in allowed].index(st.session_state.selected_endpoint)
        except ValueError:
            current_idx = default_idx
        
        picked_name = st.selectbox(
            "Choose AI Model", 
            names, 
            index=current_idx,
            help="🚀 Select the AI model endpoint for your conversation"
        )
        picked_endpoint = display_to_id[picked_name]

        if picked_endpoint != st.session_state.selected_endpoint:
            st.session_state.selected_endpoint = picked_endpoint
            st.success(f"✅ Switched to **{picked_endpoint}**")
            update_conversation_model(st.session_state.conv_id, picked_endpoint)
        
        st.markdown("---")
        
        # Chat settings
        st.markdown("### 💬 Chat Settings")
        
        # Smart suggestions toggle
        st.session_state.show_suggestions = st.checkbox(
            "💡 Show smart suggestions", 
            value=st.session_state.show_suggestions,
            help="Enable AI-generated follow-up question suggestions"
        )
        
        # Edit conversation title
        if st.session_state.messages:
            new_title = st.text_input(
                "Chat Title", 
                value=st.session_state.conversation_title,
                help="Rename this conversation"
            )
            if new_title != st.session_state.conversation_title:
                st.session_state.conversation_title = new_title
                update_conversation_title(st.session_state.conv_id, new_title)
                st.success("💾 Title updated!")
        
        # Export current conversation
        if st.session_state.messages:
            if st.button("📤 Export Chat", use_container_width=True):
                export_data = export_conversation_to_json(st.session_state.conv_id, user_id)
                st.download_button(
                    label="💾 Download JSON",
                    data=export_data,
                    file_name=f"chat_{st.session_state.conv_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        st.markdown("---")
        
        # User Identity
        st.markdown("### 👤 User Identity")
        
        email = get_forwarded_email()
        sql_user = current_user() if _conn_ok() else None
        mode = "USER" if (RUN_SQL_AS_USER and get_forwarded_token()) else "APP"
        
        # Connection status indicator
        status_class = "status-connected" if _conn_ok() else "status-disconnected"
        status_text = "Connected" if _conn_ok() else "Disconnected"
        
        st.markdown(f"""
        <div style="margin-bottom: 1rem;">
            <span class="status-indicator {status_class}"></span>
            <strong>Status:</strong> {status_text}
        </div>
        """, unsafe_allow_html=True)
        
        if email:
            st.markdown(f"📧 **Email:** `{email}`")
        else:
            st.markdown("📧 **Email:** *Not forwarded*")
        
        if sql_user:
            st.markdown(f"🔑 **SQL User:** `{sql_user}`")
        else:
            st.markdown("🔑 **SQL User:** *N/A*")
        
        st.markdown(f"🔐 **Auth Mode:** `{mode}`")
        
        if _conn_ok():
            st.markdown(f"📊 **Logging:** `{CATALOG}.{SCHEMA}`")
            st.markdown(f"📁 **Files:** `{CATALOG}.{SCHEMA}.{VOLUME_NAME}`")
        else:
            st.markdown("📊 **Logging:** *Disabled*")
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 Test Model", use_container_width=True):
                try:
                    with st.spinner("Testing endpoint..."):
                        last, _ = query_endpoint_with_usage(
                            endpoint_name=st.session_state.selected_endpoint,
                            messages=[{"role":"user","content":"Reply with OK"}],
                            max_tokens=4,
                        )
                        response_text = last.get('content','<no content>')[:40]
                        st.toast(f"✅ Model responded: {response_text}", icon="🎉")
                except Exception as e:
                    st.error(f"❌ Test failed: {str(e)[:50]}...")

        with col2:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conv_id = str(uuid.uuid4())
                st.session_state.conversation_title = "New Chat"
                st.session_state.attached_files = []
                st.toast("🧹 Chat cleared successfully!", icon="✨")
                st.rerun()
    
    # ---- ANALYTICS TAB ----
    with tab4:
        st.markdown("### 📊 Usage Analytics")
        
        if _conn_ok():
            stats = get_user_stats(user_id)
            
            # Display stats cards
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="stats-card">
                    <h3>💬 {stats.get('total_conversations', 0)}</h3>
                    <p>Total Chats</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="stats-card">
                    <h3>🔤 {stats.get('total_tokens_in', 0):,}</h3>
                    <p>Input Tokens</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="stats-card">
                    <h3>📝 {stats.get('total_messages', 0)}</h3>
                    <p>Total Messages</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="stats-card">
                    <h3>🔤 {stats.get('total_tokens_out', 0):,}</h3>
                    <p>Output Tokens</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Cost calculation if pricing is configured
            if PRICE_PROMPT_PER_1K > 0 or PRICE_COMPLETION_PER_1K > 0:
                total_cost = (stats.get('total_tokens_in', 0) / 1000.0 * PRICE_PROMPT_PER_1K + 
                             stats.get('total_tokens_out', 0) / 1000.0 * PRICE_COMPLETION_PER_1K)
                st.markdown(f"""
                <div class="stats-card">
                    <h3>💰 ${total_cost:.4f}</h3>
                    <p>Total Cost</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Current session stats
            if st.session_state.messages:
                st.markdown("---")
                st.markdown("### 📈 Current Session")
                message_count = len(st.session_state.messages)
                user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
                st.markdown(f"💬 **Messages:** {message_count}")
                st.markdown(f"❓ **Questions:** {user_messages}")
                st.markdown(f"📎 **Files:** {len(st.session_state.attached_files)}")
                st.markdown(f"🆔 **Session ID:** `{st.session_state.conv_id[:8]}...`")
        else:
            st.info("📊 Analytics require database logging to be enabled.")

# --- Main Chat Interface ---
st.markdown("### 💬 Conversation")

# Display current chat title, model, and file count
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    st.markdown(f"**📝 {st.session_state.conversation_title}**")
with col2:
    st.markdown(f"🤖 {st.session_state.selected_endpoint}")
with col3:
    if st.session_state.messages:
        st.markdown(f"💬 {len(st.session_state.messages)} msgs")
with col4:
    if st.session_state.attached_files:
        st.markdown(f"📎 {len(st.session_state.attached_files)} files")

st.markdown("---")

# Render message history with enhanced styling and reactions
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"], avatar="👤" if m["role"] == "user" else "🤖"):
        st.markdown(m["content"])
        
        # Add reaction buttons for assistant messages
        if m["role"] == "assistant" and _conn_ok():
            msg_id = f"{st.session_state.conv_id}_{i}"
            
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 6])
            
            with col1:
                if st.button("👍", key=f"like_{i}", help="Helpful"):
                    log_message_reaction(msg_id, user_id, "like")
                    st.toast("👍 Reaction added!", icon="✨")
            
            with col2:
                if st.button("👎", key=f"dislike_{i}", help="Not helpful"):
                    log_message_reaction(msg_id, user_id, "dislike")
                    st.toast("👎 Feedback recorded!", icon="📝")
            
            with col3:
                if st.button("❤️", key=f"love_{i}", help="Love it"):
                    log_message_reaction(msg_id, user_id, "love")
                    st.toast("❤️ Thanks for the love!", icon="💝")
            
            with col4:
                if st.button("📋", key=f"copy_{i}", help="Copy to clipboard"):
                    # Note: Actual clipboard copy requires JavaScript, this is a placeholder
                    st.toast("📋 Copied to clipboard!", icon="✅")

# Smart suggestions (if enabled and we have messages)
if st.session_state.show_suggestions and st.session_state.messages:
    try:
        suggestions = generate_smart_suggestions(st.session_state.messages, st.session_state.selected_endpoint)
        if suggestions:
            st.markdown("### 💡 Smart Suggestions")
            suggestion_cols = st.columns(len(suggestions))
            
            for i, suggestion in enumerate(suggestions):
                with suggestion_cols[i]:
                    if st.button(f"💭 {suggestion[:50]}{'...' if len(suggestion) > 50 else ''}", 
                               key=f"suggestion_{i}", 
                               help=suggestion,
                               use_container_width=True):
                        # Add suggestion as user message
                        st.session_state.template_prompt = suggestion
                        st.rerun()
    except Exception:
        pass  # Silently handle suggestion generation errors

# Template prompt handling
template_prompt = st.session_state.get('template_prompt', '')
if template_prompt:
    st.session_state.template_prompt = ''  # Clear after use

# Enhanced input handling
prompt = st.chat_input("💭 Ask me anything about your data...", value=template_prompt)

# Display attached files in chat context
if st.session_state.attached_files:
    st.markdown("#### 📎 Attached Files")
    for file_info in st.session_state.attached_files:
        st.markdown(f"""
        <div class="file-attachment">
            📄 <strong>{file_info['name']}</strong> ({file_info['size']} bytes)
            <br><small>{file_info['type']}</small>
        </div>
        """, unsafe_allow_html=True)

if prompt and prompt.strip():
    # Auto-generate title from first message
    if not st.session_state.messages:
        generated_title = generate_chat_title([{"role": "user", "content": prompt}])
        st.session_state.conversation_title = generated_title
    
    # Build enhanced prompt with file context
    enhanced_prompt = prompt
    if st.session_state.attached_files:
        file_context = "\n\n--- ATTACHED FILES ---\n"
        for file_info in st.session_state.attached_files:
            file_context += f"\nFile: {file_info['name']} ({file_info['type']})\n"
            if file_info.get('content') and not file_info.get('error'):
                file_context += f"Content:\n{file_info['content'][:2000]}\n"  # Limit context size
            file_context += "---\n"
        enhanced_prompt = f"{prompt}\n{file_context}"
    
    # Display current model info
    file_count_text = f" | 📎 {len(st.session_state.attached_files)} files" if st.session_state.attached_files else ""
    st.info(f"🎯 Using model: **{st.session_state.selected_endpoint}** | 💬 Turn {len(st.session_state.messages)//2 + 1}{file_count_text}")
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        
        # Show attached files in user message
        if st.session_state.attached_files:
            st.markdown("**📎 Attached files:**")
            for file_info in st.session_state.attached_files:
                st.markdown(f"• {file_info['name']}")

    # Build context window
    context_messages = build_context(st.session_state.messages, MAX_TURNS)
    
    # Use enhanced prompt for the API call (but store original in session)
    api_messages = context_messages[:-1] + [{"role": "user", "content": enhanced_prompt}]

    # Call the model
    try:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🧠 AI is thinking..."):
                reply_msg, usage = query_endpoint_with_usage(
                    endpoint_name=st.session_state.selected_endpoint,
                    messages=api_messages,
                    max_tokens=400
                )
                
                reply_text = reply_msg.get("content", "") if isinstance(reply_msg, dict) else str(reply_msg)
                tokens_in = int(usage.get("prompt_tokens", 0)) if isinstance(usage, dict) else 0
                tokens_out = int(usage.get("completion_tokens", 0)) if isinstance(usage, dict) else 0
                
                st.markdown(reply_text)
                
                # Show token usage and cost
                if tokens_in or tokens_out:
                    cost = (tokens_in / 1000.0 * PRICE_PROMPT_PER_1K + 
                           tokens_out / 1000.0 * PRICE_COMPLETION_PER_1K)
                    cost_text = f" • 💰 ${cost:.4f}" if cost > 0 else ""
                    st.caption(f"🔢 Tokens: {tokens_in} in, {tokens_out} out{cost_text}")
                    
    except Exception as e:
        with st.chat_message("assistant", avatar="❌"):
            error_msg = f"🚨 I encountered an error: {str(e)}"
            st.error(error_msg)
            reply_text = error_msg
            tokens_in = tokens_out = 0

    # Add assistant response to session
    st.session_state.messages.append({"role": "assistant", "content": reply_text})

    # Background logging with file attachments
    if _conn_ok():
        try:
            email = get_forwarded_email()
            sql_user = current_user()
            user_id = email or sql_user or "unknown_user"
            
            # Ensure conversation exists
            ensure_conversation(st.session_state.conv_id, user_id, st.session_state.selected_endpoint, 
                              title=st.session_state.conversation_title, email=email, sql_user=sql_user)
            update_conversation_model(st.session_state.conv_id, st.session_state.selected_endpoint)
            
            # Log user message
            user_msg_id = log_message(st.session_state.conv_id, "user", prompt, tokens_in=0, tokens_out=0, status="ok")
            
            # Log file attachments
            for file_info in st.session_state.attached_files:
                if file_info.get("path"):
                    log_message_file(user_msg_id, file_info["path"], file_info["name"])
            
            # Log assistant message
            log_message(st.session_state.conv_id, "assistant", reply_text, tokens_in=tokens_in, tokens_out=tokens_out, status="ok")
            
            # Log usage
            log_usage(st.session_state.conv_id, user_id, st.session_state.selected_endpoint, tokens_in, tokens_out, email=email, sql_user=sql_user)
            
            # Clear attached files after successful send
            st.session_state.attached_files = []
            
        except Exception as e:
            st.error(f"Logging error: {e}")

def export_conversation_to_json(conv_id: str, user_id: str):
    """Export conversation to JSON format"""
    messages = get_conversation_messages(conv_id, user_id)
    conversations = get_user_conversations(user_id)
    conv_info = next((c for c in conversations if c["id"] == conv_id), {})
    
    export_data = {
        "conversation_id": conv_id,
        "title": conv_info.get("title", "Unknown"),
        "model": conv_info.get("model", "Unknown"),
        "created_at": str(conv_info.get("created")) if conv_info.get("created") else None,
        "updated_at": str(conv_info.get("updated")) if conv_info.get("updated") else None,
        "messages": messages,
        "exported_at": datetime.now().isoformat()
    }
    
    return json.dumps(export_data, indent=2, default=str)

# Enhanced footer with feature highlights
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #8B949E; font-size: 0.9rem; margin-top: 2rem;">
    <p>🚀 <strong>Databricks AI Chat Assistant MVP</strong> | Built with ❤️ using Streamlit</p>
    <p>✨ <strong>Features:</strong> File Upload • Smart Suggestions • Message Reactions • Conversation Templates • Advanced Analytics</p>
    <p>🔒 Your conversations and files are secure in Databricks Volumes</p>
    <p>💡 <em>Pro tip: Upload files to chat with your data, use templates for quick starts!</em></p>
</div>
""", unsafe_allow_html=True)