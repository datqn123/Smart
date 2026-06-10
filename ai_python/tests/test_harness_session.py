from app.harness.session import resolve_thread_id
from app.harness.turn_context import TurnContext


def test_thread_id_deterministic_per_user():  # fact-thread
    a = resolve_thread_id("user-1")
    b = resolve_thread_id("user-1")
    c = resolve_thread_id("user-2")
    assert a == b
    assert a != c
    assert a.startswith("thread-")


def test_turn_context_holds_resolved_thread():
    ctx = TurnContext(raw_require="doanh thu quy 1?", user_id="user-1",
                      thread_id="thread-x")
    assert ctx.raw_require == "doanh thu quy 1?"
    assert ctx.thread_id == "thread-x"
    assert ctx.clarification_response is None
