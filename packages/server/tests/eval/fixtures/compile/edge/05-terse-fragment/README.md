Edge fixture 05: single terse WAL fragment that is too vague to compile faithfully.

Bucket: edge. Labeler: deployer (KeenySpace v1 eval baseline).

Scenario: A WAL entry contains only a short ambiguous phrase: "update auth". There is
insufficient context to faithfully merge this into any existing page. The compile agent
should not confabulate — it should either place a TBD placeholder in the body or surface
the ambiguity in CompilePlan.notes. The test verifies one of these two conditions.
