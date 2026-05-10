Golden fixture 02: two WAL fragments about the auth subsystem merged into one page.

Bucket: golden. Labeler: deployer (KeenySpace v1 eval baseline).

Scenario: Two WAL entries both relate to the authentication subsystem. The first records
that API keys use the ks_live_ prefix. The second records that OIDC bearer tokens are
accepted as an alternate path. The vault has an existing notes/auth.md. The compile agent
should merge both into a single update op on notes/auth.md.
