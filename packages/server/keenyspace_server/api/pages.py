from __future__ import annotations

import io
import os
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from keenyspace_server.db.models import Workspace
from keenyspace_server.db.session import get_db
from keenyspace_server.fs.path_safety import UnsafePath, open_workspace_page
from keenyspace_shared.mcp_contracts import ReadPageResponse

router = APIRouter()


@router.get("/{slug}/pages/{path:path}", response_model=ReadPageResponse)
async def get_page(
    slug: str,
    path: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> ReadPageResponse:
    result = await session.execute(select(Workspace).where(Workspace.slug == slug))
    ws = result.scalar_one_or_none()
    if ws is None:
        raise HTTPException(status_code=404, detail=f"workspace {slug!r} not found")

    settings = request.app.state.settings
    ws_root = settings.fs.root / "workspaces" / str(ws.uuid)

    try:
        fd, resolved = open_workspace_page(ws_root, path)
    except UnsafePath as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"page {path!r} not found")

    try:
        raw_content = io.FileIO(fd).read()
    finally:
        try:
            os.close(fd)
        except OSError:
            pass

    content_str = raw_content.decode("utf-8", errors="replace")
    frontmatter, body = _split_frontmatter(content_str)

    return ReadPageResponse(
        path=str(resolved.relative_to(ws_root)),
        content=body,
        frontmatter=frontmatter,
    )


def _split_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---\n"):
        return {}, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content
    yaml_text = content[4:end]
    body = content[end + 5:]
    try:
        fm = yaml.safe_load(yaml_text)
        if not isinstance(fm, dict):
            return {}, content
        return fm, body
    except yaml.YAMLError:
        return {}, content
