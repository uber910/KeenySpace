Edge fixture 03: WAL fragment updating a page with malformed YAML frontmatter.

Bucket: edge. Labeler: deployer (KeenySpace v1 eval baseline).

Scenario: The vault contains notes/broken.md with an unclosed frontmatter fence (no
closing ---). A WAL entry targets this page for an update. The compile agent should
use the full-overwrite policy (D-06) to replace the malformed frontmatter entirely,
producing a clean output. The test verifies apply_plan succeeds and the resulting file
has parseable frontmatter.
