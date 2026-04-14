from __future__ import annotations

import pytest

from polymarket import db


@pytest.fixture(autouse=True)
def force_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db.settings, "db_backend", "sqlite")
