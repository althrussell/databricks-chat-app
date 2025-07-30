import os, json, typing as t, requests
from databricks.sdk import WorkspaceClient

# ---- Workspace / Statement Execution helpers ----
def _wclient() -> WorkspaceClient:
    host = os.environ.get("APP_DATABRICKS_HOST") or os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("APP_DATABRICKS_TOKEN") or os.environ.get("DATABRICKS_TOKEN")
    if not host or not token:
        raise RuntimeError("Set APP_DATABRICKS_HOST and APP_DATABRICKS_TOKEN.")
    return WorkspaceClient(host=host, token=token)

def _warehouse_id() -> str:
    wid = os.environ.get("APP_SQL_WAREHOUSE_ID") or os.environ.get("SQL_WAREHOUSE_ID")
    if not wid:
        raise RuntimeError("Set APP_SQL_WAREHOUSE_ID with the ID of a SQL Warehouse.")
    return wid

def sql_exec(statement: str, catalog: str, schema: str, params: dict | None = None) -> dict:
    w = _wclient()
    wid = _warehouse_id()
    res = w.statement_execution.execute_and_wait(
        warehouse_id=wid,
        catalog=catalog,
        schema=schema,
        statement=statement,
        parameters=[{"name": k, "value": v} for k, v in (params or {}).items()]
    )
    return res.as_dict()

def sql_fetch_all(statement: str, catalog: str, schema: str) -> list[dict]:
    data = sql_exec(statement, catalog, schema)
    result = data.get("result", {})
    cols = [c["name"] for c in result.get("schema", {}).get("columns", [])]
    rows = []
    for r in result.get("data_array", []):
        row = {c: v for c, v in zip(cols, r)}
        rows.append(row)
    return rows

def get_current_user(catalog: str, schema: str) -> str:
    rows = sql_fetch_all("SELECT current_user() AS user", catalog, schema)
    return rows[0]["user"] if rows else "unknown_user"

# ---- Serving Endpoints ----
def _host_token():
    host = os.environ.get("APP_DATABRICKS_HOST") or os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("APP_DATABRICKS_TOKEN") or os.environ.get("DATABRICKS_TOKEN")
    return host.rstrip("/"), token

def call_llm_via_serving(messages: t.List[dict], endpoint_name: str, max_tokens: int = 512, temperature: float = 0.2, schema: str = "openai-chat", raw_template: t.Optional[dict]=None):
    host, token = _host_token()
    url = f"{host}/serving-endpoints/{endpoint_name}/invocations"
    headers = {"Authorization": f"Bearer {token}"}
    if schema == "openai-chat":
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
    elif schema == "anthropic":
        def map_msg(m):
            role = m.get("role","user")
            content = m.get("content","")
            return {"role": role, "content": [{"type":"text","text": content}] if isinstance(content, str) else content}
        payload = {
            "messages": [map_msg(m) for m in messages if m.get("role") in ("system","user","assistant")],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
    else:
        payload = raw_template or {"messages": messages, "max_tokens": max_tokens, "temperature": temperature}

    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    content = ""
    usage = {}
    if isinstance(data, dict):
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "") or data.get("output_text","")
        usage = data.get("usage", {}) or {}
    return content, usage

def _warehouse_id() -> str:
    # Prefer explicit ID
    wid = os.environ.get("APP_SQL_WAREHOUSE_ID") or os.environ.get("SQL_WAREHOUSE_ID")
    if wid:
        return wid
    # Else try name
    name = os.environ.get("APP_SQL_WAREHOUSE_NAME")
    if name:
        w = _wclient()
        for wh in w.warehouses.list():
            if wh.name == name:
                return wh.id
        raise RuntimeError(f"SQL Warehouse named '{name}' not found or not visible.")
    raise RuntimeError("Set APP_SQL_WAREHOUSE_ID (recommended) or APP_SQL_WAREHOUSE_NAME.")

