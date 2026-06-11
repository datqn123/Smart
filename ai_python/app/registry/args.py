from __future__ import annotations
from pydantic import BaseModel


class CommonArgs(BaseModel):
    reasoning: str                          # vi sao chon buoc nay
    resolved_require: str | None = None     # cau hoi noi tiep da viet lai tu-du-nghia


class SqlExecuteArgs(CommonArgs):
    """Sinh SQL read-only tu yeu cau va chay tren DB de lay du lieu."""
    require: str                            # yeu cau du lieu da lam ro/viet lai


class ValidatorArgs(CommonArgs):
    """Kiem tra data vua lay co du/dung de tra loi yeu cau khong."""


class ComposerArgs(CommonArgs):
    """Soan cau tra loi cuoi cho user tu data da duoc kiem dinh."""


class FinishArgs(CommonArgs):
    """Ket thuc phien voi message cuoi cho user."""
    message: str


class ClarifyArgs(CommonArgs):
    """Hoi lai user khi yeu cau mo ho/thieu thong tin."""
    message: str
