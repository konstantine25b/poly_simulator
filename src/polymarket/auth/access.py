from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Access:
    user_id: int
    is_admin: bool
