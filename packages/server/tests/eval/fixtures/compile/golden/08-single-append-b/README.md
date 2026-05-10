Golden fixture 08: single WAL fragment append to an existing notes page (second single-append variant).

Bucket: golden. Labeler: deployer (KeenySpace v1 eval baseline).

Scenario: A single WAL entry records that pydantic-ai version 1.x is used for the compile
agent and that the defer_model_check=True flag must be set to avoid API key validation at
import time. The vault has an existing notes/compile.md. The compile agent should update
that page with the new information.
