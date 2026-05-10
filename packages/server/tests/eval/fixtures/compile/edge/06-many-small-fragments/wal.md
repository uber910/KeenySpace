<wal_entry id="01HXAB000000000000000000C01" ts="2026-05-10T10:01:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">The compile agent runs in a single-worker process.</wal_entry>

<wal_entry id="01HXAB000000000000000000C02" ts="2026-05-10T10:02:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">Each compile pass is fully independent with no cross-pass memory.</wal_entry>

<wal_entry id="01HXAB000000000000000000C03" ts="2026-05-10T10:03:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">The WAL is the only writeable surface for clients.</wal_entry>

<wal_entry id="01HXAB000000000000000000C04" ts="2026-05-10T10:04:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">Temperature is hard-coded to 0 for compile agent calls.</wal_entry>

<wal_entry id="01HXAB000000000000000000C05" ts="2026-05-10T10:05:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">The compile agent uses read_page and search as its only tools.</wal_entry>

<wal_entry id="01HXAB000000000000000000C06" ts="2026-05-10T10:06:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">write_page is deliberately NOT registered as a tool.</wal_entry>

<wal_entry id="01HXAB000000000000000000C07" ts="2026-05-10T10:07:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">The compile agent output is a CompilePlan with a list of PageOps.</wal_entry>

<wal_entry id="01HXAB000000000000000000C08" ts="2026-05-10T10:08:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">Each PageOp has action, path, body, and frontmatter fields.</wal_entry>

<wal_entry id="01HXAB000000000000000000C09" ts="2026-05-10T10:09:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">The coordinator validates PageOp paths against the denylist before writing.</wal_entry>

<wal_entry id="01HXAB000000000000000000C10" ts="2026-05-10T10:10:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">The denylist includes .keenyspace/, logs/, _templates/, raw/, and CLAUDE.md.</wal_entry>

<wal_entry id="01HXAB000000000000000000C11" ts="2026-05-10T10:11:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">Idempotency is enforced via a sha256 hash of the (wal_ids, canonical_plan) triple.</wal_entry>

<wal_entry id="01HXAB000000000000000000C12" ts="2026-05-10T10:12:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">The hash is computed with model_dump(mode=json) plus json.dumps(sort_keys=True).</wal_entry>

<wal_entry id="01HXAB000000000000000000C13" ts="2026-05-10T10:13:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">A matching hash causes the coordinator to short-circuit and return idempotent_noop.</wal_entry>

<wal_entry id="01HXAB000000000000000000C14" ts="2026-05-10T10:14:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">The compile cursor stores last_wal_id and last_compile_hash in Postgres.</wal_entry>

<wal_entry id="01HXAB000000000000000000C15" ts="2026-05-10T10:15:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">Cursor advancement uses a CAS UPDATE to prevent concurrent coordinator restarts.</wal_entry>

<wal_entry id="01HXAB000000000000000000C16" ts="2026-05-10T10:16:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">The compile agent is invoked via asyncio.wait_for with a 180-second timeout.</wal_entry>

<wal_entry id="01HXAB000000000000000000C17" ts="2026-05-10T10:17:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">Timeout raises TimeoutError which the coordinator maps to abort_budget.</wal_entry>

<wal_entry id="01HXAB000000000000000000C18" ts="2026-05-10T10:18:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">Loop detection fires when the same (tool, args_hash) pair repeats 3 times.</wal_entry>

<wal_entry id="01HXAB000000000000000000C19" ts="2026-05-10T10:19:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">UsageLimitExceeded with detector.triggered=True means loop_abort.</wal_entry>

<wal_entry id="01HXAB000000000000000000C20" ts="2026-05-10T10:20:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">UsageLimitExceeded with detector.triggered=False means budget_exceeded.</wal_entry>

<wal_entry id="01HXAB000000000000000000C21" ts="2026-05-10T10:21:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">Both abort states transition the workspace compile_state to paused.</wal_entry>

<wal_entry id="01HXAB000000000000000000C22" ts="2026-05-10T10:22:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">Paused workspaces can be resumed via the /v1/api/workspaces/{slug}/compile/resume endpoint.</wal_entry>

