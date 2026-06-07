from __future__ import annotations


def test_router_intent_uses_haiku() -> None:
    from app.harness.model_router import ModelRouter

    assert ModelRouter().pick("intent") == "haiku"


def test_router_planner_uses_sonnet() -> None:
    from app.harness.model_router import ModelRouter

    assert ModelRouter().pick("planner") == "sonnet"


def test_router_escalates_to_opus_on_replan() -> None:
    from app.harness.model_router import ModelRouter

    assert ModelRouter(opt_escalate_replan_count=2).pick("sql", replan_count=2) == "opus"
