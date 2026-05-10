Edge fixture 06: 20+ small WAL fragments all related to one topic, consolidated into one page.

Bucket: edge. Labeler: deployer (KeenySpace v1 eval baseline).

Scenario: 22 short WAL entries each contribute a one-sentence observation about the
KeenySpace compile pipeline. All entries are about the same topic. The compile agent
should consolidate them into a single update op on index.md rather than creating 22
separate pages. The test verifies the wal.md has at least 20 entries and the expected
plan has exactly 1 PageOp.
