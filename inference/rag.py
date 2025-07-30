import os, math, json, time, uuid, typing as t
import requests

# Optional Vector Search client (installed in DB runtime)
try:
    from databricks.vector_search.client import VectorSearchClient
except Exception:
    VectorSearchClient = None

def _ws():
    host = os.environ.get("APP_DATABRICKS_HOST") or os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("APP_DATABRICKS_TOKEN") or os.environ.get("DATABRICKS_TOKEN")
    if not host or not token:
        raise RuntimeError("Workspace host/token not configured. Set APP_DATABRICKS_HOST and APP_DATABRICKS_TOKEN.")
    return host.rstrip("/"), token

# ---- AI Gateway helpers ----
def call_llm_via_gateway(messages: t.List[dict], route: str, max_tokens: int = 512, temperature: float = 0.2):
    host, token = _ws()
    url = f"{host}/ai-gateway/routes/{route}/invocations"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    # Expecting OpenAI-like response from gateway
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = data.get("usage", {})
    return content, usage

def embed_texts_via_gateway(texts: t.List[str], embed_route: str) -> t.List[t.List[float]]:
    host, token = _ws()
    url = f"{host}/ai-gateway/routes/{embed_route}/invocations"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"input": texts}
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    # Expect embeddings under "data"[i]["embedding"] per OpenAI compat
    out = []
    for item in data.get("data", []):
        out.append(item.get("embedding"))
    return out

# ---- Vector Search helpers (skeleton) ----
def get_vs_client():
    if VectorSearchClient is None:
        raise RuntimeError("databricks-vectorsearch package not available in this environment.")
    host, token = _ws()
    return VectorSearchClient(workspace_url=host.replace("https://",""), personal_access_token=token)

def upsert_chunks_to_vs(index_full_name: str, chunk_ids: t.List[str], embeddings: t.List[t.List[float]], metadatas: t.List[dict]):
    vs = get_vs_client()
    # This assumes index already exists and schema matches your embedding dimension
    rows = []
    for cid, emb, meta in zip(chunk_ids, embeddings, metadatas):
        row = {"id": cid, "vector": emb}
        row.update(meta)
        rows.append(row)
    # Batch upserts
    vs.index(index_full_name).upsert(rows)

def query_vs(index_full_name: str, embedding: t.List[float], k: int = 5) -> t.List[dict]:
    vs = get_vs_client()
    res = vs.index(index_full_name).similarity_search(embedding=embedding, k=k)
    return res.get("results", [])
