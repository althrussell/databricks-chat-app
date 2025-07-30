from typing import List, Dict, Any, Tuple
from mlflow.deployments import get_deploy_client

def _parse_last_message(res: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(res, dict):
        if "messages" in res and res["messages"]:
            return res["messages"][-1]
        if "choices" in res and res["choices"]:
            return res["choices"][0].get("message", {"role":"assistant","content":""})
        if "output_text" in res:
            return {"role":"assistant","content":res["output_text"]}
    return {"role":"assistant","content":str(res)}

def query_endpoint_with_usage(endpoint_name: str, messages: List[Dict[str, Any]], max_tokens: int = 400) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    client = get_deploy_client("databricks")
    res = client.predict(endpoint=endpoint_name, inputs={"messages": messages, "max_tokens": max_tokens})
    last = _parse_last_message(res)
    usage = res.get("usage", {}) if isinstance(res, dict) else {}
    return last, usage
