import pytest
from openai import OpenAI

from app.core.config import get_mkp_settings


@pytest.fixture(autouse=True)
def _clear_mkp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("FPT_MKP_API_KEY", "FPT_MKP_BASE_URL", "FPT_MKP_MODEL"):
        monkeypatch.delenv(name, raising=False)


def test_get_mkp_settings_full_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FPT_MKP_API_KEY", " test-key ")
    monkeypatch.setenv("FPT_MKP_BASE_URL", " https://example.com/ ")
    monkeypatch.setenv("FPT_MKP_MODEL", " my-model ")
    client, model = get_mkp_settings()
    assert isinstance(client, OpenAI)
    assert model == "my-model"


def test_get_mkp_settings_missing_api_key_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(RuntimeError, match="FPT_MKP_API_KEY"):
        get_mkp_settings()


def test_get_mkp_settings_default_base_url_and_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FPT_MKP_API_KEY", "sk-test")
    client, model = get_mkp_settings()
    assert client is not None
    assert model == "gemma-4-31B-it"
    assert str(client.base_url).rstrip("/") == "https://mkp-api.fptcloud.com"
