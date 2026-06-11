from app.memory import ConversationMemory


def test_append_turn_and_get_context():
    m = ConversationMemory(window=10)
    m.append_turn("t1", "cau hoi 1", "tra loi 1")
    ctx = m.get_context("t1")
    assert ctx["turns"] == [{"user": "cau hoi 1", "answer": "tra loi 1"}]
    assert ctx["summary"] is None


def test_get_context_unknown_thread_is_empty():
    m = ConversationMemory(window=10)
    assert m.get_context("nope") == {"turns": [], "summary": None}


def test_get_context_does_not_leak_reference():
    m = ConversationMemory(window=10)
    m.append_turn("t1", "u", "a")
    ctx = m.get_context("t1")
    ctx["turns"].append({"user": "x", "answer": "y"})
    ctx["turns"][0]["user"] = "sua doi"
    assert m.get_context("t1")["turns"] == [{"user": "u", "answer": "a"}]


def test_threads_isolated():
    m = ConversationMemory(window=10)
    m.append_turn("t1", "u1", "a1")
    m.append_turn("t2", "u2", "a2")
    assert m.get_context("t1")["turns"][0]["user"] == "u1"
    assert m.get_context("t2")["turns"][0]["user"] == "u2"


def test_needs_compact_only_above_window():
    m = ConversationMemory(window=2)
    m.append_turn("t1", "u1", "a1")
    m.append_turn("t1", "u2", "a2")
    assert m.needs_compact("t1") is False
    m.append_turn("t1", "u3", "a3")
    assert m.needs_compact("t1") is True


def test_needs_compact_unknown_thread_false():
    m = ConversationMemory(window=2)
    assert m.needs_compact("nope") is False
