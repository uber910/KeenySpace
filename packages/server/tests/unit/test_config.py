from __future__ import annotations

import pytest
from pydantic import ValidationError


def test_get_settings_from_env(monkeypatch):
    monkeypatch.setenv("KEENYSPACE_DB__URL", "postgresql+asyncpg://u:p@h/d")
    monkeypatch.setenv("KEENYSPACE_FS__ROOT", "/tmp/k")

    import keenyspace_server.config as cfg
    cfg.get_settings.cache_clear()

    try:
        s = cfg.get_settings()
        assert str(s.db.url) == "postgresql+asyncpg://u:p@h/d"
        assert str(s.fs.root) == "/tmp/k"
        assert s.wal.max_entry_bytes == 256 * 1024
        assert s.auth.multi_worker is False
    finally:
        cfg.get_settings.cache_clear()


def test_missing_db_url_raises(monkeypatch):
    monkeypatch.delenv("KEENYSPACE_DB__URL", raising=False)

    import keenyspace_server.config as cfg
    cfg.get_settings.cache_clear()

    try:
        with pytest.raises((ValidationError, Exception)):
            cfg.get_settings()
    finally:
        cfg.get_settings.cache_clear()
