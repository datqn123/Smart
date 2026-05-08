import os

from openai import OpenAI

from app.core.errors import MkpConfigError


def _required_env(name: str) -> str:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        raise MkpConfigError(f"Missing required environment variable: {name}")
    return raw


def get_mkp_settings() -> tuple[OpenAI, str]:
    api_key = _required_env("FPT_MKP_API_KEY").strip()
    base_url = os.getenv("FPT_MKP_BASE_URL", "https://mkp-api.fptcloud.com").rstrip("/")
    model = os.getenv("FPT_MKP_MODEL", "gemma-4-31B-it").strip()
    return OpenAI(api_key=api_key, base_url=base_url), model
