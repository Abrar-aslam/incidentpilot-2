import os
from dotenv import load_dotenv

load_dotenv()

def get_settings():
    api_key = os.getenv("QWEN_API_KEY", "").strip()
    base_url = os.getenv("QWEN_BASE_URL", "").strip()
    model = os.getenv("QWEN_MODEL", "").strip()
    if not all((api_key, base_url, model)):
        raise RuntimeError(
            "Missing QWEN_API_KEY, QWEN_BASE_URL or QWEN_MODEL. "
            "Copy .env.example to .env and fill in your provider details."
        )
    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "max_agent_steps": int(os.getenv("MAX_AGENT_STEPS", "6")),
    }
