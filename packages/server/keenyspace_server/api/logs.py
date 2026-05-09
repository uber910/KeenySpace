from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from keenyspace_server.db.models import Workspace
from keenyspace_server.db.session import get_db
from keenyspace_server.wal import writer as wal_writer
from keenyspace_shared.mcp_contracts import AppendLogRequest, AppendLogResponse

router = APIRouter()


@router.post("/{slug}/logs", response_model=AppendLogResponse, status_code=201)
async def append_log_endpoint(
    slug: str,
    body: AppendLogRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> AppendLogResponse:
    result = await session.execute(select(Workspace).where(Workspace.slug == slug))
    ws = result.scalar_one_or_none()
    if ws is None:
        raise HTTPException(status_code=404, detail=f"workspace {slug!r} not found")

    settings = request.app.state.settings
    ws_root = settings.fs.root / "workspaces" / str(ws.uuid)
    locks = request.app.state.wal_locks

    actor_sub = request.user.identity if request.user.is_authenticated else "anonymous"
    actor = f"dev:{actor_sub}"

    client_version: str | None = None
    ua = request.headers.get("user-agent")
    if ua:
        client_version = ua[:64]

    from ulid import ULID as _ULID
    parent_ulid: _ULID | None = None
    if body.parent_id is not None:
        try:
            parent_ulid = _ULID.from_str(body.parent_id)
        except Exception:
            pass

    try:
        entry_id = await wal_writer.append_log(
            ws_uuid=ws.uuid,
            ws_root=ws_root,
            content=body.content,
            actor=actor,
            source="api",
            client_version=client_version,
            parent_id=parent_ulid,
            settings=settings,
            locks=locks,
        )
    except wal_writer.PayloadTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc))

    return AppendLogResponse(
        entry_id=str(entry_id),
        ts=datetime.now(timezone.utc),
    )
