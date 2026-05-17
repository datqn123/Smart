from __future__ import annotations

import pytest

from app.graph.datetime_display import (
    localize_query_result_for_display,
    localize_value_tree,
)
from zoneinfo import ZoneInfo


def _zoneinfo_hcm_available() -> bool:
    try:
        ZoneInfo("Asia/Ho_Chi_Minh")
    except Exception:
        return False
    return True


requires_hcm_tz = pytest.mark.skipif(
    not _zoneinfo_hcm_available(),
    reason="IANA zone Asia/Ho_Chi_Minh unavailable (common on Windows without full tzdata)",
)


@requires_hcm_tz
def test_localize_z_to_hcm() -> None:
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    payload = {"rows": [{"created_at": "2026-05-11T14:55:30Z"}], "meta": {}}
    out = localize_value_tree(payload, tz)
    assert out["rows"][0]["created_at"] == "11/05/2026 21:55:30"


@requires_hcm_tz
def test_localize_offset_aware() -> None:
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    payload = {"rows": [{"created_at": "2026-05-11T14:55:30+00:00"}]}
    out = localize_value_tree(payload, tz)
    assert out["rows"][0]["created_at"] == "11/05/2026 21:55:30"


@requires_hcm_tz
def test_naive_string_unchanged() -> None:
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    payload = {"rows": [{"created_at": "2026-05-11 21:55:30"}]}
    out = localize_value_tree(payload, tz)
    assert out["rows"][0]["created_at"] == "2026-05-11 21:55:30"


def test_localize_query_result_none_tz_returns_same_structure() -> None:
    payload = {"rows": [{"created_at": "2026-05-11T14:55:30Z"}]}
    out = localize_query_result_for_display(payload, None)
    assert out is payload


def test_localize_query_result_empty_tz() -> None:
    payload = {"rows": [{"created_at": "2026-05-11T14:55:30Z"}]}
    out = localize_query_result_for_display(payload, "  ")
    assert out["rows"][0]["created_at"] == "2026-05-11T14:55:30Z"
