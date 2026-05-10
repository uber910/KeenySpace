<wal_entry id="01HXAA0000000000000000A21" ts="2026-05-10T11:00:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">KeenySpace API keys use the ks_live_ prefix for production keys. Keys are stored as bcrypt-hashed values in the api_keys table under the keenyspace_server.db.models module.</wal_entry>

<wal_entry id="01HXAA0000000000000000A22" ts="2026-05-10T11:05:00+00:00" actor="dev:test" source="api" content_hash="sha256:placeholder" parent_id="">OIDC bearer tokens are accepted as an alternate authentication path for human users. API keys remain the primary path for MCP agent sessions because short-lived OIDC tokens do not fit long-running agent sessions.</wal_entry>

