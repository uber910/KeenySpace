from __future__ import annotations

import asyncio
import fcntl
import hashlib
import html
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from ulid import ULID

from .framing import format_entry
from .locks import WorkspaceLockRegistry


class PayloadTooLarge(ValueError):
    pass


def _blocking_append(wal_file: Path, payload: bytes, multi_worker: bool) -> None:
    wal_file.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(wal_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        if multi_worker:
            fcntl.flock(fd, fcntl.LOCK_EX)
        os.write(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)


async def append_log(
    *,
    ws_uuid: UUID,
    ws_root: Path,
    content: str,
    actor: str,
    source: str,
    client_version: str | None,
    parent_id: ULID | None = None,
    settings: object,
    locks: WorkspaceLockRegistry,
) -> ULID:
    from keenyspace_server.config import Settings as _Settings

    s = settings if isinstance(settings, _Settings) else settings  # type: ignore[assignment]

    max_bytes: int = getattr(getattr(s, "wal", s), "max_entry_bytes", 256 * 1024)
    multi_worker: bool = getattr(getattr(s, "auth", s), "multi_worker", False)

    if len(content.encode()) > max_bytes:
        raise PayloadTooLarge(
            f"Content exceeds maximum size of {max_bytes} bytes"
        )

    ws_lock = await locks.for_workspace(ws_uuid)
    async with ws_lock:
        wal_path = ws_root / "logs" / f"{datetime.now(timezone.utc).date().isoformat()}.md"
        ts = datetime.now(timezone.utc)
        entry_id = ULID.from_datetime(ts)
        content_hash = "sha256:" + hashlib.sha256(content.encode()).hexdigest()

        escaped_actor = html.escape(actor, quote=True)
        payload = format_entry(
            entry_id=entry_id,
            ts=ts,
            actor=escaped_actor,
            source=source,
            client_version=client_version,
            content_hash=content_hash,
            parent_id=parent_id,
            content=content,
        )
        await asyncio.to_thread(
            _blocking_append, wal_path, payload, multi_worker
        )

    from keenyspace_server.observability.metrics import WAL_APPENDS_TOTAL, WAL_APPEND_LATENCY
    WAL_APPENDS_TOTAL.labels(workspace=str(ws_uuid), source=source).inc()

    return entry_id
