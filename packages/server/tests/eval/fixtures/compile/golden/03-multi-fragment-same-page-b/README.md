Golden fixture 03: two WAL fragments about the API subsystem merged into one page.

Bucket: golden. Labeler: deployer (KeenySpace v1 eval baseline).

Scenario: Two WAL entries both describe the REST API surface. The first records that
FastAPI is the web framework at version 0.128. The second records that the /v1/api/
prefix is used for all REST endpoints. The vault has an existing notes/api.md. The
compile agent should merge both into a single update op on notes/api.md.
