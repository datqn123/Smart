"""Thinking log — dong log tu su kien ke lai 'agent dang suy nghi gi'.

Logger rieng ten 'think' de grep/loc duoc trong console:
    10:21:33 INFO    think [SM] suy nghi: can truy van DB de tra loi...

Quy uoc prefix moi dong:
    [<component>] <dien bien>     — dang lam gi / thay gi
    [<component>] -> <ket luan>   — quyet dinh / ket qua cua buoc do
"""
from __future__ import annotations
import logging

_log = logging.getLogger("think")


def think(component: str, msg: str, *args) -> None:
    """Ghi 1 dong suy nghi. msg la format-string %s nhu logging chuan."""
    _log.info("[%s] " + msg, component, *args)
