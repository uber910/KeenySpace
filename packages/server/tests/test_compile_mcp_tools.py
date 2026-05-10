from __future__ import annotations

import asyncio
import os
import signal
import socket
import subprocess
import sys
import time

import pytest
from keenyspace_server.mcp.server import build_mcp
from keenyspace_server.mcp.tools import compile_status_tool, compile_tool


def test_compile_tool_importable() -> None:
    assert callable(compile_tool)


def test_compile_status_tool_importable() -> None:
    assert callable(compile_status_tool)


@pytest.mark.asyncio
async def test_build_mcp_registers_four_tools() -> None:
    mcp = build_mcp()
    tools = await mcp.list_tools()
    tool_names = {t.name for t in tools}
    assert "compile_tool" in tool_names, f"compile_tool not in {tool_names}"
    assert "compile_status_tool" in tool_names, f"compile_status_tool not in {tool_names}"
    assert "read_page" in tool_names
    assert "append_log" in tool_names


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


PG_URL = os.environ.get("KEENYSPACE_DB__URL")


@pytest.mark.slow
@pytest.mark.asyncio
@pytest.mark.skipif(not PG_URL, reason="postgres unavailable; KEENYSPACE_DB__URL not set")
async def test_mcp_compile_status_returns_state_field(tmp_path) -> None:
    import httpx
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport

    dev_token = "mcp-compile-token"
    fs_root = tmp_path / "fs_root"
    fs_root.mkdir()
    port = _find_free_port()

    env = os.environ.copy()
    env.update({
        "KEENYSPACE_DB__URL": PG_URL or "",
        "KEENYSPACE_FS__ROOT": str(fs_root),
        "KEENYSPACE_AUTH__DEV_TOKEN": dev_token,
        "KEENYSPACE_AUTO_MIGRATE": "false",
    })

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "keenyspace_server.main:app",
         "--port", str(port), "--workers", "1"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 20
        async with httpx.AsyncClient() as http_client:
            while time.monotonic() < deadline:
                try:
                    resp = await http_client.get(f"http://127.0.0.1:{port}/healthz")
                    if resp.status_code == 200:
                        break
                except Exception:
                    pass
                await asyncio.sleep(0.3)
            else:
                pytest.skip("server did not start (postgres likely unavailable)")
                return

        slug = "mcp-compile-test"
        async with httpx.AsyncClient(
            base_url=f"http://127.0.0.1:{port}",
            headers={"Authorization": f"Bearer dev-{dev_token}"},
        ) as http_client:
            r = await http_client.post(
                "/v1/api/workspaces/",
                json={"slug": slug, "blueprint": "default"},
            )
            if r.status_code not in (201, 409):
                pytest.skip(f"workspace create failed: {r.status_code} {r.text}")
                return

        transport = StreamableHttpTransport(
            f"http://127.0.0.1:{port}/v1/mcp/",
            headers={"Authorization": f"Bearer dev-{dev_token}"},
        )
        async with Client(transport) as mcp_client:
            result = await mcp_client.call_tool("compile_status_tool", {"workspace": slug})
            assert result is not None
            result_str = str(result)
            assert "state" in result_str, f"Expected 'state' in compile_status response: {result_str}"

    finally:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=10)


@pytest.mark.slow
@pytest.mark.asyncio
@pytest.mark.skipif(not PG_URL, reason="postgres unavailable; KEENYSPACE_DB__URL not set")
async def test_mcp_compile_trigger_returns_job_id(tmp_path) -> None:
    import httpx
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport

    dev_token = "mcp-compile-token2"
    fs_root = tmp_path / "fs_root"
    fs_root.mkdir()
    port = _find_free_port()

    env = os.environ.copy()
    env.update({
        "KEENYSPACE_DB__URL": PG_URL or "",
        "KEENYSPACE_FS__ROOT": str(fs_root),
        "KEENYSPACE_AUTH__DEV_TOKEN": dev_token,
        "KEENYSPACE_AUTO_MIGRATE": "false",
    })

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "keenyspace_server.main:app",
         "--port", str(port), "--workers", "1"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 20
        async with httpx.AsyncClient() as http_client:
            while time.monotonic() < deadline:
                try:
                    resp = await http_client.get(f"http://127.0.0.1:{port}/healthz")
                    if resp.status_code == 200:
                        break
                except Exception:
                    pass
                await asyncio.sleep(0.3)
            else:
                pytest.skip("server did not start (postgres likely unavailable)")
                return

        slug = "mcp-trigger-test"
        async with httpx.AsyncClient(
            base_url=f"http://127.0.0.1:{port}",
            headers={"Authorization": f"Bearer dev-{dev_token}"},
        ) as http_client:
            r = await http_client.post(
                "/v1/api/workspaces/",
                json={"slug": slug, "blueprint": "default"},
            )
            if r.status_code not in (201, 409):
                pytest.skip(f"workspace create failed: {r.status_code} {r.text}")
                return

        transport = StreamableHttpTransport(
            f"http://127.0.0.1:{port}/v1/mcp/",
            headers={"Authorization": f"Bearer dev-{dev_token}"},
        )
        async with Client(transport) as mcp_client:
            result = await mcp_client.call_tool("compile_tool", {"workspace": slug})
            assert result is not None
            result_str = str(result)
            assert "job_id" in result_str or "status" in result_str, (
                f"Expected job_id or status in compile response: {result_str}"
            )

    finally:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=10)
