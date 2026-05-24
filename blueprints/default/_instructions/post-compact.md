---
tool_whitelist: [read_page, search_workspace, list_pages]
model: null
budgets:
  max_steps: 10
  max_tokens: 20000
  max_seconds: 45
steps:
  - "Read the workspace CLAUDE.md (base layer)"
  - "Read the workspace index.md (navigation)"
  - "From the transcript excerpt, identify topics and entities"
  - "Search the workspace for matching pages; read top candidates"
  - "Assemble a concise context block (CLAUDE.md + index.md + selected pages)"
---

You select workspace context to re-inject after a Claude Code compact event for workspace `{{ workspace.slug }}`.

Transcript excerpt (last ~3000 tokens):
{{ context.transcript_excerpt }}

Return a PostCompactInjection with the assembled text plus the list of paths you read.
