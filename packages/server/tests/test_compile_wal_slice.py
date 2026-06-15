from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from keenyspace_server.compile.wal_slice import WalSlice, extract_wal_slice
from keenyspace_server.wal.framing import format_entry
from ulid import ULID


def _make_entry_bytes(actor: str = "dev:test", content: str = "hello") -> tuple[ULID, bytes]:
    eid = ULID()
    ts = datetime.now(UTC)
    b = format_entry(
        entry_id=eid,
        ts=ts,
        actor=actor,
        source="api",
        client_version=None,
        content_hash="0" * 64,
        parent_id=None,
        content=content,
    )
    return eid, b


def test_extract_wal_slice_empty_logs_dir_returns_empty(tmp_path: Path) -> None:
    slice_ = extract_wal_slice(tmp_path, last_wal_id=None)
    assert isinstance(slice_, WalSlice)
    assert slice_.entries == []
    assert slice_.formatted_text == ""
    assert slice_.wal_first_id is None
    assert slice_.wal_last_id is None


def test_extract_wal_slice_last_wal_id_none_returns_all(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    _eid_a, ba = _make_entry_bytes(content="a")
    _eid_b, bb = _make_entry_bytes(content="b")
    _eid_c, bc = _make_entry_bytes(content="c")
    (logs / "2026-05-09.md").write_bytes(ba + bb)
    (logs / "2026-05-10.md").write_bytes(bc)

    slice_ = extract_wal_slice(tmp_path, last_wal_id=None)
    assert len(slice_.entries) == 3
    ids_in_order = [str(e.id) for e in slice_.entries]
    assert ids_in_order == sorted(ids_in_order)
    assert slice_.wal_first_id == ids_in_order[0]
    assert slice_.wal_last_id == ids_in_order[-1]


def test_extract_wal_slice_filters_by_last_wal_id(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    eid_a, ba = _make_entry_bytes(content="a")
    eid_b, bb = _make_entry_bytes(content="b")
    eid_c, bc = _make_entry_bytes(content="c")
    (logs / "2026-05-09.md").write_bytes(ba + bb + bc)

    sorted_ids = sorted([str(eid_a), str(eid_b), str(eid_c)])
    cursor = sorted_ids[1]
    slice_ = extract_wal_slice(tmp_path, last_wal_id=cursor)
    assert len(slice_.entries) == 1
    assert str(slice_.entries[0].id) == sorted_ids[2]


def test_extract_wal_slice_multi_file_global_ordering(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    _eid_a, ba = _make_entry_bytes(content="a")
    _eid_b, bb = _make_entry_bytes(content="b")
    _eid_c, bc = _make_entry_bytes(content="c")
    (logs / "2026-05-08.md").write_bytes(bc)
    (logs / "2026-05-09.md").write_bytes(ba + bb)

    slice_ = extract_wal_slice(tmp_path, last_wal_id=None)
    ids = [str(e.id) for e in slice_.entries]
    assert ids == sorted(ids)
