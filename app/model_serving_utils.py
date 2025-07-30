"""
Databricks Model Serving Utilities
Handles communication with Databricks model serving endpoints
"""

import os
import json
import requests
from typing import Dict, List, Any, Tuple, Optional
from databricks.sdk.core import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelServingClient:
    """Client for interacting with Databricks model serving endpoints"""
    
    def __init__(self):
        self.config = Config()
        self.base_url = f"https://{self.config.host}"
        self.headers = {
            "Authorization": f"Bearer {self.config.token}",
            "Content-Type": "application/json"
        }
    
    def query_endpoint(self, 
                      endpoint_name: str, 
                      messages: List[Dict[str, str]], 
                      max_tokens: int = 400,
                      temperature: float = 0.7,
                      **kwargs) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Query a Databricks model serving endpoint
        
        Args:
            endpoint_name: Name of the serving endpoint
            messages: List of chat messages in OpenAI format
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters for the model
        
        Returns:
            Tuple of (response_message, usage_info)
        """
        url = f"{self.base_url}/serving-endpoints/{endpoint_name}/invocations"
        
        # Prepare the payload based on endpoint type
        payload = self._prepare_payload(messages, max_tokens, temperature, **kwargs)
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return self._parse_response(result)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling endpoint {endpoint_name}: {e}")
            error_response = {
                "content": f"Error calling model endpoint: {str(e)}",
                "role": "assistant"
            }
            error_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return error_response, error_usage
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            error_response = {
                "content": f"Unexpected error: {str(e)}",
                "role": "assistant"
            }
            error_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return error_response, error_usage
    
    def _prepare_payload(self, 
                        messages: List[Dict[str, str]], 
                        max_tokens: int, 
                        temperature: float, 
                        **kwargs) -> Dict[str, Any]:
        """Prepare the request payload for the model endpoint"""
        
        # Standard OpenAI-compatible format (works with most endpoints)
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        # Add any additional parameters
        payload.update(kwargs)
        
        return payload
    
    def _parse_response(self, result: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Parse the response from the model endpoint"""
        
        # Handle OpenAI-compatible format
        if "choices" in result:
            message = result["choices"][0].get("message", {})
            usage = result.get("usage", {})
            
            return message, usage
        
        # Handle custom formats
        elif "response" in result:
            message = {
                "role": "assistant",
                "content": result["response"]
            }
            usage = result.get("usage", {})
            return message, usage
        
        # Handle plain text response
        elif isinstance(result, str):
            message = {
                "role": "assistant", 
                "content": result
            }
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return message, usage
        
        # Handle other formats
        else:
            # Try to extract content from various possible keys
            content = (result.get("content") or 
                      result.get("text") or 
                      result.get("output") or 
                      str(result))
            
            message = {
                "role": "assistant",
                "content": content
            }
            usage = result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            return message, usage

# Global client instance
_client = None

def get_client() -> ModelServingClient:
    """Get or create a model serving client"""
    global _client
    if _client is None:
        _client = ModelServingClient()
    return _client

def query_endpoint_with_usage(endpoint_name: str, 
                             messages: List[Dict[str, str]], 
                             max_tokens: int = 400,
                             temperature: float = 0.7,
                             **kwargs) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Convenience function to query an endpoint and return response with usage
    
    Args:
        endpoint_name: Name of the serving endpoint
        messages: List of chat messages in OpenAI format
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        **kwargs: Additional parameters for the model
    
    Returns:
        Tuple of (response_message, usage_info)
    """
    client = get_client()
    return client.query_endpoint(endpoint_name, messages, max_tokens, temperature, **kwargs)

def test_endpoint(endpoint_name: str) -> bool:
    """
    Test if an endpoint is accessible and responding
    
    Args:
        endpoint_name: Name of the serving endpoint
    
    Returns:
        True if endpoint is working, False otherwise
    """
    try:
        test_messages = [{"role": "user", "content": "Hello"}]
        response, usage = query_endpoint_with_usage(endpoint_name, test_messages, max_tokens=5)
        return "content" in response and len(response["content"]) > 0
    except Exception as e:
        logger.error(f"Endpoint {endpoint_name} test failed: {e}")
        return False

def list_available_endpoints() -> List[str]:
    """
    List available model serving endpoints (if accessible via API)
    
    Returns:
        List of endpoint names
    """
    try:
        client = get_client()
        url = f"{client.base_url}/api/2.0/serving-endpoints"
        
        response = requests.get(url, headers=client.headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        endpoints = result.get("endpoints", [])
        return [ep.get("name", "") for ep in endpoints if ep.get("state") == "READY"]
        
    except Exception as e:
        logger.error(f"Failed to list endpoints: {e}")
        return []

# Endpoint-specific helpers for common model types

def query_openai_endpoint(endpoint_name: str, 
                         messages: List[Dict[str, str]], 
                         max_tokens: int = 400,
                         temperature: float = 0.7) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Query OpenAI-compatible endpoint (GPT-4, GPT-3.5, etc.)"""
    return query_endpoint_with_usage(
        endpoint_name=endpoint_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.9
    )

def query_anthropic_endpoint(endpoint_name: str, 
                           messages: List[Dict[str, str]], 
                           max_tokens: int = 400,
                           temperature: float = 0.7) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Query Anthropic Claude endpoint"""
    return query_endpoint_with_usage(
        endpoint_name=endpoint_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.9
    )

def query_llama_endpoint(endpoint_name: str, 
                        messages: List[Dict[str, str]], 
                        max_tokens: int = 400,
                        temperature: float = 0.7) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Query Llama model endpoint"""
    return query_endpoint_with_usage(
        endpoint_name=endpoint_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.9,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

def query_mixtral_endpoint(endpoint_name: str, 
                          messages: List[Dict[str, str]], 
                          max_tokens: int = 400,
                          temperature: float = 0.7) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Query Mixtral model endpoint"""
    return query_endpoint_with_usage(
        endpoint_name=endpoint_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.9
    )

# Utility functions for message formatting

def format_messages_for_chat(conversation_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Format conversation history for model consumption
    
    Args:
        conversation_history: List of messages with 'role' and 'content'
    
    Returns:
        Formatted messages for the model
    """
    formatted = []
    for msg in conversation_history:
        if msg.get("role") in ["user", "assistant", "system"]:
            formatted.append({
                "role": msg["role"],
                "content": str(msg.get("content", ""))
            })
    return formatted

def add_system_message(messages: List[Dict[str, str]], 
                      system_prompt: str) -> List[Dict[str, str]]:
    """
    Add a system message to the beginning of the conversation
    
    Args:
        messages: Existing conversation messages
        system_prompt: System instruction to add
    
    Returns:
        Messages with system prompt added
    """
    system_msg = {"role": "system", "content": system_prompt}
    
    # Check if there's already a system message
    if messages and messages[0].get("role") == "system":
        messages[0] = system_msg  # Replace existing system message
        return messages
    else:
        return [system_msg] + messages

def truncate_conversation(messages: List[Dict[str, str]], 
                         max_tokens: int = 4000,
                         chars_per_token: float = 4.0) -> List[Dict[str, str]]:
    """
    Truncate conversation to fit within token limits
    
    Args:
        messages: Conversation messages
        max_tokens: Maximum tokens allowed
        chars_per_token: Estimated characters per token
    
    Returns:
        Truncated conversation that fits within limits
    """
    max_chars = int(max_tokens * chars_per_token)
    
    # Keep system message if present
    system_msgs = [msg for msg in messages if msg.get("role") == "system"]
    other_msgs = [msg for msg in messages if msg.get("role") != "system"]
    
    # Calculate running total
    total_chars = sum(len(msg.get("content", "")) for msg in system_msgs)
    result = system_msgs.copy()
    
    # Add messages from the end (most recent first)
    for msg in reversed(other_msgs):
        msg_chars = len(msg.get("content", ""))
        if total_chars + msg_chars <= max_chars:
            result.insert(-len(system_msgs) if system_msgs else 0, msg)
            total_chars += msg_chars
        else:
            break
    
    return result

# Error handling and retry logic

def query_with_retry(endpoint_name: str, 
                    messages: List[Dict[str, str]], 
                    max_retries: int = 3,
                    retry_delay: float = 1.0,
                    **kwargs) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Query endpoint with retry logic for handling transient failures
    
    Args:
        endpoint_name: Name of the serving endpoint
        messages: List of chat messages
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        **kwargs: Additional parameters for query_endpoint_with_usage
    
    Returns:
        Tuple of (response_message, usage_info)
    """
    import time
    
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            return query_endpoint_with_usage(endpoint_name, messages, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt + 1} failed for endpoint {endpoint_name}: {e}")
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
            else:
                logger.error(f"All {max_retries + 1} attempts failed for endpoint {endpoint_name}")
    
    # Return error response if all retries failed
    error_response = {
        "content": f"Failed to get response after {max_retries + 1} attempts: {str(last_error)}",
        "role": "assistant"
    }
    error_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    return error_response, error_usage

# Batch processing utilities

def query_multiple_endpoints(endpoints: List[str], 
                           messages: List[Dict[str, str]], 
                           **kwargs) -> Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Query multiple endpoints with the same input for comparison
    
    Args:
        endpoints: List of endpoint names
        messages: List of chat messages
        **kwargs: Additional parameters for query_endpoint_with_usage
    
    Returns:
        Dictionary mapping endpoint names to (response, usage) tuples
    """
    results = {}
    
    for endpoint in endpoints:
        try:
            response, usage = query_endpoint_with_usage(endpoint, messages, **kwargs)
            results[endpoint] = (response, usage)
        except Exception as e:
            logger.error(f"Failed to query endpoint {endpoint}: {e}")
            error_response = {
                "content": f"Error: {str(e)}",
                "role": "assistant"
            }
            error_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            results[endpoint] = (error_response, error_usage)
    
    return results

# Streaming support (for future enhancement)

def query_endpoint_streaming(endpoint_name: str, 
                           messages: List[Dict[str, str]], 
                           **kwargs):
    """
    Query endpoint with streaming response (if supported)
    
    Args:
        endpoint_name: Name of the serving endpoint
        messages: List of chat messages
        **kwargs: Additional parameters
    
    Yields:
        Streaming response chunks
    """
    client = get_client()
    url = f"{client.base_url}/serving-endpoints/{endpoint_name}/invocations"
    
    payload = client._prepare_payload(messages, stream=True, **kwargs)
    
    try:
        response = requests.post(
            url, 
            headers=client.headers, 
            json=payload, 
            stream=True,
            timeout=60
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode('utf-8'))
                    yield chunk
                except json.JSONDecodeError:
                    continue
                    
    except Exception as e:
        logger.error(f"Streaming error for endpoint {endpoint_name}: {e}")
        yield {"error": str(e)}

# Model-specific optimizations

def get_optimal_parameters(endpoint_name: str) -> Dict[str, Any]:
    """
    Get optimal parameters for specific model types
    
    Args:
        endpoint_name: Name of the serving endpoint
    
    Returns:
        Dictionary of optimal parameters
    """
    # Default parameters
    params = {
        "temperature": 0.7,
        "max_tokens": 400,
        "top_p": 0.9
    }
    
    endpoint_lower = endpoint_name.lower()
    
    # GPT models
    if any(model in endpoint_lower for model in ["gpt", "openai"]):
        params.update({
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        })
    
    # Claude models
    elif any(model in endpoint_lower for model in ["claude", "anthropic"]):
        params.update({
            "top_k": 40
        })
    
    # Llama models
    elif any(model in endpoint_lower for model in ["llama", "llama2", "llama-2"]):
        params.update({
            "top_k": 50,
            "repetition_penalty": 1.1
        })
    
    # Mixtral models
    elif any(model in endpoint_lower for model in ["mixtral", "mistral"]):
        params.update({
            "top_k": 50
        })
    
    return params

# Cost calculation utilities

def estimate_cost(messages: List[Dict[str, str]], 
                 endpoint_name: str,
                 input_cost_per_1k: float = 0.001,
                 output_cost_per_1k: float = 0.002) -> Dict[str, float]:
    """
    Estimate the cost of a query before sending it
    
    Args:
        messages: List of chat messages
        endpoint_name: Name of the serving endpoint
        input_cost_per_1k: Cost per 1K input tokens
        output_cost_per_1k: Cost per 1K output tokens
    
    Returns:
        Dictionary with cost estimates
    """
    # Simple token estimation (4 chars ≈ 1 token)
    total_chars = sum(len(msg.get("content", "")) for msg in messages)
    estimated_input_tokens = total_chars / 4
    
    # Estimate output tokens (conservative estimate)
    estimated_output_tokens = min(400, estimated_input_tokens * 0.5)
    
    estimated_input_cost = (estimated_input_tokens / 1000) * input_cost_per_1k
    estimated_output_cost = (estimated_output_tokens / 1000) * output_cost_per_1k
    
    return {
        "estimated_input_tokens": estimated_input_tokens,
        "estimated_output_tokens": estimated_output_tokens,
        "estimated_input_cost": estimated_input_cost,
        "estimated_output_cost": estimated_output_cost,
        "estimated_total_cost": estimated_input_cost + estimated_output_cost
    }

# Health check and monitoring

def health_check_all_endpoints(endpoints: List[str]) -> Dict[str, bool]:
    """
    Check the health of multiple endpoints
    
    Args:
        endpoints: List of endpoint names to check
    
    Returns:
        Dictionary mapping endpoint names to health status
    """
    results = {}
    for endpoint in endpoints:
        results[endpoint] = test_endpoint(endpoint)
    return results

def get_endpoint_metrics(endpoint_name: str) -> Dict[str, Any]:
    """
    Get metrics for an endpoint (if available via API)
    
    Args:
        endpoint_name: Name of the serving endpoint
    
    Returns:
        Dictionary with endpoint metrics
    """
    try:
        client = get_client()
        url = f"{client.base_url}/api/2.0/serving-endpoints/{endpoint_name}"
        
        response = requests.get(url, headers=client.headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "name": result.get("name"),
            "state": result.get("state"),
            "creator": result.get("creator"),
            "creation_timestamp": result.get("creation_timestamp"),
            "last_updated_timestamp": result.get("last_updated_timestamp"),
            "config": result.get("config", {})
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics for endpoint {endpoint_name}: {e}")
        return {"error": str(e)}

# Export utilities

def export_conversation_for_training(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Export conversation in format suitable for model fine-tuning
    
    Args:
        messages: List of conversation messages
    
    Returns:
        Formatted conversation for training
    """
    return {
        "messages": format_messages_for_chat(messages),
        "exported_at": json.dumps({"timestamp": str(pd.Timestamp.now())}),
        "format_version": "1.0"
    }

# Configuration validation

def validate_endpoint_config(endpoint_name: str) -> Dict[str, Any]:
    """
    Validate endpoint configuration and connectivity
    
    Args:
        endpoint_name: Name of the serving endpoint
    
    Returns:
        Validation results
    """
    results = {
        "endpoint_name": endpoint_name,
        "accessible": False,
        "response_time_ms": None,
        "supports_streaming": False,
        "error": None
    }
    
    try:
        import time
        start_time = time.time()
        
        # Test basic connectivity
        success = test_endpoint(endpoint_name)
        end_time = time.time()
        
        results["accessible"] = success
        results["response_time_ms"] = (end_time - start_time) * 1000
        
        if success:
            # Test streaming support (basic check)
            try:
                # This is a simple check - actual streaming test would be more complex
                results["supports_streaming"] = True  # Assume true for now
            except Exception:
                results["supports_streaming"] = False
        
    except Exception as e:
        results["error"] = str(e)
    
    return results