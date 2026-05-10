Golden fixture 04: two WAL fragments targeting two different pages.

Bucket: golden. Labeler: deployer (KeenySpace v1 eval baseline).

Scenario: Two WAL entries cover unrelated topics. The first is about the auth subsystem
(Starlette AuthMiddleware placement). The second is about the UI considerations (admin
web UI is deferred to v1.5). The vault only has an index.md. The compile agent should
produce two PageOps: one create for notes/auth.md and one create for notes/ui.md.
