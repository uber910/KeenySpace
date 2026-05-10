Edge fixture 04: WAL fragment mentions a page that does not exist in the vault.

Bucket: edge. Labeler: deployer (KeenySpace v1 eval baseline).

Scenario: A WAL entry mentions updating a page (notes/nonexistent.md) that does not
exist in the vault. The compile agent's read_page tool raises ModelRetry on FileNotFoundError.
The agent should recover by emitting a create op instead of looping. The test verifies
that the resulting plan has action=create (not update) and no UsageLimitExceeded is raised.
