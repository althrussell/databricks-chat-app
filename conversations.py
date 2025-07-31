# conversations.py
import json
from typing import Dict, List

from model_serving_utils import query_endpoint_with_usage
import db

def default_title_from_prompt(prompt: str) -> str:
    prompt = (prompt or "").strip().replace("\n", " ")
    if not prompt:
        return "New Chat"
    words = prompt.split()
    title = " ".join(words[:6])
    if len(words) > 6:
        title += "…"
    return title

def generate_auto_title(endpoint: str, messages: List[Dict], fallback: str) -> str:
    try:
        sys_prompt = {"role": "system", "content": "Generate a concise title (<= 6 words) for this conversation. Return title only."}
        last, _ = query_endpoint_with_usage(endpoint_name=endpoint, messages=[sys_prompt] + messages[:4], max_tokens=16)
        title = (last.get("content") or "").strip()
        title = title.strip('"').strip("'")
        if title:
            return title[:60]
    except Exception:
        pass
    return fallback[:60]

def export_conversation_json(conv_id: str) -> str:
    meta = db.fetch_conversation_meta(conv_id)
    msgs = db.fetch_conversation_messages(conv_id)
    payload = {
        "conversation": meta,
        "messages": [
            {
                "role": m["role"],
                "content": m["content"],
                "created_at": str(m["created_at"]),
            }
            for m in msgs
        ],
    }
    # Use default=str to serialize datetimes/decimals safely
    return json.dumps(payload, indent=2, default=str)
