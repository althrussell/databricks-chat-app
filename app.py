import os, uuid, streamlit as st
from databricks import sql
from databricks.sdk.core import Config
from model_serving_utils import query_endpoint_with_usage

st.set_page_config(page_title="Databricks Chat App", layout="wide", page_icon="🤖")

# Custom CSS for beautiful UI
st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding-top: 2rem;
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #5B8DEE 0%, #7C3AED 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(91, 141, 238, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(91, 141, 238, 0.4);
    }
    
    /* Select box styling */
    .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Chat input styling */
    .stChatInput > div {
        border-radius: 25px;
        border: 2px solid rgba(91, 141, 238, 0.3);
        background-color: rgba(255, 255, 255, 0.05);
    }
    
    /* Info/Error message styling */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid;
    }
    
    /* Title gradient */
    h1 {
        background: linear-gradient(90deg, #5B8DEE 0%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    /* Improve readability */
    .element-container {
        margin-bottom: 1rem;
    }
    
    /* Loading spinner custom color */
    .stSpinner > div {
        border-top-color: #5B8DEE !important;
    }
    
    /* Custom divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #5B8DEE, transparent);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header with gradient and icon
st.markdown("""
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">
        🤖 Databricks Chat App
    </h1>
    <p style="font-size: 1.2rem; opacity: 0.8;">
        Powered by AI Serving Endpoints
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

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
    st.error("❌ No serving endpoints configured. Set SERVING_ENDPOINTS_CSV in app.yaml.", icon="🚫")
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
SCHEMA  = os.getenv("SCHEMA", "app")
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

# --- Sidebar ---
with st.sidebar:
    # Logo/Header section
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; margin-bottom: 2rem;">
        <h2 style="color: #5B8DEE; margin: 0;">⚙️ Configuration</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Model selection with better styling
    st.markdown("### 🎯 Model Selection")
    names = [m["name"] for m in allowed]
    display_to_id = {m["name"]: m["id"] for m in allowed}
    try:
        current_idx = [m["id"] for m in allowed].index(st.session_state.selected_endpoint)
    except ValueError:
        current_idx = default_idx
    picked_name = st.selectbox("Serving endpoint", names, index=current_idx, label_visibility="collapsed")
    picked_endpoint = display_to_id[picked_name]

    if picked_endpoint != st.session_state.selected_endpoint:
        st.session_state.selected_endpoint = picked_endpoint
        st.info(f"✨ Switched to **{picked_endpoint}**", icon="🔄")
        update_conversation_model(st.session_state.conv_id, picked_endpoint)

    st.markdown("---")

    # Identity section with icons
    st.markdown("### 👤 Identity & Logging")
    email = get_forwarded_email()
    sql_user = current_user() if _conn_ok() else None
    mode = "USER" if (RUN_SQL_AS_USER and get_forwarded_token()) else "APP"
    
    with st.container():
        if email:
            st.markdown(f"📧 **Email:** {email}")
        else:
            st.markdown("📧 **Email:** *(not forwarded)*")
            
        if sql_user:
            st.markdown(f"🔐 **SQL User:** {sql_user}")
        else:
            st.markdown("🔐 **SQL User:** *(n/a)*")
            
        if _conn_ok():
            st.markdown(f"💾 **Logging to:** `{CATALOG}.{SCHEMA}`")
            st.markdown(f"🔑 **SQL Auth:** {mode}")
        else:
            st.markdown("💾 **Logging:** Disabled")

    st.markdown("---")
    
    # Action buttons with better spacing
    st.markdown("### 🎬 Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧪 Test endpoint", use_container_width=True):
            try:
                with st.spinner("Testing..."):
                    last, _ = query_endpoint_with_usage(
                        endpoint_name=st.session_state.selected_endpoint,
                        messages=[{"role":"user","content":"Reply with OK"}],
                        max_tokens=4,
                    )
                st.success(f"✅ Endpoint responded: {last.get('content','<no content>')[:40]}", icon="✨")
            except Exception as e:
                st.error(f"❌ Test failed: {str(e)}", icon="🚫")
    
    with col2:
        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conv_id = str(uuid.uuid4())
            st.rerun()

# --- Render history ---
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🧑‍💻" if m["role"] == "user" else "🤖"):
        st.markdown(m["content"])

# --- Input ---
prompt = st.chat_input("💭 Type your message here...")
if prompt and prompt.strip():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        
        # Show calling endpoint info
        with message_placeholder.container():
            st.info(f"🚀 Calling endpoint: **{st.session_state.selected_endpoint}**", icon="📡")

        window = build_context(st.session_state.messages, MAX_TURNS)

        # Serve first, then log
        try:
            reply_msg, usage = query_endpoint_with_usage(
                endpoint_name=st.session_state.selected_endpoint,
                messages=window,
                max_tokens=400
            )
            reply_text = reply_msg.get("content", "") if isinstance(reply_msg, dict) else str(reply_msg)
            tokens_in = int(usage.get("prompt_tokens", 0)) if isinstance(usage, dict) else 0
            tokens_out = int(usage.get("completion_tokens", 0)) if isinstance(usage, dict) else 0
            
            # Clear the info message and show response
            message_placeholder.markdown(reply_text)
            
        except Exception as e:
            message_placeholder.error(f"❌ Serving error ({st.session_state.selected_endpoint}): {e}")
            reply_text = f"(serving error: {e})"
            tokens_in = tokens_out = 0

    st.session_state.messages.append({"role": "assistant", "content": reply_text})

    # Post-send logging (best-effort)
    if _conn_ok():
        email = get_forwarded_email()
        sql_user = current_user()
        user_id = email or sql_user or "unknown_user"
        ensure_conversation(st.session_state.conv_id, user_id, st.session_state.selected_endpoint, email=email, sql_user=sql_user)
        update_conversation_model(st.session_state.conv_id, st.session_state.selected_endpoint)
        log_message(st.session_state.conv_id, "user", prompt, tokens_in=0, tokens_out=0, status="ok")
        log_message(st.session_state.conv_id, "assistant", reply_text, tokens_in=tokens_in, tokens_out=tokens_out, status="ok")
        log_usage(st.session_state.conv_id, user_id, st.session_state.selected_endpoint, tokens_in, tokens_out, email=email, sql_user=sql_user)