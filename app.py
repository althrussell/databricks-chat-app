# app.py - Fixed version with sticky chat input
import os
import uuid
import json
from typing import Dict, Any, List, Optional

import streamlit as st

import db  # local persistence/analytics helpers (safe-called below)
from model_serving_utils import query_endpoint_with_usage
from conversations import (
    default_title_from_prompt,
    generate_auto_title,
    export_conversation_json,
)
from analytics_utils import build_analytics_frames
from ui import inject_global_css, status_badge

st.set_page_config(page_title="Databricks Chat App", layout="wide", page_icon="🤖")

# Inject custom CSS for sticky chat input
def inject_chat_css():
    st.markdown("""
    <style>
    /* Make the chat input sticky at bottom */
    .stChatInput {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 999 !important;
        background: var(--background-color) !important;
        border-top: 1px solid var(--border-color) !important;
        padding: 1rem !important;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1) !important;
    }
    
    /* Add padding to main content to prevent overlap */
    .main .block-container {
        padding-bottom: 120px !important;
    }
    
    /* Ensure chat messages container has proper spacing */
    .stChatMessage {
        margin-bottom: 1rem !important;
    }
    
    /* Style the chat input container */
    .stChatInput > div {
        max-width: 800px !important;
        margin: 0 auto !important;
    }
    
    /* Fix sidebar positioning */
    .css-1d391kg {
        padding-bottom: 120px !important;
    }
    
    /* Auto-scroll behavior for chat messages */
    .stChatMessage:last-child {
        scroll-margin-bottom: 150px;
    }
    </style>
    """, unsafe_allow_html=True)

inject_global_css()
inject_chat_css()

# -------- Helpers to safely call optional functions on db --------
def _call_if_exists(module, name: str, default=None):
    fn = getattr(module, name, None)
    return fn if callable(fn) else (default if callable(default) else (lambda *a, **k: default))

# -------- Serving endpoints config (tabs render even when not configured) --------
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
    allowed = [{"id": "", "name": "⚠️ Not configured"}]

default_idx = 0
if DEFAULT_ENDPOINT:
    for i, m in enumerate(allowed):
        if m["id"] == DEFAULT_ENDPOINT:
            default_idx = i
            break

# -------- Session state --------
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, Any]] = []
if "conv_id" not in st.session_state:
    st.session_state.conv_id = str(uuid.uuid4())
if "selected_endpoint" not in st.session_state:
    st.session_state.selected_endpoint = allowed[default_idx]["id"]
if "chat_title" not in st.session_state:
    st.session_state.chat_title = "New Chat"

endpoint_ok = bool(st.session_state.selected_endpoint)

# -------- Sidebar (status; configuration moved to Settings) --------
with st.sidebar:
    st.markdown(
        """
    <div style="text-align: center; padding: 1rem 0; margin-bottom: 0.75rem;">
        <h2 style="margin: 0;">📎 Status</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Safely read identity info
    get_forwarded_email = _call_if_exists(db, "get_forwarded_email", default=lambda: None)
    current_user = _call_if_exists(db, "current_user", default=lambda: None)
    get_forwarded_token = _call_if_exists(db, "get_forwarded_token", default=lambda: None)

    email = get_forwarded_email()
    sql_user = current_user() if os.getenv("DATABRICKS_WAREHOUSE_ID") else None
    mode = "USER" if (os.getenv("RUN_SQL_AS_USER", "0") == "1" and get_forwarded_token()) else "APP"

    status_badge(True, f"Endpoint: {st.session_state.selected_endpoint or '⚠️ Not configured'}")
    status_badge(
        bool(os.getenv("DATABRICKS_WAREHOUSE_ID")),
        f"SQL Logging: {'ON' if os.getenv('DATABRICKS_WAREHOUSE_ID') else 'OFF'}",
    )
    status_badge(True, f"Auth mode: {mode}")
    if not endpoint_ok:
        st.warning(
            "No serving endpoint configured. Set `SERVING_ENDPOINTS_CSV` (or `SERVING_ENDPOINT`) to enable Chat calls.",
            icon="⚠️",
        )
    st.markdown("---")

    st.markdown("### 👤 Identity")
    st.markdown(f"📧 **Email:** {email or '*not forwarded*'}")
    st.markdown(f"🔐 **SQL User:** {sql_user or '*n/a*'}")
    st.markdown("---")

    # Quick actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧪 Test model", use_container_width=True, disabled=not endpoint_ok, key="sidebar_test_model"):
            try:
                with st.spinner("Testing endpoint…"):
                    last, _ = query_endpoint_with_usage(
                        endpoint_name=st.session_state.selected_endpoint,
                        messages=[{"role": "user", "content": "Reply with OK"}],
                        max_tokens=4,
                    )
                st.success(f"✅ {last.get('content','OK')[:40]}", icon="✨")
            except Exception as e:
                st.error(f"❌ Test failed: {e}", icon="🚫")
    with col2:
        if st.button("🗑️ Clear chat", use_container_width=True, key="sidebar_clear_chat"):
            st.session_state.messages = []
            st.session_state.chat_title = "New Chat"
            st.session_state.conv_id = str(uuid.uuid4())
            st.rerun()

# -------- Header --------
st.markdown(
    f"""
<div style="text-align:center; padding: 1rem 0 0.25rem 0;">
  <h1>🤖 Databricks Chat App</h1>
  <p style="opacity:0.8">Powered by AI Serving Endpoints</p>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown("---")

# -------- Tabs --------
tab_chat, tab_history, tab_settings, tab_analytics = st.tabs(["💬 Chat", "📚 History", "⚙️ Settings", "📊 Analytics"])

# # ======================== Chat Tab ========================
# with tab_chat:
#     st.subheader(st.session_state.chat_title)

#     # Create a container for messages with custom styling
#     messages_container = st.container()
    
#     with messages_container:
#         # Render chat history
#         for i, m in enumerate(st.session_state.messages):
#             with st.chat_message(m["role"], avatar="🧑‍💻" if m["role"] == "user" else "🤖"):
#                 st.markdown(m["content"])
    
#     # Add some spacing before the input
#     st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
#     # Chat input - this will be styled to stick to bottom via CSS
#     prompt = st.chat_input("💭 Type your message here…", disabled=not endpoint_ok, key="main_chat_input")
    
#     if prompt and prompt.strip():
#         # Display user message
#         st.session_state.messages.append({"role": "user", "content": prompt})
        
#         # Rerun to show the user message immediately
#         st.rerun()

#     # Handle assistant response (only if we just added a user message)
#     if (st.session_state.messages and 
#         st.session_state.messages[-1]["role"] == "user" and 
#         len(st.session_state.messages) % 2 == 1):  # Odd number means last is user message
        
#         with st.chat_message("assistant", avatar="🤖"):
#             message_placeholder = st.empty()
#             with message_placeholder.container():
#                 st.info(f"📡 Calling endpoint **{st.session_state.selected_endpoint or 'N/A'}**…", icon="🚀")

#             # Build context window
#             max_turns = int(os.getenv("MAX_TURNS", "12") or "12")
#             window = st.session_state.messages[-max_turns:] if max_turns > 0 else st.session_state.messages

#             # Call endpoint
#             try:
#                 reply_msg, usage = query_endpoint_with_usage(
#                     endpoint_name=st.session_state.selected_endpoint,
#                     messages=window,
#                     max_tokens=400,
#                 )
#                 reply_text = reply_msg.get("content", "") if isinstance(reply_msg, dict) else str(reply_msg)
#                 tokens_in = int(usage.get("prompt_tokens", 0)) if isinstance(usage, dict) else 0
#                 tokens_out = int(usage.get("completion_tokens", 0)) if isinstance(usage, dict) else 0
#                 message_placeholder.markdown(reply_text)
#             except Exception as e:
#                 message_placeholder.error(f"❌ Serving error ({st.session_state.selected_endpoint or 'N/A'}): {e}")
#                 reply_text = f"(serving error: {e})"
#                 tokens_in = tokens_out = 0

#         st.session_state.messages.append({"role": "assistant", "content": reply_text})

#         # Post-send logging + ensure conversation exists
#         if os.getenv("DATABRICKS_WAREHOUSE_ID"):
#             get_forwarded_email = _call_if_exists(db, "get_forwarded_email", default=lambda: None)
#             current_user = _call_if_exists(db, "current_user", default=lambda: None)
#             email = get_forwarded_email()
#             sql_user = current_user()
#             user_id = email or sql_user or "unknown_user"
#             db.ensure_conversation(
#                 st.session_state.conv_id,
#                 user_id,
#                 st.session_state.selected_endpoint,
#                 title=st.session_state.chat_title,
#                 email=email,
#                 sql_user=sql_user,
#             )
#             db.update_conversation_model(st.session_state.conv_id, st.session_state.selected_endpoint)
#             db.log_message(st.session_state.conv_id, "user", st.session_state.messages[-2]["content"], tokens_in=0, tokens_out=0, status="ok")
#             db.log_message(
#                 st.session_state.conv_id, "assistant", reply_text, tokens_in=tokens_in, tokens_out=tokens_out, status="ok"
#             )
#             db.log_usage(
#                 st.session_state.conv_id,
#                 user_id,
#                 st.session_state.selected_endpoint,
#                 tokens_in,
#                 tokens_out,
#                 email=email,
#                 sql_user=sql_user,
#             )

#         # Auto-generate title after first exchange if still default
#         if st.session_state.chat_title == "New Chat" and len(st.session_state.messages) >= 2:
#             fallback_title = default_title_from_prompt(st.session_state.messages[0].get("content", ""))
#             auto_title = generate_auto_title(
#                 st.session_state.selected_endpoint, st.session_state.messages[:3], fallback=fallback_title
#             )
#             st.session_state.chat_title = auto_title
#             if os.getenv("DATABRICKS_WAREHOUSE_ID"):
#                 db.update_conversation_title(st.session_state.conv_id, auto_title)

#         # Auto-scroll to bottom using JavaScript
#         st.markdown("""
#         <script>
#         window.parent.document.querySelector('.main').scrollTo({
#             top: window.parent.document.querySelector('.main').scrollHeight,
#             behavior: 'smooth'
#         });
#         </script>
#         """, unsafe_allow_html=True)
        
#         st.rerun()
# ======================== Chat Tab ========================
with tab_chat:
    st.subheader(st.session_state.chat_title)

    messages_container = st.container()
    with messages_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"], avatar="🧑‍💻" if m["role"] == "user" else "🤖"):
                st.markdown(m["content"])

        # Scroll target div
        scroll_target = st.empty()
        scroll_target.markdown("<div id='scroll-to-bottom'></div>", unsafe_allow_html=True)

    # Conditionally scroll to bottom only if near bottom
    st.markdown("""
    <script>
    const scrollTarget = document.getElementById('scroll-to-bottom');
    const threshold = 200;  // px from bottom to still scroll
    const isNearBottom = () => {
        const scrollY = window.scrollY;
        const visible = window.innerHeight;
        const pageHeight = document.body.scrollHeight;
        return (pageHeight - (scrollY + visible)) < threshold;
    };

    if (isNearBottom() && scrollTarget) {
        scrollTarget.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    </script>
    """, unsafe_allow_html=True)

    # Chat input
    prompt = st.chat_input("💭 Type your message here…", disabled=not endpoint_ok, key="main_chat_input")

    if prompt and prompt.strip():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    if (
        st.session_state.messages and
        st.session_state.messages[-1]["role"] == "user" and
        len(st.session_state.messages) % 2 == 1
    ):
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            with message_placeholder.container():
                st.info(f"📡 Calling endpoint **{st.session_state.selected_endpoint or 'N/A'}**…", icon="🚀")

            max_turns = int(os.getenv("MAX_TURNS", "12") or "12")
            window = st.session_state.messages[-max_turns:] if max_turns > 0 else st.session_state.messages

            try:
                reply_msg, usage = query_endpoint_with_usage(
                    endpoint_name=st.session_state.selected_endpoint,
                    messages=window,
                    max_tokens=400,
                )
                reply_text = reply_msg.get("content", "") if isinstance(reply_msg, dict) else str(reply_msg)
                tokens_in = int(usage.get("prompt_tokens", 0)) if isinstance(usage, dict) else 0
                tokens_out = int(usage.get("completion_tokens", 0)) if isinstance(usage, dict) else 0
                message_placeholder.markdown(reply_text)
            except Exception as e:
                message_placeholder.error(f"❌ Serving error ({st.session_state.selected_endpoint or 'N/A'}): {e}")
                reply_text = f"(serving error: {e})"
                tokens_in = tokens_out = 0

        st.session_state.messages.append({"role": "assistant", "content": reply_text})

        if os.getenv("DATABRICKS_WAREHOUSE_ID"):
            get_forwarded_email = _call_if_exists(db, "get_forwarded_email", default=lambda: None)
            current_user = _call_if_exists(db, "current_user", default=lambda: None)
            email = get_forwarded_email()
            sql_user = current_user()
            user_id = email or sql_user or "unknown_user"
            db.ensure_conversation(
                st.session_state.conv_id,
                user_id,
                st.session_state.selected_endpoint,
                title=st.session_state.chat_title,
                email=email,
                sql_user=sql_user,
            )
            db.update_conversation_model(st.session_state.conv_id, st.session_state.selected_endpoint)
            db.log_message(st.session_state.conv_id, "user", st.session_state.messages[-2]["content"], tokens_in=0, tokens_out=0, status="ok")
            db.log_message(st.session_state.conv_id, "assistant", reply_text, tokens_in=tokens_in, tokens_out=tokens_out, status="ok")
            db.log_usage(
                st.session_state.conv_id,
                user_id,
                st.session_state.selected_endpoint,
                tokens_in,
                tokens_out,
                email=email,
                sql_user=sql_user,
            )

        if st.session_state.chat_title == "New Chat" and len(st.session_state.messages) >= 2:
            fallback_title = default_title_from_prompt(st.session_state.messages[0].get("content", ""))
            auto_title = generate_auto_title(
                st.session_state.selected_endpoint, st.session_state.messages[:3], fallback=fallback_title
            )
            st.session_state.chat_title = auto_title
            if os.getenv("DATABRICKS_WAREHOUSE_ID"):
                db.update_conversation_title(st.session_state.conv_id, auto_title)

        st.rerun()


# ====================== History Tab ======================
with tab_history:
    st.markdown("#### Browse Conversations")
    if not os.getenv("DATABRICKS_WAREHOUSE_ID"):
        st.info("Logging is disabled. History is unavailable.")
    else:
        get_forwarded_email = _call_if_exists(db, "get_forwarded_email", default=lambda: None)
        current_user = _call_if_exists(db, "current_user", default=lambda: None)
        email = get_forwarded_email()
        sql_user = current_user()
        user_id = email or sql_user or "unknown_user"

        colf1, colf2, colf3 = st.columns([3, 1, 1])
        search = colf1.text_input(
            "Search (title/model/content)", placeholder="Type keywords…", label_visibility="collapsed", key="history_search"
        )
        include_content = colf2.toggle("In content", value=False, key="history_include_content")
        limit = colf3.number_input("Limit", min_value=10, max_value=500, value=100, step=10, key="history_limit")

        rows = db.list_conversations(user_id=user_id, search=search, limit=int(limit), include_content=include_content)

        if not rows:
            st.write("No conversations yet.")
        else:
            for i, r in enumerate(rows):
                conv_id = r["conversation_id"]
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([4, 2, 2, 3])
                    c1.markdown(f"**{r.get('title','Untitled')}**")
                    c2.caption(f"🧠 {r.get('model','')}")
                    c3.caption(f"🗨️ {int(r.get('messages',0))} msgs")
                    cost = float(r.get("cost", 0.0) or 0.0)
                    c4.caption(f"💲{cost:,.4f}")

                    b1, b2, _ = st.columns(3)
                    if b1.button("↩️ Load", key=f"load_{i}_{conv_id}"):
                        msgs = db.fetch_conversation_messages(conv_id)
                        st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in msgs]
                        st.session_state.conv_id = conv_id
                        st.session_state.chat_title = r.get("title", "Chat")
                        st.session_state.selected_endpoint = r.get("model", st.session_state.selected_endpoint)
                        st.success(f"Loaded {st.session_state.chat_title}")
                        st.rerun()

                    if b2.button("🗑️ Delete", key=f"del_{i}_{conv_id}"):
                        db.delete_conversation(conv_id)
                        st.warning(f"Deleted '{r.get('title','Untitled')}'")
                        st.rerun()

                    export_payload = export_conversation_json(conv_id)
                    st.download_button(
                        "⬇️ Export JSON",
                        file_name=f"conversation_{conv_id}.json",
                        mime="application/json",
                        data=export_payload,
                        key=f"exp_{i}_{conv_id}",
                    )

# ===================== Settings Tab =====================
with tab_settings:
    st.markdown("#### Preferences & Tools")

    # Model Configuration (moved from main)
    st.markdown("##### Model Configuration")
    names = [m["name"] for m in allowed]
    display_to_id = {m["name"]: m["id"] for m in allowed}
    try:
        current_idx = [m["id"] for m in allowed].index(st.session_state.selected_endpoint)
    except ValueError:
        current_idx = default_idx
    picked_name = st.selectbox("Serving endpoint", names, index=current_idx, key="settings_endpoint_select")
    picked_endpoint = display_to_id[picked_name]

    if picked_endpoint != st.session_state.selected_endpoint:
        st.session_state.selected_endpoint = picked_endpoint
        st.info(f"✨ Switched to **{picked_endpoint or 'N/A'}**", icon="🔄")
        if os.getenv("DATABRICKS_WAREHOUSE_ID"):
            db.update_conversation_model(st.session_state.conv_id, picked_endpoint)

    st.markdown("---")

    # User identity info
    st.markdown("##### User Identity")
    get_forwarded_email = _call_if_exists(db, "get_forwarded_email", default=lambda: None)
    current_user = _call_if_exists(db, "current_user", default=lambda: None)
    get_forwarded_token = _call_if_exists(db, "get_forwarded_token", default=lambda: None)
    email = get_forwarded_email()
    sql_user = current_user() if os.getenv("DATABRICKS_WAREHOUSE_ID") else None
    mode = "USER" if (os.getenv("RUN_SQL_AS_USER", "0") == "1" and get_forwarded_token()) else "APP"
    st.write(f"📧 Email: {email or '*not forwarded*'}")
    st.write(f"🔐 SQL User: {sql_user or '*n/a*'}")
    st.write(f"🔑 SQL Auth Mode: {mode}")

    st.markdown("---")

    # Chat title editing
    st.markdown("##### Chat Title")
    new_title = st.text_input(
        "Edit current chat title",
        value=st.session_state.chat_title,
        help="Auto-generated after the first exchange.",
        key="settings_title_input",
    )
    col_t = st.columns(2)
    if col_t[0].button("💾 Save Title", key="settings_save_title"):
        st.session_state.chat_title = new_title or "Untitled"
        if os.getenv("DATABRICKS_WAREHOUSE_ID"):
            db.update_conversation_title(st.session_state.conv_id, st.session_state.chat_title)
        st.success("Title updated.")

    # Conversation export
    st.markdown("##### Conversation Export")
    exp_data = (
        export_conversation_json(st.session_state.conv_id)
        if os.getenv("DATABRICKS_WAREHOUSE_ID")
        else json.dumps({"messages": st.session_state.messages}, indent=2, default=str)
    )
    st.download_button(
        "⬇️ Export current conversation (JSON)",
        data=exp_data,
        file_name=f"conversation_{st.session_state.conv_id}.json",
        mime="application/json",
        key="settings_export_current",
    )

    st.markdown("---")

    # Quick actions
    st.markdown("##### Quick Actions")
    colq1, colq2, colq3 = st.columns(3)
    with colq1:
        if st.button("🧪 Test model", disabled=not endpoint_ok, key="settings_test_model"):
            try:
                with st.spinner("Testing endpoint…"):
                    last, _ = query_endpoint_with_usage(
                        endpoint_name=st.session_state.selected_endpoint,
                        messages=[{"role": "user", "content": "Reply with OK"}],
                        max_tokens=4,
                    )
                st.success(f"✅ {last.get('content','OK')[:40]}", icon="✨")
            except Exception as e:
                st.error(f"❌ Test failed: {e}", icon="🚫")
    with colq2:
        if st.button("🗑️ Clear this chat", key="settings_clear_chat"):
            st.session_state.messages = []
            st.session_state.chat_title = "New Chat"
            st.session_state.conv_id = str(uuid.uuid4())
            st.rerun()
    with colq3:
        if st.button("🆕 New chat", key="settings_new_chat"):
            st.session_state.messages = []
            st.session_state.chat_title = "New Chat"
            st.session_state.conv_id = str(uuid.uuid4())
            st.rerun()

# ==================== Analytics Tab ====================
with tab_analytics:
    st.markdown("#### Usage & Cost Analytics")
    if not os.getenv("DATABRICKS_WAREHOUSE_ID"):
        st.info("Logging is disabled. Analytics are unavailable.")
    else:
        get_forwarded_email = _call_if_exists(db, "get_forwarded_email", default=lambda: None)
        current_user = _call_if_exists(db, "current_user", default=lambda: None)
        email = get_forwarded_email()
        sql_user = current_user()
        user_id = email or sql_user or "unknown_user"

        totals, by_day, by_model = build_analytics_frames(user_id)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Conversations", int(totals.get("conversations", 0) or 0))
        m2.metric("Usage Events", int(totals.get("events", 0) or 0))
        tokens_in = int(totals.get("tokens_in", 0) or 0)
        tokens_out = int(totals.get("tokens_out", 0) or 0)
        m3.metric("Tokens (in/out)", f"{tokens_in:,} / {tokens_out:,}")
        m4.metric("Cost (USD)", f"${float(totals.get('cost', 0.0) or 0.0):,.4f}")

        st.markdown("---")
        st.markdown("##### Daily Cost")
        if by_day is not None and not by_day.empty:
            st.bar_chart(by_day, x="day", y="cost", use_container_width=True)
        else:
            st.caption("No daily data.")

        st.markdown("##### Tokens by Day")
        if by_day is not None and not by_day.empty:
            st.line_chart(by_day, x="day", y="tokens", use_container_width=True)
        else:
            st.caption("No token data.")

        st.markdown("##### Top Models by Cost")
        if by_model is not None and not by_model.empty:
            st.dataframe(
                by_model.rename(columns={"model": "Model", "tokens": "Tokens", "cost": "Cost", "events": "Events"}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No model breakdown.")