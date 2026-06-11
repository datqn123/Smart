import asyncio

from app.memory import ConversationMemory


class _CompactLLM:
    def __init__(self, reply="Tom tat moi.", fail=False):
        self.reply, self.fail, self.calls = reply, fail, []

    def complete(self, *, system, user, role="default", temperature=None):
        self.calls.append({"system": system, "user": user, "role": role})
        if self.fail:
            raise RuntimeError("LLM down")
        return self.reply


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


def test_compact_merges_overflow_and_keeps_window():
    m = ConversationMemory(window=2)
    for i in range(4):
        m.append_turn("t1", f"cauhoi{i}", f"traloi{i}")
    llm = _CompactLLM(reply="  Tom tat moi.  ")
    asyncio.run(m.compact("t1", llm=llm))
    ctx = m.get_context("t1")
    assert ctx["summary"] == "Tom tat moi."          # strip
    assert ctx["turns"] == [{"user": "cauhoi2", "answer": "traloi2"},
                            {"user": "cauhoi3", "answer": "traloi3"}]
    call = llm.calls[0]
    assert call["role"] == "default"
    assert "(chua co)" in call["user"]                # summary cu rong
    assert "cauhoi0" in call["user"] and "cauhoi1" in call["user"]  # overflow vao prompt
    assert "cauhoi3" not in call["user"]              # luot trong window KHONG gop


def test_compact_second_round_merges_old_summary():
    m = ConversationMemory(window=1)
    m.append_turn("t1", "u0", "a0")
    m.append_turn("t1", "u1", "a1")
    asyncio.run(m.compact("t1", llm=_CompactLLM(reply="S1")))
    m.append_turn("t1", "u2", "a2")
    llm = _CompactLLM(reply="S2")
    asyncio.run(m.compact("t1", llm=llm))
    assert "S1" in llm.calls[0]["user"]               # summary cu di vao prompt merge
    assert m.get_context("t1")["summary"] == "S2"


def test_compact_llm_error_degrades_keeps_summary_still_drops():
    m = ConversationMemory(window=1)
    m.append_turn("t1", "u0", "a0")
    m.append_turn("t1", "u1", "a1")
    asyncio.run(m.compact("t1", llm=_CompactLLM(reply="S1")))
    m.append_turn("t1", "u2", "a2")
    asyncio.run(m.compact("t1", llm=_CompactLLM(fail=True)))  # khong duoc raise
    ctx = m.get_context("t1")
    assert ctx["summary"] == "S1"                                # giu summary cu
    assert ctx["turns"] == [{"user": "u2", "answer": "a2"}]      # van drop luot tran


def test_compact_truncates_to_summary_max_chars():
    m = ConversationMemory(window=1, summary_max_chars=10)
    m.append_turn("t1", "u0", "a0")
    m.append_turn("t1", "u1", "a1")
    asyncio.run(m.compact("t1", llm=_CompactLLM(reply="x" * 50)))
    assert len(m.get_context("t1")["summary"]) == 10


def test_compact_noop_within_window():
    m = ConversationMemory(window=10)
    m.append_turn("t1", "u", "a")
    llm = _CompactLLM()
    asyncio.run(m.compact("t1", llm=llm))
    assert llm.calls == []
