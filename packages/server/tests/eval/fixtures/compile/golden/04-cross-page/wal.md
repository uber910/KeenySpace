<wal_entry id="01HXAA0000000000000000A41" ts="2026-05-10T13:00:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">The Starlette AuthMiddleware must be placed on the FastAPI root app before the /v1/mcp/ mount to ensure MCP requests are authenticated at the ASGI root layer. Placing it after the mount causes auth to be bypassed for MCP tool calls.</wal_entry>

<wal_entry id="01HXAA0000000000000000A42" ts="2026-05-10T13:05:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">The admin web UI is explicitly deferred to KeenySpace v1.5. In v1, all administrative operations are performed via CLI commands or direct Postgres queries. No admin UI surface will be built in Phase 1 through Phase 5.</wal_entry>

