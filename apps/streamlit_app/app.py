import os, io, json, time, uuid, pathlib, yaml, typing as t
import streamlit as st
import pandas as pd
from datetime import datetime

from inference.rag import call_llm_via_serving, sql_exec, sql_fetch_all, get_current_user
from pipelines.upload_ingest import process_upload

# --------- Config helpers ---------
def load_yaml(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def get_cfg():
    here = pathlib.Path(__file__).resolve().parent  # directory containing app.py
    # Try app-local files first
    cfg_path = here / "config" / "app_config.yaml"
    mc_path  = here / "inference" / "model_catalog.yaml"
    # Also try one level up (in case packaging moved folders)
    if not cfg_path.exists():
        alt = here.parent / "config" / "app_config.yaml"
        if alt.exists():
            cfg_path = alt
    if not mc_path.exists():
        alt = here.parent / "inference" / "model_catalog.yaml"
        if alt.exists():
            mc_path = alt

    # If both files exist, load them
    if cfg_path.exists() and mc_path.exists():
        cfg = load_yaml(str(cfg_path))
        model_catalog = load_yaml(str(mc_path))
        st.caption(f"Config loaded from files: {cfg_path.name}, {mc_path.name}")
        return cfg, model_catalog

    # ---- Fallback: build config from environment variables ----
    # Minimal viable config so the app can boot even if files aren't packaged.
    st.warning("Config files not found; using environment-based defaults. Package config under apps/streamlit_app/ if you want to edit them.")
    catalog = os.environ.get("APP_CATALOG", "app_catalog")
    schema  = os.environ.get("APP_SCHEMA", "app")
    volume  = os.environ.get("APP_VOLUME", "user_files")
    allowed = [m.strip() for m in os.environ.get("APP_ALLOWED_MODEL_IDS", "sonnet-4").split(",") if m.strip()]

    cfg = {
        "app": {
            "title": "Databricks Chat App",
            "catalog": catalog,
            "schema": schema,
            "volume": volume,
            "allowed_model_ids": allowed,
            "features": {
                "enable_rag": False,
                "enable_sql_tool": False,
                "enable_budgets": True
            }
        }
    }

    # Model catalog: single model fallback (Claude Sonnet 4) unless overridden via env
    default_model = {
        "id": os.environ.get("APP_DEFAULT_MODEL_ID", "sonnet-4"),
        "display_name": os.environ.get("APP_DEFAULT_MODEL_NAME", "Claude Sonnet 4"),
        "provider": "serving",
        "endpoint": os.environ.get("APP_DEFAULT_MODEL_ENDPOINT", "databricks-claude-sonnet-4"),
        "schema": os.environ.get("APP_DEFAULT_MODEL_SCHEMA", "openai-chat"),
        "allowed": True,
        "context_window": 200000,
        "max_output_tokens": 2048
    }
    model_catalog = {"models": [default_model]}
    st.caption(f"Model catalog from env: {default_model['display_name']} → {default_model['endpoint']}")
    return cfg, model_catalog
def ensure_session_state():
    defaults = {
        "user_id": None,
        "tenant_id": "default",
        "current_conv": None,
        "selected_model_id": None,
        "temperature": 0.2,
        "max_tokens": 768
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# --------- UC helpers ---------
def vol_root(cfg: dict, user_id: str) -> str:
    cat = cfg["app"]["catalog"]
    sch = cfg["app"]["schema"]
    vol = cfg["app"]["volume"]
    return f"/Volumes/{cat}/{sch}/{vol}/{user_id}"

def tbl(cfg: dict, name: str) -> str:
    return f"{cfg['app']['catalog']}.{cfg['app']['schema']}.{name}"

# --------- Theme ---------
def load_theme(cfg: dict, tenant_id: str) -> dict:
    root = f"/Volumes/{cfg['app']['catalog']}/{cfg['app']['schema']}/{cfg['app']['volume']}/branding/{tenant_id}"
    theme_path = os.path.join(root, "theme.json")
    if os.path.exists(theme_path):
        try:
            with open(theme_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"colors": {"primary": "#0C6CF2", "surface":"#FFFFFF", "text":"#0F172A"}, "radius": 12}

def apply_theme(theme: dict):
    colors = theme.get("colors", {})
    primary = colors.get("primary", "#0C6CF2")
    surface = colors.get("surface", "#FFFFFF")
    text = colors.get("text", "#0F172A")
    radius = theme.get("radius", 12)
    css = f'''
    <style>
    :root {{
      --primary: {primary};
      --surface: {surface};
      --text: {text};
      --radius: {radius}px;
    }}
    .stApp {{ background: var(--surface); color: var(--text); }}
    .chat-bubble {{ padding: 0.75rem 1rem; border-radius: var(--radius); margin-bottom: 0.5rem; border: 1px solid rgba(0,0,0,0.05); }}
    .chat-user {{ background: rgba(12,108,242,0.08); }}
    .chat-assistant {{ background: #fff; }}
    .chat-title {{ font-size: 0.9rem; opacity: 0.7; }}
    </style>
    '''
    st.markdown(css, unsafe_allow_html=True)

# --------- Lakehouse CRUD via SQL Warehouse ---------
def list_conversations(cfg: dict, user_id: str) -> list[dict]:
    rows = sql_fetch_all(f"""
        SELECT conversation_id, title, model, created_at, updated_at
        FROM {tbl(cfg, 'conversations')}
        WHERE user_id = '{user_id}'
        ORDER BY updated_at DESC
    """, cfg["app"]["catalog"], cfg["app"]["schema"])
    return rows

def load_messages(cfg: dict, conversation_id: str) -> t.List[dict]:
    rows = sql_fetch_all(f"""
        SELECT role, content, created_at FROM {tbl(cfg, 'messages')}
        WHERE conversation_id = '{conversation_id}'
        ORDER BY created_at ASC
    """, cfg["app"]["catalog"], cfg["app"]["schema"])
    return [{"role": r["role"], "content": r["content"]} for r in rows]

def save_conversation(cfg: dict, conversation_id: str, user_id: str, tenant_id: str, title: str, model: str):
    sql_exec(f"""
      INSERT INTO {tbl(cfg, 'conversations')} VALUES (
        '{conversation_id}', '{user_id}', '{tenant_id}', '{title}', '{model}', ARRAY(), current_timestamp(), current_timestamp(), map())
    """, cfg["app"]["catalog"], cfg["app"]["schema"])

def save_message(cfg: dict, conversation_id: str, role: str, content: str, tokens_in: int = 0, tokens_out: int = 0, status: str = "ok"):
    msg_id = str(uuid.uuid4())
    escaped = content.replace("$", "\$").replace("'", "''")
    sql_exec(f"""
      INSERT INTO {tbl(cfg, 'messages')} VALUES (
        '{msg_id}', '{conversation_id}', '{role}', $${escaped}$$, ARRAY(), {tokens_in}, {tokens_out}, current_timestamp(), '{status}')
    """, cfg["app"]["catalog"], cfg["app"]["schema"])

# --------- Models ---------
def allowed_models(cfg: dict, model_catalog: dict):
    allow_ids = cfg["app"].get("allowed_model_ids", [])
    models = model_catalog.get("models", [])
    if allow_ids:
        return [m for m in models if m.get("id") in allow_ids]
    return [m for m in models if m.get("allowed", False)]

# --------- UI ---------
def sidebar(cfg: dict, model_catalog: dict, user_id: str):
    with st.sidebar:
        st.markdown("### 💬 Chats")
        chats = list_conversations(cfg, user_id)
        if st.button("➕ New chat") or st.session_state.get("current_conv") is None:
            conv_id = str(uuid.uuid4())
            st.session_state["current_conv"] = conv_id
            am = allowed_models(cfg, model_catalog)
            default_model_id = am[0]["id"] if am else ""
            st.session_state["selected_model_id"] = st.session_state.get("selected_model_id") or default_model_id
            save_conversation(cfg, conv_id, user_id, st.session_state.get("tenant_id","default"), "New Chat", st.session_state["selected_model_id"])

        selected_conv = st.session_state.get("current_conv")
        if chats:
            titles = [f"{r['title']} ({r['created_at'][:10]})" for r in chats]
            idx = st.selectbox("Your conversations", options=list(range(len(titles))), format_func=lambda i: titles[i], index=0 if len(titles)>0 else None)
            if idx is not None:
                selected_conv = chats[idx]["conversation_id"]
        st.session_state["current_conv"] = selected_conv

        st.markdown("---")
        st.markdown("### ⚙️ Model")
        am = allowed_models(cfg, model_catalog)
        if not am:
            st.error("No allowed models configured. Edit config/app_config.yaml or model_catalog.yaml.")
        else:
            name_to_id = {m["display_name"]: m["id"] for m in am}
            names = list(name_to_id.keys())
            cur_id = st.session_state.get("selected_model_id") or am[0]["id"]
            cur_name = [n for n, mid in name_to_id.items() if mid == cur_id][0]
            picked = st.selectbox("Model", names, index=names.index(cur_name))
            st.session_state["selected_model_id"] = name_to_id[picked]
            st.session_state["temperature"] = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
            st.session_state["max_tokens"] = st.slider("Max output tokens", 128, 4096, 768, 64)

        st.markdown("---")
        st.markdown("### ⬆️ Upload data")
        up = st.file_uploader("CSV or Excel", type=["csv","tsv","xlsx","xls"], accept_multiple_files=False)
        if up is not None:
            info = process_upload(up.name, up.getvalue(), cfg["app"]["catalog"], cfg["app"]["schema"], cfg["app"]["volume"], st.session_state.get("tenant_id","default"))
            st.success(f"Uploaded {up.name}. Registered tables: {', '.join(info.get('tables', [])) or 'none'}")

def chat_area(cfg: dict, model_catalog: dict, theme: dict):
    st.markdown(f"#### {cfg['app']['title']}")
    st.caption("Chat with Databricks pay‑per‑token models. (No Gateway. SQL Warehouse for storage.)")

    conv = st.session_state.get("current_conv")
    if conv:
        msgs = load_messages(cfg, conv)
        for m in msgs:
            css_class = "chat-bubble chat-user" if m["role"] == "user" else "chat-bubble chat-assistant"
            st.markdown(f'<div class="{css_class}"><div class="chat-title">{m["role"]}</div>{m["content"]}</div>', unsafe_allow_html=True)

    prompt = st.chat_input("Type your message")
    if prompt and st.session_state.get("selected_model_id"):
        save_message(cfg, conv, "user", prompt)

        # Build context
        history = load_messages(cfg, conv)
        messages = [{"role": "system", "content": "You are a helpful assistant."}] + history

        # Resolve model
        models = {m["id"]: m for m in model_catalog.get("models", [])}
        model = models[st.session_state["selected_model_id"]]
        endpoint = model["endpoint"]
        schema = model.get("schema", "openai-chat")

        # Call Serving endpoint
        content, usage = call_llm_via_serving(messages, endpoint_name=endpoint, max_tokens=st.session_state["max_tokens"], temperature=st.session_state["temperature"], schema=schema)
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)
        save_message(cfg, conv, "assistant", content, tokens_in, tokens_out)
        st.rerun()

def main():
    cfg, model_catalog = get_cfg()
    ensure_session_state()
    # Resolve user id via SQL Warehouse current_user()
    if not st.session_state.get("user_id"):
        uid = get_current_user(cfg["app"]["catalog"], cfg["app"]["schema"])
        if uid:
            st.session_state["user_id"] = uid
    if not st.session_state.get("user_id"):
        st.info("We couldn't determine your identity automatically. Please enter an identifier (e.g., your email).")
        manual = st.text_input("Your ID", value="", key="manual_id")
        if st.button("Set identity") and manual:
            st.session_state["user_id"] = manual
    if not st.session_state.get("user_id"):
        st.stop()

    theme = load_theme(cfg, st.session_state.get("tenant_id","default"))
    apply_theme(theme)
    sidebar(cfg, model_catalog, st.session_state["user_id"])
    chat_area(cfg, model_catalog, theme)

if __name__ == "__main__":
    main()
