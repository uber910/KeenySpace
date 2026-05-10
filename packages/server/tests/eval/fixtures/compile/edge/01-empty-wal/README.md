Edge fixture 01: empty WAL slice produces an idempotent_noop result.

Bucket: edge. Labeler: deployer (KeenySpace v1 eval baseline).

Scenario: The wal.md file is empty (no WAL entries). The coordinator's empty-slice
short-circuit path should detect zero entries from extract_wal_slice and return
idempotent_noop without invoking the compile agent at all.
