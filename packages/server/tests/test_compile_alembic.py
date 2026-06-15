from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

PG_URL = os.environ.get("KEENYSPACE_DB__URL")
SERVER_DIR = Path(__file__).parent.parent


@pytest.mark.skipif(not PG_URL, reason="postgres unavailable; KEENYSPACE_DB__URL not set")
def test_alembic_upgrade_creates_compile_runs_and_workspace_columns() -> None:
    env = {**os.environ, "KEENYSPACE_DB__URL": PG_URL}
    up = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=SERVER_DIR, env=env, capture_output=True, text=True,
    )
    assert up.returncode == 0, up.stderr

    import asyncio

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    async def _check() -> None:
        eng = create_async_engine(PG_URL)
        async with eng.connect() as conn:
            r = await conn.execute(text("SELECT to_regclass('public.compile_runs')"))
            assert r.scalar() == "compile_runs"
            cols = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='workspaces' AND column_name LIKE 'compile_%'"
            ))
            col_names = {row[0] for row in cols.fetchall()}
            assert {"compile_state", "compile_paused_reason", "compile_paused_at"} <= col_names
        await eng.dispose()

    asyncio.run(_check())


@pytest.mark.skipif(not PG_URL, reason="postgres unavailable; KEENYSPACE_DB__URL not set")
def test_alembic_downgrade_reverts_phase2() -> None:
    env = {**os.environ, "KEENYSPACE_DB__URL": PG_URL}
    subprocess.run(["uv", "run", "alembic", "upgrade", "head"], cwd=SERVER_DIR, env=env, check=True)
    down = subprocess.run(
        ["uv", "run", "alembic", "downgrade", "-1"],
        cwd=SERVER_DIR, env=env, capture_output=True, text=True,
    )
    assert down.returncode == 0, down.stderr

    import asyncio

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    async def _check() -> None:
        eng = create_async_engine(PG_URL)
        async with eng.connect() as conn:
            r = await conn.execute(text("SELECT to_regclass('public.compile_runs')"))
            assert r.scalar() is None
        await eng.dispose()

    asyncio.run(_check())

    subprocess.run(["uv", "run", "alembic", "upgrade", "head"], cwd=SERVER_DIR, env=env, check=True)
