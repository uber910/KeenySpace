"""Client `keenyspace backup` streamer tests."""

from __future__ import annotations

import importlib
import os
from pathlib import Path

from pytest_httpserver import HTTPServer
from typer.testing import CliRunner


def _reload_and_get_app(server_url: str) -> object:
    os.environ["KEENYSPACE_SERVER_URL"] = server_url
    os.environ["COLUMNS"] = "200"
    import keenyspace.paths as paths_mod

    importlib.reload(paths_mod)
    import keenyspace.config as cfg

    importlib.reload(cfg)
    cfg.get_client_settings.cache_clear()  # type: ignore[attr-defined]
    import keenyspace.auth as auth_mod

    importlib.reload(auth_mod)
    import keenyspace.clients.http as http_mod

    importlib.reload(http_mod)
    import keenyspace.cli.backup as backup_mod

    importlib.reload(backup_mod)
    import keenyspace.__main__ as main_mod

    return importlib.reload(main_mod)


def _seed_auth(config_dir: Path, *, api_key: str = "ks_live_test") -> None:
    import json
    import stat

    auth_path = config_dir / "auth.json"
    auth_path.write_text(json.dumps({"api_key": api_key}))
    os.chmod(auth_path, stat.S_IRUSR | stat.S_IWUSR)


def test_backup_writes_chunks_to_output_path(
    temp_config_dir: dict[str, Path],
    cli_runner: CliRunner,
    httpserver: HTTPServer,
    tmp_path: Path,
) -> None:
    payload = b"\x1f\x8b\x08\x00fake-gzip-magic" + b"x" * 1024
    httpserver.expect_request("/v1/admin/backup", method="POST").respond_with_data(
        payload, content_type="application/gzip"
    )
    _seed_auth(temp_config_dir["config_dir"])
    server_url = httpserver.url_for("").replace("localhost", "127.0.0.1")
    main_mod = _reload_and_get_app(server_url)
    out = tmp_path / "out.tar.gz"
    result = cli_runner.invoke(  # type: ignore[attr-defined]
        main_mod.app,  # type: ignore[attr-defined]
        ["backup", "-o", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert out.read_bytes() == payload


def test_backup_default_output_path_iso_named(
    temp_config_dir: dict[str, Path],
    cli_runner: CliRunner,
    httpserver: HTTPServer,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    payload = b"hello"
    httpserver.expect_request("/v1/admin/backup", method="POST").respond_with_data(
        payload, content_type="application/gzip"
    )
    _seed_auth(temp_config_dir["config_dir"])
    server_url = httpserver.url_for("").replace("localhost", "127.0.0.1")
    main_mod = _reload_and_get_app(server_url)
    cwd_target = tmp_path / "out-cwd"
    cwd_target.mkdir()
    os.chdir(cwd_target)
    result = cli_runner.invoke(  # type: ignore[attr-defined]
        main_mod.app,  # type: ignore[attr-defined]
        ["backup"],
    )
    assert result.exit_code == 0, result.output
    candidates = list(cwd_target.glob("keenyspace-backup-*.tar.gz"))
    assert candidates, f"no default-named backup in {cwd_target}"
    assert candidates[0].read_bytes() == payload


def test_backup_no_auth_exits_2(
    temp_config_dir: dict[str, Path],
    cli_runner: CliRunner,
    httpserver: HTTPServer,
    tmp_path: Path,
) -> None:
    server_url = httpserver.url_for("").replace("localhost", "127.0.0.1")
    main_mod = _reload_and_get_app(server_url)
    out = tmp_path / "out.tar.gz"
    result = cli_runner.invoke(  # type: ignore[attr-defined]
        main_mod.app,  # type: ignore[attr-defined]
        ["backup", "-o", str(out)],
    )
    assert result.exit_code == 2, result.output
    assert "Not logged in" in result.output


def test_backup_propagates_http_error(
    temp_config_dir: dict[str, Path],
    cli_runner: CliRunner,
    httpserver: HTTPServer,
    tmp_path: Path,
) -> None:
    httpserver.expect_request("/v1/admin/backup", method="POST").respond_with_data(
        "boom", status=500
    )
    _seed_auth(temp_config_dir["config_dir"])
    server_url = httpserver.url_for("").replace("localhost", "127.0.0.1")
    main_mod = _reload_and_get_app(server_url)
    out = tmp_path / "out.tar.gz"
    result = cli_runner.invoke(  # type: ignore[attr-defined]
        main_mod.app,  # type: ignore[attr-defined]
        ["backup", "-o", str(out)],
    )
    assert result.exit_code != 0, result.output
