# app.py - Working Databricks Chat App with Proper Sidebar
import os
import uuid
import json
from typing import Dict, Any, List, Optional

import streamlit as st

import db
from model_serving_utils import query_endpoint_with_usage
from conversations import (
    default_title_from_prompt,
    generate_auto_title,
    export_conversation_json,
)
from analytics_utils import build_analytics_frames
from ui import inject_global_css, status_badge
from auth_utils import get_user_identity, setup_request_context

# Configure Streamlit - USE SIDEBAR
st.set_page_config(
    page_title="Databricks Chat App", 
    layout="wide", 
    page_icon="🤖",
    initial_sidebar_state="expanded"  # Use Streamlit's native sidebar
)

# Setup authentication and styling
setup_request_context()
inject_global_css()

# Much simpler CSS - work WITH Streamlit, not against it
st.markdown("""
<style>
/* Style the native Streamlit sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--background-color) 0%, var(--secondary-background-color) 100%);
    border-right: 2px solid var(--border-color);
}

section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    margin-bottom: 0.5rem;
    border: 1px solid var(--border-color);
    background: transparent;
    color: var(--text-color);
    padding: 0.75rem 1rem;
    border-radius: var(--border-radius);
    font-size: 0.9rem;
    text-align: left;
    min-height: 3rem; /* Bigger buttons */
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--secondary-background-color);
    border-color: var(--primary-color);
}

section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: var(--primary-color) !important;
    color: white !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] h3 {
    color: var(--primary-color);
    text-align: center;
}

section[data-testid="stSidebar"] h4 {
    color: var(--text-color);
    margin-top: 1.5rem;
}

/* Main content - let Streamlit handle chat input naturally */
.main .block-container {
    padding-bottom: 1rem; /* Normal padding */
}

.main-header {
    text-align: center;
    padding: 1rem 0 2rem 0;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 2rem;
}

.main-header h1 {
    color: var(--primary-color);
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
}
</style>
""", unsafe_allow_html=True)

def _call_if_exists(module, name: str, default=None):
    """Safely call optional functions on db module"""
    fn = getattr(module, name, None)
    return fn if callable(fn) else (default if callable(default) else (lambda *a, **k: default))

def get_serving_endpoints():
    """Parse and return available serving endpoints"""
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
    
    return allowed, default_idx

def initialize_session_state():
    """Initialize all session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages: List[Dict[str, Any]] = []
    if "conv_id" not in st.session_state:
        st.session_state.conv_id = str(uuid.uuid4())
    if "chat_title" not in st.session_state:
        st.session_state.chat_title = "New Chat"
    if "current_page" not in st.session_state:
        st.session_state.current_page = "chat"
    
    # Initialize endpoint selection
    allowed_endpoints, default_idx = get_serving_endpoints()
    if "selected_endpoint" not in st.session_state:
        st.session_state.selected_endpoint = allowed_endpoints[default_idx]["id"]
    
    return allowed_endpoints

def render_sidebar():
    """Render the sidebar using Streamlit's native sidebar"""
    with st.sidebar:
        # Header
        st.markdown("### :material/smart_toy: Databricks AI")
        st.caption("Powered by Serving Endpoints")
        st.markdown("---")
        
        # Navigation
        st.markdown("#### Navigation")
        
        nav_items = [
            {"key": "chat", "label": ":material/chat: Chat"},
            {"key": "history", "label": ":material/history: History"},
            {"key": "analytics", "label": ":material/analytics: Analytics"},
            {"key": "settings", "label": ":material/settings: Settings"}
        ]
        
        for item in nav_items:
            is_active = st.session_state.current_page == item["key"]
            button_type = "primary" if is_active else "secondary"
            
            if st.button(
                item["label"],
                key=f"nav_{item['key']}",
                type=button_type,
                use_container_width=True
            ):
                st.session_state.current_page = item["key"]
                st.rerun()
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("#### Quick Actions")
        
        if st.button(":material/add: New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_title = "New Chat"
            st.session_state.conv_id = str(uuid.uuid4())
            st.session_state.current_page = "chat"
            st.rerun()
        
        if st.button(":material/science: Test Model", use_container_width=True):
            test_model_endpoint()
        
        st.markdown("---")
        
        # Status
        st.markdown("#### :material/monitoring: Status")
        render_status_section()

def test_model_endpoint():
    """Test the currently selected model endpoint"""
    if not st.session_state.selected_endpoint:
        st.error("❌ No endpoint configured")
        return
    
    try:
        with st.spinner("Testing endpoint..."):
            last, _ = query_endpoint_with_usage(
                endpoint_name=st.session_state.selected_endpoint,
                messages=[{"role": "user", "content": "Reply with OK"}],
                max_tokens=4,
            )
        st.success(f"✅ {last.get('content', 'OK')[:40]}")
    except Exception as e:
        st.error(f"❌ Test failed: {e}")

def render_status_section():
    """Render status information"""
    user_identity = get_user_identity()
    
    # Status indicators
    endpoint_ok = bool(st.session_state.selected_endpoint)
    
    if endpoint_ok:
        st.success(f"**Endpoint:** {st.session_state.selected_endpoint}")
    else:
        st.error("**Endpoint:** Not configured")
    
    sql_logging_ok = bool(os.getenv("DATABRICKS_WAREHOUSE_ID"))
    if sql_logging_ok:
        st.success("**SQL Logging:** ON")
    else:
        st.warning("**SQL Logging:** OFF")
    
    auth_mode = user_identity.get("auth_mode", "APP")
    st.info(f"**Auth Mode:** {auth_mode}")
    
    # User Identity
    st.markdown("**User Info:**")
    st.write(f"📧 {user_identity.get('email', '*not available*')}")
    st.write(f"🔐 {user_identity.get('sql_user', '*n/a*')}")

def render_main_content():
    """Render the main content area"""
    # Page info with separate title and icon
    page_info = {
        "chat": {"title": st.session_state.chat_title, "icon": ":material/chat:"},
        "history": {"title": "Conversation History", "icon": ":material/history:"},
        "analytics": {"title": "Usage Analytics", "icon": ":material/analytics:"},
        "settings": {"title": "Settings", "icon": ":material/settings:"}
    }
    
    current_info = page_info.get(st.session_state.current_page, {"title": "Databricks Chat", "icon": ":material/smart_toy:"})
    
    st.markdown(f"""
    <div class="main-header">
        <h1>{current_info['icon']} {current_info['title']}</h1>
        <p style="opacity: 0.7;">Databricks AI Chat Application</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Route to appropriate page
    current_page = st.session_state.current_page
    
    if current_page == "chat":
        render_chat_page()
    elif current_page == "history":
        render_history_page()
    elif current_page == "analytics":
        render_analytics_page()
    elif current_page == "settings":
        render_settings_page()

def render_chat_page():
    """Render the main chat interface"""
    # Check if endpoint is configured
    endpoint_ok = bool(st.session_state.selected_endpoint)
    
    if not endpoint_ok:
        st.error("⚠️ No serving endpoint configured. Please check Settings.")
        return
    
    # Render chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input - Streamlit handles positioning automatically
    prompt = st.chat_input("Type your message here...")
    
    if prompt and prompt.strip():
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    
    # Handle assistant response
    if (st.session_state.messages and 
        st.session_state.messages[-1]["role"] == "user" and 
        len(st.session_state.messages) % 2 == 1):
        
        handle_assistant_response()

def handle_assistant_response():
    """Handle the assistant's response to user input"""
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Show loading state
        with message_placeholder:
            st.info(f"📡 Calling **{st.session_state.selected_endpoint}**...")
        
        # Prepare context window
        max_turns = int(os.getenv("MAX_TURNS", "12") or "12")
        window = st.session_state.messages[-max_turns:] if max_turns > 0 else st.session_state.messages
        
        try:
            # Call the endpoint
            reply_msg, usage = query_endpoint_with_usage(
                endpoint_name=st.session_state.selected_endpoint,
                messages=window,
                max_tokens=400,
            )
            
            reply_text = reply_msg.get("content", "") if isinstance(reply_msg, dict) else str(reply_msg)
            tokens_in = int(usage.get("prompt_tokens", 0)) if isinstance(usage, dict) else 0
            tokens_out = int(usage.get("completion_tokens", 0)) if isinstance(usage, dict) else 0
            
            # Display response
            message_placeholder.markdown(reply_text)
            
        except Exception as e:
            message_placeholder.error(f"❌ Error: {e}")
            reply_text = f"(error: {e})"
            tokens_in = tokens_out = 0
    
    # Add assistant message to history
    st.session_state.messages.append({"role": "assistant", "content": reply_text})
    
    # Log to database if enabled
    log_conversation_to_db(tokens_in, tokens_out)
    
    # Auto-generate title if needed
    if st.session_state.chat_title == "New Chat" and len(st.session_state.messages) >= 2:
        generate_conversation_title()
    
    st.rerun()

def log_conversation_to_db(tokens_in: int, tokens_out: int):
    """Log conversation to database if SQL logging is enabled"""
    if not os.getenv("DATABRICKS_WAREHOUSE_ID"):
        return
    
    try:
        user_identity = get_user_identity()
        user_id = user_identity.get("user_id", "unknown_user")
        
        # Ensure conversation exists
        db.ensure_conversation(
            st.session_state.conv_id,
            user_id,
            st.session_state.selected_endpoint,
            title=st.session_state.chat_title,
            email=user_identity.get("email"),
            sql_user=user_identity.get("sql_user"),
        )
        
        # Update conversation model
        db.update_conversation_model(st.session_state.conv_id, st.session_state.selected_endpoint)
        
        # Log messages
        if len(st.session_state.messages) >= 2:
            user_msg = st.session_state.messages[-2]["content"]
            assistant_msg = st.session_state.messages[-1]["content"]
            
            db.log_message(st.session_state.conv_id, "user", user_msg, tokens_in=0, tokens_out=0, status="ok")
            db.log_message(st.session_state.conv_id, "assistant", assistant_msg, 
                          tokens_in=tokens_in, tokens_out=tokens_out, status="ok")
            
            # Log usage
            db.log_usage(
                st.session_state.conv_id,
                user_id,
                st.session_state.selected_endpoint,
                tokens_in,
                tokens_out,
                email=user_identity.get("email"),
                sql_user=user_identity.get("sql_user"),
            )
    except Exception as e:
        st.error(f"Failed to log to database: {e}")

def generate_conversation_title():
    """Generate an automatic title for the conversation"""
    try:
        fallback_title = default_title_from_prompt(st.session_state.messages[0].get("content", ""))
        auto_title = generate_auto_title(
            st.session_state.selected_endpoint, 
            st.session_state.messages[:3], 
            fallback=fallback_title
        )
        st.session_state.chat_title = auto_title
        
        if os.getenv("DATABRICKS_WAREHOUSE_ID"):
            db.update_conversation_title(st.session_state.conv_id, auto_title)
    except Exception as e:
        st.error(f"Failed to generate title: {e}")

def render_history_page():
    """Render the conversation history page"""
    if not os.getenv("DATABRICKS_WAREHOUSE_ID"):
        st.info("💡 SQL logging is disabled. History is unavailable.")
        return
    
    # Search controls
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        search = st.text_input("🔍 Search conversations", placeholder="Search...")
    
    with col2:
        include_content = st.toggle("Search content", value=False)
    
    with col3:
        limit = st.number_input("Results", min_value=10, max_value=500, value=100)
    
    # Get conversations
    user_identity = get_user_identity()
    user_id = user_identity.get("user_id", "unknown_user")
    
    try:
        conversations = db.list_conversations(user_id=user_id, search=search, limit=int(limit), include_content=include_content)
        
        if not conversations:
            st.info("📝 No conversations found.")
            return
        
        # Display conversations
        for i, conv in enumerate(conversations):
            with st.expander(f"**{conv.get('title', 'Untitled')}** - {conv.get('created_at', 'Unknown date')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📂 Load", key=f"load_{i}", use_container_width=True):
                        load_conversation(conv["conversation_id"], conv.get("title", "Chat"))
                
                with col2:
                    if st.button("🗑️ Delete", key=f"del_{i}", use_container_width=True):
                        delete_conversation(conv["conversation_id"], conv.get("title", "Untitled"))
                
                with col3:
                    export_data = export_conversation_json(conv["conversation_id"])
                    st.download_button(
                        "⬇️ Export",
                        data=export_data,
                        file_name=f"conversation_{conv['conversation_id']}.json",
                        mime="application/json",
                        key=f"exp_{i}",
                        use_container_width=True
                    )
                
                st.write(f"Model: {conv.get('model', 'Unknown')} | Messages: {conv.get('messages', 0)} | Cost: ${float(conv.get('cost', 0)):.4f}")
    
    except Exception as e:
        st.error(f"❌ Failed to load history: {e}")

def load_conversation(conv_id: str, title: str):
    """Load a conversation from history"""
    try:
        messages = db.fetch_conversation_messages(conv_id)
        st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in messages]
        st.session_state.conv_id = conv_id
        st.session_state.chat_title = title
        st.session_state.current_page = "chat"
        st.success(f"✅ Loaded: {title}")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Failed to load: {e}")

def delete_conversation(conv_id: str, title: str):
    """Delete a conversation from history"""
    try:
        db.delete_conversation(conv_id)
        st.success(f"🗑️ Deleted: {title}")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Failed to delete: {e}")

def render_analytics_page():
    """Render the analytics page"""
    if not os.getenv("DATABRICKS_WAREHOUSE_ID"):
        st.info("💡 SQL logging is disabled. Analytics unavailable.")
        return
    
    try:
        user_identity = get_user_identity()
        user_id = user_identity.get("user_id", "unknown_user")
        
        totals, by_day, by_model = build_analytics_frames(user_id)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Conversations", int(totals.get("conversations", 0) or 0))
        
        with col2:
            st.metric("Events", int(totals.get("events", 0) or 0))
        
        with col3:
            tokens = int(totals.get("tokens_in", 0) or 0) + int(totals.get("tokens_out", 0) or 0)
            st.metric("Tokens", f"{tokens:,}")
        
        with col4:
            cost = float(totals.get('cost', 0.0) or 0.0)
            st.metric("Cost", f"${cost:.4f}")
        
        # Charts
        if by_day is not None and not by_day.empty:
            st.subheader("Daily Usage")
            tab1, tab2 = st.tabs(["Cost", "Tokens"])
            
            with tab1:
                st.bar_chart(by_day.set_index("day")["cost"])
            
            with tab2:
                st.line_chart(by_day.set_index("day")["tokens"])
        
        if by_model is not None and not by_model.empty:
            st.subheader("Model Breakdown")
            st.dataframe(by_model, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Analytics error: {e}")

def render_settings_page():
    """Render the settings page"""
    st.subheader("Model Configuration")
    
    allowed_endpoints, _ = get_serving_endpoints()
    names = [m["name"] for m in allowed_endpoints]
    display_to_id = {m["name"]: m["id"] for m in allowed_endpoints}
    
    try:
        current_idx = [m["id"] for m in allowed_endpoints].index(st.session_state.selected_endpoint)
    except ValueError:
        current_idx = 0
    
    picked_name = st.selectbox("Serving Endpoint", names, index=current_idx)
    picked_endpoint = display_to_id[picked_name]
    
    if picked_endpoint != st.session_state.selected_endpoint:
        st.session_state.selected_endpoint = picked_endpoint
        st.success(f"✅ Switched to **{picked_endpoint}**")
        
        if os.getenv("DATABRICKS_WAREHOUSE_ID"):
            db.update_conversation_model(st.session_state.conv_id, picked_endpoint)
    
    st.subheader("User Identity")
    user_identity = get_user_identity()
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"📧 **Email:** {user_identity.get('email', '*not available*')}")
        st.info(f"🔐 **SQL User:** {user_identity.get('sql_user', '*n/a*')}")
    
    with col2:
        st.info(f"🔑 **Auth:** {user_identity.get('auth_mode', 'APP')}")
        st.info(f"👤 **User ID:** {user_identity.get('user_id', 'unknown')}")
    
    st.subheader("Chat Management")
    
    new_title = st.text_input("Chat Title", value=st.session_state.chat_title)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Title", use_container_width=True):
            st.session_state.chat_title = new_title or "Untitled"
            if os.getenv("DATABRICKS_WAREHOUSE_ID"):
                db.update_conversation_title(st.session_state.conv_id, st.session_state.chat_title)
            st.success("✅ Title updated!")
    
    with col2:
        if os.getenv("DATABRICKS_WAREHOUSE_ID"):
            export_data = export_conversation_json(st.session_state.conv_id)
        else:
            export_data = json.dumps({"messages": st.session_state.messages}, indent=2, default=str)
        
        st.download_button(
            "⬇️ Export Chat",
            data=export_data,
            file_name=f"conversation_{st.session_state.conv_id}.json",
            mime="application/json",
            use_container_width=True
        )

def main():
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render main content
    render_main_content()

if __name__ == "__main__":
    main()