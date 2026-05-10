Golden fixture 07: WAL fragment creates a brand-new page for a second topic (first-write).

Bucket: golden. Labeler: deployer (KeenySpace v1 eval baseline).

Scenario: A WAL entry documents the WAL framing format, specifically the ULID-based
entry IDs and the XML attribute structure. No existing page covers this topic. The
vault is empty. The compile agent should produce a create op for notes/wal-format.md.
