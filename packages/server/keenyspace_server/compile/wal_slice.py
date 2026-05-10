from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ulid import ULID

from keenyspace_server.wal.framing import format_entry
from keenyspace_server.wal.parser import WalEntry, parse_wal


@dataclass
class WalSlice:
    entries: list[WalEntry] = field(default_factory=list)
    formatted_text: str = ""

    @property
    def wal_first_id(self) -> str | None:
        return str(self.entries[0].id) if self.entries else None

    @property
    def wal_last_id(self) -> str | None:
        return str(self.entries[-1].id) if self.entries else None


def extract_wal_slice(ws_root: Path, last_wal_id: str | None) -> WalSlice:
    """Read every logs/YYYY-MM-DD.md, parse, return entries with id > last_wal_id (ULID lex order).

    ULID strings are lexicographically chronological (Crockford base32, 26 chars), so
    a string > comparison against `last_wal_id` is equivalent to a timestamp filter.
    """
    logs_dir = ws_root / "logs"
    if not logs_dir.is_dir():
        return WalSlice()

    all_entries: list[WalEntry] = []
    for log_file in sorted(logs_dir.glob("*.md")):
        try:
            text = log_file.read_text(encoding="utf-8")
        except OSError:
            continue
        all_entries.extend(parse_wal(text))

    # ULID is sortable by timestamp via lex order; sort to be defensive against
    # multi-file ordering surprises (parse order is per-file but we need global order).
    all_entries.sort(key=lambda e: str(e.id))

    if last_wal_id is not None:
        new_entries = [e for e in all_entries if str(e.id) > last_wal_id]
    else:
        new_entries = all_entries

    # Re-build formatted_text from raw file fragments — but parser strips framing,
    # so re-serialize via wal/framing.format_entry to guarantee identical bytes.
    chunks: list[bytes] = []
    for e in new_entries:
        chunks.append(format_entry(
            entry_id=ULID.from_str(str(e.id)),
            ts=e.ts,
            actor=e.actor,
            source=e.source,
            client_version=e.client_version,
            content_hash=e.content_hash,
            parent_id=e.parent_id,
            content=e.content,
        ))
    formatted_text = b"".join(chunks).decode("utf-8")

    return WalSlice(entries=new_entries, formatted_text=formatted_text)
