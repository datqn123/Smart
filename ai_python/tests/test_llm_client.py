from unittest.mock import MagicMock
from app.config.llm_client import OpenAILLMClient, make_llm
from app.config.settings import Settings


def _settings():
    return Settings(llm_base_url="https://x", llm_api_key="k",
                    llm_model="Qwen3.6-27B", database_url_ro="postgresql://u:p@h/db")


def test_make_llm_default_uses_qwen_and_tool_temp():
    s = _settings()
    client = make_llm(s, role="default")
    assert client.model == "Qwen3.6-27B"
    assert client.temperature == 0.2


def test_make_llm_sm_uses_qwen_with_sm_temp():
    # R5: SM dung CHINH Qwen nhung config rieng (temperature 0.0)
    s = _settings()
    client = make_llm(s, role="sm")
    assert client.model == "Qwen3.6-27B"
    assert client.temperature == 0.0


def test_complete_calls_chat_completions_with_messages():
    s = _settings()
    fake_sdk = MagicMock()
    fake_sdk.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="hi"))])
    client = OpenAILLMClient(sdk=fake_sdk, model="Qwen3.6-27B", temperature=0.2)
    out = client.complete(system="S", user="U")
    assert out == "hi"
    kwargs = fake_sdk.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "Qwen3.6-27B"
    assert kwargs["messages"][0] == {"role": "system", "content": "S"}
    assert kwargs["messages"][1] == {"role": "user", "content": "U"}
    assert kwargs["temperature"] == 0.2
