from __future__ import annotations

from datetime import datetime, timezone

import pytest
from ulid import ULID

from keenyspace_server.wal.framing import format_entry
from keenyspace_server.wal.parser import parse_wal


def _make_entry(
    content: str = "hello world",
    actor: str = "dev:default",
    source: str = "mcp",
    client_version: str | None = None,
    parent_id: ULID | None = None,
) -> bytes:
    ts = datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc)
    entry_id = ULID.from_datetime(ts)
    return format_entry(
        entry_id=entry_id,
        ts=ts,
        actor=actor,
        source=source,
        client_version=client_version,
        content_hash="sha256:abc123",
        parent_id=parent_id,
        content=content,
    )


def test_round_trip_basic() -> None:
    raw = _make_entry("hello world")
    entries = parse_wal(raw.decode())
    assert len(entries) == 1
    e = entries[0]
    assert e.content == "hello world"
    assert e.actor == "dev:default"
    assert e.source == "mcp"
    assert e.content_hash == "sha256:abc123"
    assert e.client_version is None
    assert e.parent_id is None


def test_round_trip_with_html_entities() -> None:
    content = "a < b && b > c"
    raw = _make_entry(content)
    entries = parse_wal(raw.decode())
    assert entries[0].content == content


def test_round_trip_closing_tag_in_content() -> None:
    content = "data </wal_entry> more data"
    raw = _make_entry(content)
    entries = parse_wal(raw.decode())
    assert entries[0].content == content


def test_round_trip_with_client_version() -> None:
    raw = _make_entry(client_version="claude-code/1.0")
    entries = parse_wal(raw.decode())
    assert entries[0].client_version == "claude-code/1.0"


def test_round_trip_with_parent_id() -> None:
    parent = ULID()
    raw = _make_entry(parent_id=parent)
    entries = parse_wal(raw.decode())
    assert str(entries[0].parent_id) == str(parent)


def test_multiple_entries_parsed() -> None:
    raw1 = _make_entry("entry 1")
    raw2 = _make_entry("entry 2")
    combined = raw1.decode() + raw2.decode()
    entries = parse_wal(combined)
    assert len(entries) == 2
    assert entries[0].content == "entry 1"
    assert entries[1].content == "entry 2"


def test_empty_wal_returns_empty_list() -> None:
    entries = parse_wal("")
    assert entries == []


def test_ulid_monotonicity() -> None:
    ts = datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc)
    u1 = ULID.from_datetime(ts)
    u2 = ULID.from_datetime(ts)
    assert str(u1)[:10] == str(u2)[:10]


def test_actor_html_escaped_in_output() -> None:
    raw = _make_entry(actor="actor<with>&special")
    text = raw.decode()
    assert "actor<with>&special" not in text
    entries = parse_wal(text)
    assert "actor" in entries[0].actor


def test_format_entry_attribute_order() -> None:
    raw = _make_entry()
    text = raw.decode()
    id_pos = text.find('id="')
    ts_pos = text.find('ts="')
    actor_pos = text.find('actor="')
    source_pos = text.find('source="')
    assert id_pos < ts_pos < actor_pos < source_pos
