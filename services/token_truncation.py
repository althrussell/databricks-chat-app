from transformers import GPT2TokenizerFast

# Load GPT2 tokenizer (token count approximation)
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

# Max context limits per supported model
MODEL_TOKEN_LIMITS = {
    "claude": 180_000,
    "llama": 28_000,
    "gemma": 28_000,
    "gpt": 120_000,
    "default": 30_000
}

def truncate_to_model_context(text: str, model_key: str) -> str:
    limit = MODEL_TOKEN_LIMITS.get(model_key.lower(), MODEL_TOKEN_LIMITS["default"])
    tokens = tokenizer.encode(text)
    if len(tokens) > limit:
        return tokenizer.decode(tokens[:limit])
    return text
