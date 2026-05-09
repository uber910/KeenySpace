This workspace is an Obsidian-compatible KeenySpace vault.

Categories:
- `_templates/` — page templates for new knowledge artefacts
- `raw/` — verbatim agent ingest fragments (pre-compile); content here will be compiled into pages
- `logs/` — per-day WAL entries, lazy-created on first append_log call
- root-level `.md` pages — compiled knowledge artefacts

Wikilinks `[[concepts/foo]]` are plain text at the storage layer. The server does not rewrite them; navigation happens through the client and Obsidian.
