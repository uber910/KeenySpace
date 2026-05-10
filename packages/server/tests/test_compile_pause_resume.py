from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update


PG_URL = os.environ.get("KEENYSPACE_DB__URL")

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(not PG_URL, reason="postgres unavailable; KEENYSPACE_DB__URL not set"),
]


async def _seed_paused_workspace(slug: str) -> None:
    from keenyspace_server.db.session import get_db_session
    from keenyspace_server.db.models import Workspace
    async with get_db_session() as session:
        ws = (await session.execute(select(Workspace).where(Workspace.slug == slug))).scalar_one()
        await session.execute(
            update(Workspace).where(Workspace.uuid == ws.uuid).values(
                compile_state="paused",
                compile_paused_reason="loop_abort",
                compile_paused_at=datetime.now(UTC),
            )
        )
        await session.commit()


async def _seed(client: AsyncClient, dev_token: str) -> str:
    slug = f"pause-resume-{uuid4().hex[:8]}"
    resp = await client.post(
        "/v1/api/workspaces/",
        json={"slug": slug, "blueprint": "default"},
        headers={"Authorization": f"Bearer dev-{dev_token}"},
    )
    assert resp.status_code == 201, resp.text
    return slug


async def test_post_compile_returns_409_when_paused(tmp_path: Path) -> None:
    dev_token = "pause-resume-token"
    os.environ["KEENYSPACE_AUTH__DEV_TOKEN"] = dev_token
    os.environ["KEENYSPACE_FS__ROOT"] = str(tmp_path)
    from keenyspace_server.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]
    from keenyspace_server.main import build_app
    app = build_app()

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/healthz")
        if health.status_code in (500, 503):
            pytest.skip("server not ready")
        slug = await _seed(client, dev_token)
        await _seed_paused_workspace(slug)

        resp = await client.post(
            f"/v1/api/workspaces/{slug}/compile",
            headers={"Authorization": f"Bearer dev-{dev_token}"},
        )
        assert resp.status_code == 409, resp.text
        body = resp.json()
        assert body["detail"]["paused_reason"] == "loop_abort"
        assert body["detail"]["paused_at"] is not None


async def test_post_compile_resume_resets_state(tmp_path: Path) -> None:
    dev_token = "resume-token"
    os.environ["KEENYSPACE_AUTH__DEV_TOKEN"] = dev_token
    os.environ["KEENYSPACE_FS__ROOT"] = str(tmp_path)
    from keenyspace_server.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]
    from keenyspace_server.main import build_app
    app = build_app()

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/healthz")
        if health.status_code in (500, 503):
            pytest.skip("server not ready")
        slug = await _seed(client, dev_token)
        await _seed_paused_workspace(slug)

        r = await client.post(
            f"/v1/api/workspaces/{slug}/compile/resume",
            headers={"Authorization": f"Bearer dev-{dev_token}"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["state"] == "idle"
        assert r.json()["paused_reason"] is None

        r2 = await client.post(
            f"/v1/api/workspaces/{slug}/compile/resume",
            headers={"Authorization": f"Bearer dev-{dev_token}"},
        )
        assert r2.status_code == 200
        assert r2.json()["state"] == "idle"


async def test_get_compile_status_returns_state(tmp_path: Path) -> None:
    dev_token = "status-token"
    os.environ["KEENYSPACE_AUTH__DEV_TOKEN"] = dev_token
    os.environ["KEENYSPACE_FS__ROOT"] = str(tmp_path)
    from keenyspace_server.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]
    from keenyspace_server.main import build_app
    app = build_app()

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/healthz")
        if health.status_code in (500, 503):
            pytest.skip("server not ready")
        slug = await _seed(client, dev_token)

        r = await client.get(
            f"/v1/api/workspaces/{slug}/compile/status",
            headers={"Authorization": f"Bearer dev-{dev_token}"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["state"] == "idle"
        assert body["last_wal_id"] is None
        assert body["paused_reason"] is None
