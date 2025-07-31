# db.py
import os
import uuid
from typing import Any, Dict, List, Optional

from databricks import sql
from databricks.sdk.core import Config

# --- Environment / pricing / schema ---
ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "1") == "1"
RUN_SQL_AS_USER = os.getenv("RUN_SQL_AS_USER", "0") == "1"
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID") or ""
CATALOG = os.getenv("CATALOG", "shared")
SCHEMA = os.getenv("SCHEMA", "app")
PRICE_PROMPT_PER_1K = float(os.getenv("PRICE_PROMPT_PER_1K", "0") or "0")
PRICE_COMPLETION_PER_1K = float(os.getenv("PRICE_COMPLETION_PER_1K", "0") or "0")

def fqn(name: str) -> str:
    return f"{CATALOG}.{SCHEMA}.{name}"

# ---- Header & auth helpers ----
def _get_header(name: str) -> Optional[str]:
    # Streamlit doesn't officially expose request headers; rely on env if proxied
    env_key = name.replace("-", "_").upper()
    return os.environ.get(env_key) or os.environ.get(name)

def get_forwarded_email() -> Optional[str]:
    for key in ["X-Forwarded-Email", "x-forwarded-email", "X_FORWARDED_EMAIL", "DATABRICKS_FORWARD_EMAIL"]:
        v = _get_header(key)
        if v:
            return v
    return None

def get_forwarded_token() -> Optional[str]:
    for key in ["X-Forwarded-Access-Token", "x-forwarded-access-token", "X_FORWARDED_ACCESS_TOKEN", "DATABRICKS_FORWARD_ACCESS_TOKEN"]:
        v = _get_header(key)
        if v:
            return v
    return None

# ---- Connections ----
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

# ---- Exec helpers ----
def sql_exec(statement: str) -> None:
    if not _conn_ok():
        return
    try:
        conn, _ = _get_conn_and_mode()
        with conn as c, c.cursor() as cur:
            cur.execute(statement)
    except Exception:
        pass

def _rows_to_dicts(cursor, rows) -> List[Dict[str, Any]]:
    cols = [d[0] for d in cursor.description] if getattr(cursor, "description", None) else []
    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append(r)
        else:
            d = {}
            for i, v in enumerate(r):
                key = cols[i] if i < len(cols) else f"c{i}"
                d[key] = v
            out.append(d)
    return out

def sql_query(query: str) -> List[Dict[str, Any]]:
    if not _conn_ok():
        return []
    try:
        conn, _ = _get_conn_and_mode()
        with conn as c, c.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            return _rows_to_dicts(cur, rows)
    except Exception:
        return []

def sql_fetch_one(query: str):
    rows = sql_query(query)
    if rows:
        first = list(rows[0].values())[0]
        return first
    return None

def current_user() -> str:
    u = sql_fetch_one("SELECT current_user() AS u")
    return u if u else "unknown_user"

def _esc(s: Optional[str]) -> str:
    return (s or "").replace("'", "''")

# ---- Logging primitives ----
def ensure_conversation(conv_id: str, user_id: str, model: str, title: str = "New Chat", email: Optional[str] = None, sql_user: Optional[str] = None):
    if not _conn_ok():
        return
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
    if not _conn_ok():
        return
    sql_exec(f"UPDATE {fqn('conversations')} SET model = '{_esc(model)}', updated_at = current_timestamp() WHERE conversation_id = '{conv_id}'")

def update_conversation_title(conv_id: str, new_title: str):
    if not _conn_ok():
        return
    sql_exec(f"UPDATE {fqn('conversations')} SET title = '{_esc(new_title)}', updated_at = current_timestamp() WHERE conversation_id = '{conv_id}'")

def log_message(conv_id: str, role: str, content: str, tokens_in: int = 0, tokens_out: int = 0, status: str = "ok"):
    if not _conn_ok():
        return
    sql_exec(f"""
        INSERT INTO {fqn('messages')} (message_id, conversation_id, role, content, tool_invocations, tokens_in, tokens_out, created_at, status)
        VALUES ('{uuid.uuid4()}', '{conv_id}', '{_esc(role)}', '{_esc(content)}', ARRAY(), {tokens_in}, {tokens_out}, current_timestamp(), '{_esc(status)}')
    """)

def log_usage(conv_id: str, user_id: str, model: str, tokens_in: int, tokens_out: int, email: Optional[str] = None, sql_user: Optional[str] = None):
    if not _conn_ok():
        return
    cost = (tokens_in/1000.0)*PRICE_PROMPT_PER_1K + (tokens_out/1000.0)*PRICE_COMPLETION_PER_1K
    e_email = _esc(email)
    e_sql = _esc(sql_user)
    meta_expr = f"map('email','{e_email}','sql_user','{e_sql}')" if (email or sql_user) else "map()"
    sql_exec(f"""
        INSERT INTO {fqn('usage_events')} (event_id, conversation_id, user_id, model, tokens_in, tokens_out, cost, created_at, meta)
        VALUES ('{uuid.uuid4()}', '{conv_id}', '{_esc(user_id)}', '{_esc(model)}', {tokens_in}, {tokens_out}, {cost}, current_timestamp(), {meta_expr})
    """)

# ---- History APIs ----
def list_conversations(user_id: Optional[str], search: str = "", limit: int = 100, include_content: bool = False) -> List[Dict[str, Any]]:
    if not _conn_ok():
        return []
    where = ["1=1"]
    if user_id:
        where.append(f"user_id = '{_esc(user_id)}'")
    if search:
        where.append(f"(title ILIKE '%{_esc(search)}%' OR model ILIKE '%{_esc(search)}%')")
        if include_content:
            where.append(f"EXISTS (SELECT 1 FROM {fqn('messages')} m WHERE m.conversation_id = c.conversation_id AND m.content ILIKE '%{_esc(search)}%')")
    where_clause = " AND ".join(where)
    q = f"""
        SELECT c.conversation_id, c.title, c.model, c.created_at, c.updated_at,
               COALESCE(m.msg_count, 0) AS messages,
               COALESCE(u.tokens_in,0) AS tokens_in, COALESCE(u.tokens_out,0) AS tokens_out,
               COALESCE(u.cost,0.0) AS cost
        FROM {fqn('conversations')} c
        LEFT JOIN (
            SELECT conversation_id, COUNT(*) AS msg_count
            FROM {fqn('messages')}
            GROUP BY conversation_id
        ) m ON m.conversation_id = c.conversation_id
        LEFT JOIN (
            SELECT conversation_id, SUM(tokens_in) AS tokens_in, SUM(tokens_out) AS tokens_out, SUM(cost) AS cost
            FROM {fqn('usage_events')}
            GROUP BY conversation_id
        ) u ON u.conversation_id = c.conversation_id
        WHERE {where_clause}
        ORDER BY c.updated_at DESC
        LIMIT {int(limit)}
    """
    return sql_query(q.replace(f"{fqn('conversations')} c", f"{fqn('conversations')} c"))

def fetch_conversation_messages(conv_id: str) -> List[Dict[str, Any]]:
    if not _conn_ok():
        return []
    q = f"""
        SELECT role, content, created_at
        FROM {fqn('messages')}
        WHERE conversation_id = '{_esc(conv_id)}'
        ORDER BY created_at ASC
    """
    return sql_query(q)

def delete_conversation(conv_id: str):
    if not _conn_ok():
        return
    sql_exec(f"DELETE FROM {fqn('usage_events')} WHERE conversation_id = '{_esc(conv_id)}'")
    sql_exec(f"DELETE FROM {fqn('messages')} WHERE conversation_id = '{_esc(conv_id)}'")
    sql_exec(f"DELETE FROM {fqn('conversations')} WHERE conversation_id = '{_esc(conv_id)}'")

def fetch_conversation_meta(conv_id: str) -> Dict[str, Any]:
    rows = sql_query(f"""
        SELECT conversation_id, title, model, created_at, updated_at, user_id
        FROM {fqn('conversations')}
        WHERE conversation_id = '{_esc(conv_id)}'
        LIMIT 1
    """)
    return rows[0] if rows else {}
