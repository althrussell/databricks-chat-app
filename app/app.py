import os, uuid, streamlit as st
from databricks import sql
from databricks.sdk.core import Config
from model_serving_utils import query_endpoint_with_usage

# Enhanced page configuration with beautiful styling
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
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1C2128 0%, #0D1117 100%);
    }
    
    /* Button styling */
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
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: #2D333B;
        border: 1px solid #FF6B35;
        border-radius: 8px;
    }
    
    /* Info box styling */
    .stInfo {
        background: linear-gradient(135deg, #1F6BED 0%, #0969DA 100%);
        border-radius: 8px;
        border-left: 4px solid #58A6FF;
    }
    
    /* Toast styling */
    .stToast {
        background: linear-gradient(135deg, #238636 0%, #2EA043 100%);
        border-radius: 8px;
    }
    
    /* Input box styling */
    .stTextInput > div > div > input {
        background-color: #2D333B;
        border: 2px solid transparent;
        border-radius: 8px;
        color: #F0F6FC;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #FF6B35;
        box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.2);
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-top-color: #FF6B35 !important;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-connected {
        background-color: #2EA043;
        box-shadow: 0 0 6px rgba(46, 160, 67, 0.6);
    }
    
    .status-disconnected {
        background-color: #F85149;
        box-shadow: 0 0 6px rgba(248, 81, 73, 0.6);
    }
    
    /* Card styling for sidebar sections */
    .sidebar-card {
        background: rgba(45, 51, 59, 0.8);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 107, 53, 0.2);
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

# Enhanced title with emoji and styling
st.markdown("""
<h1 class="stTitle">
    🤖 Databricks AI Chat Assistant
</h1>
<div style="text-align: center; margin-bottom: 2rem; color: #8B949E;">
    <em>Powered by Databricks Model Serving • Intelligent • Scalable • Secure</em>
</div>
""", unsafe_allow_html=True)

# --- Serving endpoints config ---
DEFAULT_ENDPOINT = os.getenv("SERVING_ENDPOINT", "")
ALLOWED_CSV = os.getenv("SERVING_ENDPOINTS_CSV", DEFAULT_ENDPOINT)
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

# --- SQL logging config ---
ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "1") == "1"
RUN_SQL_AS_USER = os.getenv("RUN_SQL_AS_USER", "0") == "1"
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID") or ""
CATALOG = os.getenv("CATALOG", "shared")
SCHEMA = os.getenv("SCHEMA", "app")
PRICE_PROMPT_PER_1K = float(os.getenv("PRICE_PROMPT_PER_1K", "0") or "0")
PRICE_COMPLETION_PER_1K = float(os.getenv("PRICE_COMPLETION_PER_1K", "0") or "0")
MAX_TURNS = int(os.getenv("MAX_TURNS", "12") or "12")

def fqn(name: str) -> str:
    return f"{CATALOG}.{SCHEMA}.{name}"

# ---- Header & auth helpers ----
def _get_header(name: str):
    try:
        h = st.context.headers.get(name)
        if h:
            return h
    except Exception:
        pass
    env_key = name.replace("-", "_").upper()
    return os.environ.get(env_key) or os.environ.get(name)

def get_forwarded_email() -> str | None:
    for key in ["X-Forwarded-Email", "x-forwarded-email", "X_FORWARDED_EMAIL", "DATABRICKS_FORWARD_EMAIL"]:
        v = _get_header(key)
        if v:
            return v
    return None

def get_forwarded_token() -> str | None:
    for key in ["X-Forwarded-Access-Token", "x-forwarded-access-token", "X_FORWARDED_ACCESS_TOKEN", "DATABRICKS_FORWARD_ACCESS_TOKEN"]:
        v = _get_header(key)
        if v:
            return v
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
            try:
                return _user_conn(tok), "user"
            except Exception:
                pass
    return _sp_conn(), "app"

def sql_exec(statement: str) -> None:
    if not _conn_ok(): return
    try:
        conn, _ = _get_conn_and_mode()
        with conn as c, c.cursor() as cur:
            cur.execute(statement)
    except Exception:
        pass

def sql_fetch_one(query: str):
    if not _conn_ok(): return None
    try:
        conn, _ = _get_conn_and_mode()
        with conn as c, c.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            return rows[0][0] if rows else None
    except Exception:
        return None

def current_user() -> str:
    u = sql_fetch_one("SELECT current_user() AS u")
    return u if u else "unknown_user"

def _esc(s: str | None) -> str:
    return (s or "").replace("'", "''")

def ensure_conversation(conv_id: str, user_id: str, model: str, title: str = "New Chat", email: str | None = None, sql_user: str | None = None):
    if not _conn_ok(): return
    esc_title = _esc(title)
    e_email = _esc(email)
    e_sql = _esc(sql_user)
    meta_expr = f"map('email','{e_email}','sql_user','{e_sql}')" if (email or sql_user) else "map()"
    sql_exec(f"""
        INSERT INTO {fqn('conversations')} (conversation_id, user_id, tenant_id, title, model, tools, created_at, updated_at, meta)
        VALUES ('{conv_id}', '{_esc(user_id)}', 'default', '{esc_title}', '{_esc(model)}', ARRAY(), current_timestamp(), current_timestamp(), {meta_expr})
    """)
    sql_exec(f"UPDATE {fqn('conversations')} SET updated_at = current_timestamp() WHERE conversation_id = '{conv_id}'")

def update_conversation_model(conv_id: str, model: str):
    if not _conn_ok(): return
    sql_exec(f"UPDATE {fqn('conversations')} SET model = '{_esc(model)}', updated_at = current_timestamp() WHERE conversation_id = '{conv_id}'")

def log_message(conv_id: str, role: str, content: str, tokens_in: int = 0, tokens_out: int = 0, status: str = "ok"):
    if not _conn_ok(): return
    sql_exec(f"""
        INSERT INTO {fqn('messages')} (message_id, conversation_id, role, content, tool_invocations, tokens_in, tokens_out, created_at, status)
        VALUES ('{uuid.uuid4()}', '{conv_id}', '{_esc(role)}', '{_esc(content)}', ARRAY(), {tokens_in}, {tokens_out}, current_timestamp(), '{_esc(status)}')
    """)

def log_usage(conv_id: str, user_id: str, model: str, tokens_in: int, tokens_out: int, email: str | None = None, sql_user: str | None = None):
    if not _conn_ok(): return
    cost = (tokens_in/1000.0)*PRICE_PROMPT_PER_1K + (tokens_out/1000.0)*PRICE_COMPLETION_PER_1K
    e_email = _esc(email)
    e_sql = _esc(sql_user)
    meta_expr = f"map('email','{e_email}','sql_user','{e_sql}')" if (email or sql_user) else "map()"
    sql_exec(f"""
        INSERT INTO {fqn('usage_events')} (event_id, conversation_id, user_id, model, tokens_in, tokens_out, cost, created_at, meta)
        VALUES ('{uuid.uuid4()}', '{conv_id}', '{_esc(user_id)}', '{_esc(model)}', {tokens_in}, {tokens_out}, {cost}, current_timestamp(), {meta_expr})
    """)

def build_context(messages, max_turns: int):
    if max_turns <= 0 or len(messages) <= max_turns:
        return messages
    return messages[-max_turns:]

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conv_id" not in st.session_state:
    st.session_state.conv_id = str(uuid.uuid4())
if "selected_endpoint" not in st.session_state:
    st.session_state.selected_endpoint = allowed[default_idx]["id"]

# --- Enhanced Sidebar ---
with st.sidebar:
    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
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
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Enhanced Identity display
    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
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
    else:
        st.markdown("📊 **Logging:** *Disabled*")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Enhanced action buttons
    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
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
            st.toast("🧹 Chat cleared successfully!", icon="✨")
            st.rerun()
    
    # Stats display
    if st.session_state.messages:
        message_count = len(st.session_state.messages)
        st.markdown(f"💬 **Messages:** {message_count}")
        st.markdown(f"🆔 **Session:** `{st.session_state.conv_id[:8]}...`")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Enhanced chat interface ---
st.markdown("### 💬 Conversation")

# Render message history with enhanced styling
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"], avatar="👤" if m["role"] == "user" else "🤖"):
        st.markdown(m["content"])

# Enhanced input handling
if prompt := st.chat_input("💭 Ask me anything about your data..."):
    # Display current model info
    st.info(f"🎯 Using model: **{st.session_state.selected_endpoint}** | 💬 Turn {len(st.session_state.messages)//2 + 1}")
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Build context window
    window = build_context(st.session_state.messages, MAX_TURNS)

    # Call the model
    try:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🧠 AI is thinking..."):
                reply_msg, usage = query_endpoint_with_usage(
                    endpoint_name=st.session_state.selected_endpoint,
                    messages=window,
                    max_tokens=400
                )
                
                reply_text = reply_msg.get("content", "") if isinstance(reply_msg, dict) else str(reply_msg)
                tokens_in = int(usage.get("prompt_tokens", 0)) if isinstance(usage, dict) else 0
                tokens_out = int(usage.get("completion_tokens", 0)) if isinstance(usage, dict) else 0
                
                st.markdown(reply_text)
                
                # Show token usage in a subtle way
                if tokens_in or tokens_out:
                    st.caption(f"🔢 Tokens: {tokens_in} in, {tokens_out} out")
                    
    except Exception as e:
        with st.chat_message("assistant", avatar="❌"):
            error_msg = f"🚨 I encountered an error: {str(e)}"
            st.error(error_msg)
            reply_text = error_msg
            tokens_in = tokens_out = 0

    # Add assistant response to session
    st.session_state.messages.append({"role": "assistant", "content": reply_text})

    # Background logging (best-effort)
    if _conn_ok():
        try:
            email = get_forwarded_email()
            sql_user = current_user()
            user_id = email or sql_user or "unknown_user"
            ensure_conversation(st.session_state.conv_id, user_id, st.session_state.selected_endpoint, email=email, sql_user=sql_user)
            update_conversation_model(st.session_state.conv_id, st.session_state.selected_endpoint)
            log_message(st.session_state.conv_id, "user", prompt, tokens_in=0, tokens_out=0, status="ok")
            log_message(st.session_state.conv_id, "assistant", reply_text, tokens_in=tokens_in, tokens_out=tokens_out, status="ok")
            log_usage(st.session_state.conv_id, user_id, st.session_state.selected_endpoint, tokens_in, tokens_out, email=email, sql_user=sql_user)
        except Exception:
            pass  # Silent fail for logging

# Enhanced footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #8B949E; font-size: 0.9rem; margin-top: 2rem;">
    <p>🚀 <strong>Databricks AI Chat Assistant</strong> | Built with ❤️ using Streamlit</p>
    <p>🔒 Your conversations are secure and logged for analytics purposes</p>
</div>
""", unsafe_allow_html=True)