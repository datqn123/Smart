from openai import OpenAI

from app.core.config import get_mkp_settings


def get_mkp_client() -> tuple[OpenAI, str]:
    return get_mkp_settings()
