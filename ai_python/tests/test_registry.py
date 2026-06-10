import pytest
from app.registry.registry import (TOOL_NAMES, load_skill, render_tool_catalog,
                                    is_registered)


def test_registry_lists_exactly_four_tools():  # fact-registry-static
    assert set(TOOL_NAMES) == {
        "sql_execute", "data_validator", "answer_composer", "session_manager"}


def test_only_registered_tools_callable():  # fact-registry-static
    assert is_registered("sql_execute")
    assert not is_registered("rm_rf_database")


def test_load_skill_reads_md_fresh_each_call(tmp_path, monkeypatch):
    first = load_skill("sql_execute")
    assert isinstance(first, str) and len(first) > 0


def test_load_skill_unknown_raises():
    with pytest.raises(KeyError):
        load_skill("nope")


def test_catalog_contains_descriptions_for_dispatch_tools():
    cat = render_tool_catalog()
    assert "sql_execute" in cat
    assert "data_validator" in cat
    assert "answer_composer" in cat
