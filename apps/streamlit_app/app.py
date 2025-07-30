import os, io, json, time, uuid, pathlib, yaml, typing as t
import streamlit as st
import pandas as pd
from datetime import datetime
from pyspark.sql import SparkSession

# Local modules
from inference.rag import call_llm_via_gateway, embed_texts_via_gateway
from pipelines.upload_ingest import process_upload, get_spark

# --------- Config helpers ---------
def load_yaml(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def get_cfg():
    root = pathlib.Path(__file__).resolve().parents[2]  # repo root
    cfg = load_yaml(str(root / "config" / "app_config.yaml"))
    model_catalog = load_yaml(str(root / "inference" / "model_catalog.yaml"))
    return cfg, model_catalog

def ensure_session_state():
    defaults = {
        "user_id": None,
        "tenant_id": os.environ.get("APP_TENANT_ID_DEFAULT", "default"),
        "current_conv": None,
        "messages": {},
        "selected_model": None,
        "use_rag": True,
        "temperature": 0.2,
        "max_tokens": 768
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def get_user_id() -> str:
    # Prefer Spark current_user()
    try:
        spark = get_spark()
        user = spark.sql("SELECT current_user()").first()[0]
        return user
    except Exception:
        # Fallback to prompted id
        return st.session_state.get("user_id") or ""

# --------- UC paths ---------
def vol_root(cfg: dict, user_id: str) -> str:
    cat = cfg["app"]["catalog"]
    sch = cfg["app"]["schema"]
    vol = cfg["app"]["volume"]
    return f"/Volumes/{cat}/{sch}/{vol}/{user_id}"

# --------- Lakehouse tables ---------
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
    .stApp {{
      background: var(--surface);
      color: var(--text);
    }}
    .chat-bubble {{
      padding: 0.75rem 1rem;
      border-radius: var(--radius);
      margin-bottom: 0.5rem;
      border: 1px solid rgba(0,0,0,0.05);
    }}
    .chat-user {{ background: rgba(12,108,242,0.08); }}
    .chat-assistant {{ background: #fff; }}
    .chat-title {{
      font-size: 0.9rem; opacity: 0.7;
    }}
    </style>
    '''
    st.markdown(css, unsafe_allow_html=True)

# --------- Spark ---------
def get_spark():
    spark = SparkSession.getActiveSession()
    if spark is None:
        spark = SparkSession.builder.getOrCreate()
    return spark

# --------- Conversation storage ---------
def list_conversations(cfg: dict, user_id: str) -> pd.DataFrame:
    spark = get_spark()
    df = spark.sql(f"""
        SELECT conversation_id, title, model, created_at, updated_at
        FROM {tbl(cfg, 'conversations')}
        WHERE user_id = '{user_id}'
        ORDER BY updated_at DESC
    """).toPandas() if spark._jsparkSession is not None else pd.DataFrame(columns=["conversation_id","title","model","created_at","updated_at"])
    return df

def load_messages(cfg: dict, conversation_id: str) -> t.List[dict]:
    spark = get_spark()
    pdf = spark.sql(f"""
        SELECT role, content, created_at FROM {tbl(cfg, 'messages')}
        WHERE conversation_id = '{conversation_id}'
        ORDER BY created_at ASC
    """).toPandas()
    msgs = [{"role": row["role"], "content": row["content"]} for _, row in pdf.iterrows()]
    return msgs

def save_conversation(cfg: dict, conversation_id: str, user_id: str, tenant_id: str, title: str, model: str):
    spark = get_spark()
    spark.sql(f"""
      INSERT INTO {tbl(cfg, 'conversations')} VALUES (
        '{conversation_id}', '{user_id}', '{tenant_id}', '{title}', '{model}', ARRAY(), current_timestamp(), current_timestamp(), map())
    """)

def save_message(cfg: dict, conversation_id: str, role: str, content: str, tokens_in: int = 0, tokens_out: int = 0, status: str = "ok"):
    spark = get_spark()
    msg_id = str(uuid.uuid4())
    spark.sql(f"""
      INSERT INTO {tbl(cfg, 'messages')} VALUES (
        '{msg_id}', '{conversation_id}', '{role}', $${content.replace('$','\$')}$$, ARRAY(), {tokens_in}, {tokens_out}, current_timestamp(), '{status}')
    """)

# --------- UI ---------
def sidebar(cfg: dict, model_catalog: dict, user_id: str):
    with st.sidebar:
        st.markdown("### 💬 Chats")
        # Conversations list
        chats = list_conversations(cfg, user_id)
        new_chat = st.button("➕ New chat")
        selected_conv = None
        if not chats.empty:
            titles = [f"{r['title']} ({r['created_at']:%b %d})" for _, r in chats.iterrows()]
            idx = st.selectbox("Your conversations", options=list(range(len(titles))), format_func=lambda i: titles[i] if i is not None else "", index=0 if len(titles)>0 else None)
            if idx is not None:
                selected_conv = chats.iloc[idx]["conversation_id"]
        st.session_state["current_conv"] = selected_conv if selected_conv else st.session_state.get("current_conv")
        if new_chat or st.session_state.get("current_conv") is None:
            conv_id = str(uuid.uuid4())
            st.session_state["current_conv"] = conv_id
            save_conversation(cfg, conv_id, user_id, st.session_state["tenant_id"], "New Chat", st.session_state.get("selected_model") or cfg["app"]["default_llm_route"])

        st.markdown("---")
        st.markdown("### ⚙️ Model & Tools")
        models = model_catalog.get("models", [])
        model_display_to_route = {m["display_name"]: m["route"] for m in models}
        display_names = list(model_display_to_route.keys())
        current = st.session_state.get("selected_model") or cfg["app"]["default_llm_route"]
        display_default = [k for k, v in model_display_to_route.items() if v == current]
        index = display_names.index(display_default[0]) if display_default else 0
        picked = st.selectbox("Model", display_names, index=index)
        st.session_state["selected_model"] = model_display_to_route[picked]
        st.session_state["use_rag"] = st.toggle("Use my uploads (RAG)", value=True)
        st.session_state["temperature"] = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
        st.session_state["max_tokens"] = st.slider("Max output tokens", 128, 4096, 768, 64)

        st.markdown("---")
        st.markdown("### ⬆️ Upload data")
        up = st.file_uploader("CSV or Excel", type=["csv","tsv","xlsx","xls"], accept_multiple_files=False)
        if up is not None:
            info = process_upload(up.name, up.getvalue(), cfg["app"]["catalog"], cfg["app"]["schema"], cfg["app"]["volume"], st.session_state["tenant_id"])
            st.success(f"Uploaded {up.name} → {info['rows']} row(s).")

def chat_area(cfg: dict, theme: dict):
    st.markdown(f"#### {cfg['app']['title']}")
    st.caption("Chat with Databricks‑hosted models, with optional RAG on your uploads.")

    # Messages display
    conv = st.session_state["current_conv"]
    if conv:
        msgs = load_messages(cfg, conv)
        for m in msgs:
            css_class = "chat-bubble chat-user" if m["role"] == "user" else "chat-bubble chat-assistant"
            st.markdown(f'<div class="{css_class}"><div class="chat-title">{m["role"]}</div>{m["content"]}</div>', unsafe_allow_html=True)

    prompt = st.chat_input("Type your message")
    if prompt:
        # Save user message
        save_message(cfg, conv, "user", prompt)
        messages = [{"role":"system","content":"You are a helpful assistant."}]
        # Add prior conversation context
        hist = load_messages(cfg, conv)
        for h in hist:
            messages.append({"role": h["role"], "content": h["content"]})

        # TODO: If RAG enabled, retrieve top chunks and prepend as system/context
        # For MVP, we skip the actual retrieval to keep the scaffold minimal.

        # Call LLM via AI Gateway
        content, usage = call_llm_via_gateway(messages, route=st.session_state["selected_model"], max_tokens=st.session_state["max_tokens"], temperature=st.session_state["temperature"])
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)
        save_message(cfg, conv, "assistant", content, tokens_in, tokens_out)
        st.rerun()

# ---------- Main ----------
def main():
    cfg, model_catalog = get_cfg()
    ensure_session_state()

    # Resolve user id
    if not st.session_state.get("user_id"):
        # Attempt to read from Spark
        uid = get_user_id()
        if uid:
            st.session_state["user_id"] = uid

    if not st.session_state.get("user_id"):
        st.info("We couldn't determine your identity automatically. Please enter an identifier (e.g., your email).")
        manual = st.text_input("Your ID", value="", key="manual_id")
        if st.button("Set identity") and manual:
            st.session_state["user_id"] = manual

    if not st.session_state.get("user_id"):
        st.stop()

    # Load/apply theme
    theme = load_theme(cfg, st.session_state["tenant_id"])
    apply_theme(theme)

    # Layout
    sidebar(cfg, model_catalog, st.session_state["user_id"])
    chat_area(cfg, theme)

if __name__ == "__main__":
    main()
