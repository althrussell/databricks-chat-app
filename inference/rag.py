import os, json, typing as t, requests

def _ws():
    host = os.environ.get("APP_DATABRICKS_HOST") or os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("APP_DATABRICKS_TOKEN") or os.environ.get("DATABRICKS_TOKEN")
    if not host or not token:
        raise RuntimeError("Workspace host/token not configured. Set APP_DATABRICKS_HOST and APP_DATABRICKS_TOKEN.")
    return host.rstrip("/"), token

def call_llm_via_serving(messages: t.List[dict], endpoint_name: str, max_tokens: int = 512, temperature: float = 0.2, schema: str = "openai-chat", raw_template: t.Optional[dict]=None):
    host, token = _ws()
    url = f"{host}/serving-endpoints/{endpoint_name}/invocations"
    headers = {"Authorization": f"Bearer {token}"}
    if schema == "openai-chat":
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
    elif schema == "anthropic":
        # Map OpenAI-style messages to simple Anthropic-style (text-only). Adjust as needed for tools/images.
        def map_msg(m):
            role = m.get("role","user")
            content = m.get("content","")
            # Anthropic expects list-of-content blocks per message
            return {"role": role, "content": [{"type":"text","text": content}] if isinstance(content, str) else content}
        payload = {
            "messages": [map_msg(m) for m in messages if m.get("role") in ("system","user","assistant")],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
    else:  # raw passthrough
        payload = raw_template or {"messages": messages, "max_tokens": max_tokens, "temperature": temperature}

    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    # Prefer OpenAI-like response fields
    content = ""
    usage = {}
    if isinstance(data, dict):
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "") or data.get("output_text","")
        usage = data.get("usage", {}) or {}
    return content, usage
