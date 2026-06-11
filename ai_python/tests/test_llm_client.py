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


def _fake_sdk(content="hi"):
    sdk = MagicMock()
    sdk.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=content))])
    return sdk


def test_complete_disables_qwen_thinking_and_bounds_tokens():
    sdk = _fake_sdk()
    client = OpenAILLMClient(sdk=sdk, model="m", temperature=0.2,
                             max_tokens=1500, disable_thinking=True)
    client.complete(system="S", user="U")
    kwargs = sdk.chat.completions.create.call_args.kwargs
    assert kwargs["max_tokens"] == 1500
    assert kwargs["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}


def test_complete_strips_think_block():
    sdk = _fake_sdk("<think>dai dong suy nghi</think>\n{\"ok\": true}")
    client = OpenAILLMClient(sdk=sdk, model="m", temperature=0.2)
    assert client.complete(system="S", user="U") == '{"ok": true}'


def test_make_llm_wires_max_tokens_and_thinking_from_settings():
    client = make_llm(_settings(), role="default")
    assert client.max_tokens == 1500
    assert client.disable_thinking is True


# ===== Native tool-calling (Task 1, plan 2026-06-11-native-tool-calling) =====
import json
import pytest
from typing import Literal
from pydantic import BaseModel
from app.config.llm_client import StructuredOutputError, ToolCallError


class _Verdict(BaseModel):
    """Ket luan kiem dinh."""
    verdict: Literal["pass", "fail"]
    reason: str


def _sdk_returning(tool_calls_list):
    """Moi phan tu = list tool_calls (hoac None) cho 1 lan create()."""
    sdk = MagicMock()
    resps = []
    for tcs in tool_calls_list:
        msg = MagicMock()
        msg.tool_calls = tcs
        msg.content = ""
        resps.append(MagicMock(choices=[MagicMock(message=msg)]))
    sdk.chat.completions.create.side_effect = resps
    return sdk


def _tc(name, args: dict):
    tc = MagicMock()
    tc.function.name = name
    tc.function.arguments = json.dumps(args, ensure_ascii=False)
    return tc


def test_complete_structured_parses_valid_args():
    sdk = _sdk_returning([[_tc("respond", {"verdict": "pass", "reason": "ok"})]])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0)
    out = c.complete_structured(system="S", user="U", output_model=_Verdict)
    assert out.verdict == "pass" and out.reason == "ok"
    kwargs = sdk.chat.completions.create.call_args.kwargs
    assert kwargs["tool_choice"] == {"type": "function",
                                     "function": {"name": "respond"}}
    assert kwargs["tools"][0]["function"]["name"] == "respond"
    assert kwargs["tools"][0]["function"]["parameters"]["properties"]["verdict"]


def test_complete_structured_retries_once_then_succeeds():
    sdk = _sdk_returning([[_tc("respond", {"verdict": "maybe", "reason": "x"})],
                          [_tc("respond", {"verdict": "fail", "reason": "thieu"})]])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0)
    out = c.complete_structured(system="S", user="U", output_model=_Verdict)
    assert out.verdict == "fail"
    assert sdk.chat.completions.create.call_count == 2
    u2 = sdk.chat.completions.create.call_args.kwargs["messages"][1]["content"]
    assert "[Loi attempt truoc" in u2


def test_complete_structured_raises_after_two_failures():
    sdk = _sdk_returning([[_tc("respond", {"verdict": "maybe", "reason": "x"})],
                          [_tc("respond", {"verdict": "no", "reason": "y"})]])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0)
    with pytest.raises(StructuredOutputError):
        c.complete_structured(system="S", user="U", output_model=_Verdict)


def test_complete_structured_no_toolcall_counts_as_failure():
    sdk = _sdk_returning([None, [_tc("respond", {"verdict": "pass", "reason": "r"})]])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0)
    out = c.complete_structured(system="S", user="U", output_model=_Verdict)
    assert out.verdict == "pass"
    assert sdk.chat.completions.create.call_count == 2


def test_complete_tool_select_returns_name_and_args():
    sdk = _sdk_returning([[_tc("sql_execute", {"reasoning": "r", "require": "q"})]])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0)
    tools = [{"type": "function", "function": {"name": "sql_execute",
              "description": "d", "parameters": {"type": "object"}}}]
    name, args = c.complete_tool_select(system="S", user="U", tools=tools)
    assert name == "sql_execute"
    assert json.loads(args)["require"] == "q"
    kwargs = sdk.chat.completions.create.call_args.kwargs
    assert kwargs["tool_choice"] == "required"
    assert kwargs["tools"] is tools


def test_complete_tool_select_raises_when_no_toolcall():
    sdk = _sdk_returning([None])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0)
    with pytest.raises(ToolCallError):
        c.complete_tool_select(system="S", user="U", tools=[])


def test_tool_calls_carry_disable_thinking_extra_body():
    sdk = _sdk_returning([[_tc("respond", {"verdict": "pass", "reason": "r"})]])
    c = OpenAILLMClient(sdk=sdk, model="m", temperature=0.0, disable_thinking=True)
    c.complete_structured(system="S", user="U", output_model=_Verdict)
    kwargs = sdk.chat.completions.create.call_args.kwargs
    assert kwargs["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}
