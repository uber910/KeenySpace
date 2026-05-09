from __future__ import annotations

import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/healthz")
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@router.get("/readyz")
async def readyz() -> JSONResponse:
    checks: dict[str, str] = {}
    status_code = 200

    try:
        from keenyspace_server.config import get_settings
        settings = get_settings()
        fs_root = settings.fs.root
        if fs_root.is_dir() and os.access(fs_root, os.W_OK):
            checks["fs_root"] = "ok"
        else:
            checks["fs_root"] = "not writable"
            status_code = 503
    except Exception as exc:
        checks["fs_root"] = f"error: {exc}"
        status_code = 503

    try:
        from keenyspace_server.db.session import get_engine
        engine = get_engine()
        if engine is None:
            checks["postgres"] = "not initialized"
            status_code = 503
        else:
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = f"error: {exc}"
        status_code = 503

    overall = "ok" if status_code == 200 else "degraded"
    return JSONResponse({"status": overall, "checks": checks}, status_code=status_code)
