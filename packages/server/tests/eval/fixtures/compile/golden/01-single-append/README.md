Golden fixture 01: single WAL fragment append to an existing index page.

Bucket: golden. Labeler: deployer (KeenySpace v1 eval baseline).

Scenario: A single WAL entry records that the KeenySpace project adopted AGPL-3.0
as its license on 2026-05-10. The vault already has an index.md with a heading.
The compile agent should append the licensing decision to index.md via an update op.
