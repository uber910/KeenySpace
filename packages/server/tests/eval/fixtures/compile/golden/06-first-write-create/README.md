Golden fixture 06: WAL fragment creates a brand-new page (first-write).

Bucket: golden. Labeler: deployer (KeenySpace v1 eval baseline).

Scenario: A WAL entry describes the atomic write mechanism using fsync + rename.
There is no existing page for this topic. The vault is empty. The compile agent
should produce a create op for a new notes/atomic-writes.md page.
