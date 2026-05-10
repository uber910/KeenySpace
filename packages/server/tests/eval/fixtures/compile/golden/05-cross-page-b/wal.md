<wal_entry id="01HXAA0000000000000000A51" ts="2026-05-10T14:00:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">WAL writes use a per-workspace asyncio.Lock to prevent concurrent append races in single-worker mode. The lock is registered in wal/locks.py and acquired before the filename is derived inside the lock scope to avoid a TOCTOU race on date-roll.</wal_entry>

<wal_entry id="01HXAA0000000000000000A52" ts="2026-05-10T14:05:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">The compile_cursors table stores last_wal_id and last_compile_hash per workspace. Advancing the cursor uses a CAS UPDATE to detect concurrent coordinator restarts and prevent double-compile.</wal_entry>

<wal_entry id="01HXAA0000000000000000A53" ts="2026-05-10T14:10:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">The keenyspace CLI uses Typer as its command framework. Commands include pull, push, backup, restore, and doctor. The doctor command is shipped in v1 as the primary self-host failure-mode diagnostic.</wal_entry>

