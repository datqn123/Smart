# ai_python/tests/conftest.py
import json
import pytest

pytest_plugins = ()


class FakeLLM:
    """Deterministic LLM thay openai SDK.

    - `scripted`: list[str] tra lan luot theo thu tu goi complete().
    - `by_role`: dict[str, list[str]] tra theo role neu complete(role=...) duoc truyen.
    - Ghi `self.calls` = list[{"role","system","user"}] de assert skill duoc nap.
    """

    def __init__(self, scripted=None, by_role=None, structured=None,
                 tool_selects=None):
        self.scripted = list(scripted or [])
        self.by_role = {k: list(v) for k, v in (by_role or {}).items()}
        self.structured = list(structured or [])      # dict | Exception
        self.tool_selects = list(tool_selects or [])  # (name, args_dict) | Exception
        self.calls = []
        self.structured_calls = []
        self.tool_select_calls = []

    def complete(self, *, system: str, user: str, role: str = "default",
                 temperature: float | None = None) -> str:
        self.calls.append({"role": role, "system": system, "user": user})
        if role in self.by_role and self.by_role[role]:
            return self.by_role[role].pop(0)
        if self.scripted:
            return self.scripted.pop(0)
        raise AssertionError(f"FakeLLM het kich ban cho role={role!r}")

    def json(self, payload) -> str:
        return json.dumps(payload, ensure_ascii=False)

    def complete_structured(self, *, system, user, output_model,
                            role="default", temperature=None):
        self.structured_calls.append({"role": role, "system": system,
                                      "user": user,
                                      "model": output_model.__name__})
        if not self.structured:
            raise AssertionError(
                f"FakeLLM het kich ban structured cho {output_model.__name__}")
        item = self.structured.pop(0)
        if isinstance(item, Exception):
            raise item
        return output_model.model_validate(item)

    def complete_tool_select(self, *, system, user, tools,
                             role="default", temperature=None):
        self.tool_select_calls.append({
            "role": role, "system": system, "user": user,
            "tools": [t["function"]["name"] for t in tools]})
        if not self.tool_selects:
            raise AssertionError("FakeLLM het kich ban tool_selects")
        item = self.tool_selects.pop(0)
        if isinstance(item, Exception):
            raise item
        name, args = item
        return name, json.dumps(args, ensure_ascii=False)


class StubSqlExecutor:
    """Thay PostgresRoExecutor. Tra rows co dinh; chan non-SELECT de
    chung minh guard phai chay TRUOC executor (fact-sql-guard)."""

    def __init__(self, rows=None):
        self.rows = rows if rows is not None else [{"id": 1, "name": "Acme"}]
        self.executed = []

    def run(self, sql: str, *, row_limit: int = 100):
        stripped = sql.strip().lower()
        if not stripped.startswith("select"):
            raise AssertionError("StubSqlExecutor nhan non-SELECT — guard da khong chan")
        self.executed.append(sql)
        return {"columns": list(self.rows[0].keys()) if self.rows else [],
                "rows": self.rows[:row_limit]}


@pytest.fixture
def fake_llm():
    return FakeLLM()


@pytest.fixture
def stub_sql():
    return StubSqlExecutor()
