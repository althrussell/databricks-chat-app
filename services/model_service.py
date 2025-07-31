# services/model_service.py - Model endpoint management service
import os
from typing import List, Dict, Tuple, Any
from model_serving_utils import query_endpoint_with_usage

class ModelService:
    """Handles model endpoint operations"""
    
    def get_available_endpoints(self) -> Tuple[List[Dict[str, str]], int]:
        """Get list of available model endpoints"""
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
            allowed = [{"id": "", "name": "Not configured"}]
        
        # Find default index
        default_idx = 0
        if DEFAULT_ENDPOINT:
            for i, m in enumerate(allowed):
                if m["id"] == DEFAULT_ENDPOINT:
                    default_idx = i
                    break
        
        return allowed, default_idx
    
    def test_endpoint(self, endpoint_name: str) -> Tuple[bool, str]:
        """Test if an endpoint is working"""
        if not endpoint_name:
            return False, "No endpoint specified"
        
        try:
            last, _ = query_endpoint_with_usage(
                endpoint_name=endpoint_name,
                messages=[{"role": "user", "content": "Reply with OK"}],
                max_tokens=4,
            )
            message = last.get('content', 'OK')[:40]
            return True, message
        except Exception as e:
            return False, str(e)
    
    def generate_response(self, endpoint_name: str, messages: List[Dict[str, Any]]) -> Tuple[str, int, int]:
        """Generate a response from the model"""
        if not endpoint_name:
            raise ValueError("No endpoint configured")
        
        # Prepare context window
        max_turns = int(os.getenv("MAX_TURNS", "12") or "12")
        window = messages[-max_turns:] if max_turns > 0 else messages
        
        # Call endpoint
        reply_msg, usage = query_endpoint_with_usage(
            endpoint_name=endpoint_name,
            messages=window,
            max_tokens=400,
        )
        
        reply_text = reply_msg.get("content", "") if isinstance(reply_msg, dict) else str(reply_msg)
        tokens_in = int(usage.get("prompt_tokens", 0)) if isinstance(usage, dict) else 0
        tokens_out = int(usage.get("completion_tokens", 0)) if isinstance(usage, dict) else 0
        
        return reply_text, tokens_in, tokens_out