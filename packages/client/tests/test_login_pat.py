"""Tests for the personal-access-token login type (`keenyspace login --pat`)."""

from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path
from typing import Any

import pytest
from pytest_httpserver import HTTPServer


def _reload() -> Any:
    import keenyspace.paths as paths_mod

    importlib.reload(paths_mod)
    import keenyspace.config as cfg

    importlib.reload(cfg)
    cfg.get_client_settings.cache_clear()  # type: ignore[attr-defined]
    import keenyspace.auth as auth_mod

    importlib.reload(auth_mod)
    import keenyspace.cli.login as login_mod

    return importlib.reload(login_mod)


def _ipv4(url: str) -> str:
    return url.replace("localhost", "127.0.0.1")


def test_login_pat_validates_and_persists_api_key(
    httpserver: HTTPServer, temp_config_dir: dict[str, Path]
) -> None:
    login = _reload()
    url = _ipv4(httpserver.url_for("")).rstrip("/")
    httpserver.expect_request("/v1/api/auth/api-keys", method="GET").respond_with_json([])

    asyncio.run(login.run_login_pat(token="ks_live_abc123", server_url=url))

    import keenyspace.paths as paths_mod

    data = json.loads(Path(paths_mod.AUTH_JSON).read_text())
    assert data["api_key"] == "ks_live_abc123"
    # Durable credential — no OIDC access/refresh token persisted.
    assert "access_token" not in data
    assert "refresh_token" not in data


def test_login_pat_rejects_invalid_token(
    httpserver: HTTPServer, temp_config_dir: dict[str, Path]
) -> None:
    login = _reload()
    url = _ipv4(httpserver.url_for("")).rstrip("/")
    httpserver.expect_request("/v1/api/auth/api-keys", method="GET").respond_with_data(
        "", status=401
    )

    with pytest.raises(SystemExit):
        asyncio.run(login.run_login_pat(token="ks_live_bad", server_url=url))

    import keenyspace.paths as paths_mod

    assert not Path(paths_mod.AUTH_JSON).exists()
