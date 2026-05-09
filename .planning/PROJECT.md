# KeenySpace

## What This Is

KeenySpace — self-hosted opensource система для построения и совместного использования knowledge graph'ов между людьми и LLM-агентами. Каждый workspace — обычная директория markdown-файлов (Obsidian-совместимая); поверх стоит сервер, который отвечает за authn, MCP-доступ агентам и server-side compile накопленных логов в страницы.

Грубо: «Obsidian vault как managed multi-user resource с auth и MCP-доступом для агентов». Self-host-first, без vendor lock-in: потерять сервер = откатиться к single-user режиму на тех же файлах.

## Core Value

LLM-агенты безопасно читают и пополняют workspace через MCP, при этом сами файлы остаются обычной markdown-директорией, открываемой Obsidian'ом без сервера. Прикладная логика (prompts, шаги команд) живёт server-side и деплоится без обновления клиента.

## Requirements

### Validated

(None yet — ship to validate)

### Active

#### Server foundation
- [ ] Single ASGI app: FastAPI + FastMCP в одном процессе с префиксами `/v1/api/*`, `/v1/mcp`, `/v1/admin/*`
- [ ] Persistent state: FS root для workspaces + Postgres для registry
- [ ] Atomic write страниц (`tmp` + fsync + rename)
- [ ] WAL per workspace (append-only, daily-rotated, под per-workspace asyncio lock + flock)
- [ ] Health endpoints (`/healthz`, `/readyz`) и Prometheus metrics

#### Authentication (v1)
- [ ] OIDC interactive login flow (`/v1/api/auth/login` → IdP → callback → session token)
- [ ] API keys (`ks_live_*`) для programmatic доступа
- [ ] Authn middleware покрывает HTTP и MCP transport одинаково
- [ ] Session refresh

#### Workspace model
- [ ] Workspace = Obsidian vault на диске (UUID stable, slug human-readable)
- [ ] Default blueprint
- [ ] Workspace lifecycle: create (clone из blueprint), use, archive
- [ ] `.keenyspace/config.yaml` per workspace
- [ ] Obsidian compatibility: `.obsidian/` ignored sync, wikilinks как plain text

#### Compile pipeline
- [ ] Server-side compile-агент: WAL → pages через pydantic-ai + instructor
- [ ] Provider-agnostic LLM (Anthropic / OpenAI / Ollama) через единый pydantic-ai интерфейс
- [ ] Compile triggered ON-DEMAND (REST/MCP) и периодически через scheduler

#### Client (`keenyspace`)
- [ ] Установка: `uv tool install keenyspace`
- [ ] `keenyspace init`, `login`, `logout`, `status`
- [ ] `keenyspace workspace list/create/use/pull`
- [ ] `keenyspace ingest`, `query`, `lint`, `compile`
- [ ] `keenyspace hook session-start/session-end/pre-compact/post-compact/post-tool`
- [ ] `keenyspace daemon start/stop/status` для background tasks
- [ ] Server-driven model: команды тянут prompts/steps с сервера через MCP
- [ ] Конфиг в `~/.config/keenyspace/`, auth tokens с file mode 0600
- [ ] Post-compact context injection (base layer + smart selection)

#### MCP surface
- [ ] Базовые MCP tools: `read_page`, `append_log`, `search_workspace`, `get_instructions`, `list_blueprints`, etc. (точный inventory — implementation phase)
- [ ] Каждый MCP tool call проходит authn + authz middleware
- [ ] MCP transport mounted at `/v1/mcp`

#### Metrikus wiki migration
- [ ] Migration tool: import markdown-страниц Metrikus wiki в KeenySpace workspace как первичный dataset для тестирования
- [ ] Логика существующих scripts (compile, ingest, query, lint, hooks) перенесена в KeenySpace client+server (старые scripts не мигрируем — только функциональность)

#### Deployment v1
- [ ] Docker image
- [ ] docker-compose recipe (keenyspace + postgres + reverse proxy example)
- [ ] Setup guide для одного OIDC-провайдера (выбор провайдера — отдельное решение в roadmap)
- [ ] Backup/restore документация (FS root tar + pg_dump)

#### Public release v1
- [ ] AGPL-3.0 license + CLA process (DCO или signed CLA — TBD)
- [ ] Public GitHub repo (`README`, `CONTRIBUTING`, `LICENSE`, `NOTICE`, code of conduct)
- [ ] Versioned release (v0.1.0 alpha)
- [ ] Минимальная docs site / repo README с install, usage, MCP setup
- [ ] Observability defaults: structured jsonl logs, Prometheus metrics; Loki+Grafana — opt-in пример

### Out of Scope

#### v1 cuts (deferred to v1.5+)
- Multi-tenant authorization (роли, group-based ACL, custom permissions) — v1 = single-org, все authn'd видят всё
- Helm chart — v1 = только docker-compose; helm в v1.1
- Admin-driven blueprint CRUD UI — v1 = blueprint клонируется, но управление blueprint'ами через FS вручную
- Multi-machine replication / clustering — v2
- Encryption-at-rest, audit log redaction, privacy controls — отдельный design pass
- Vector search / embeddings / full-text grep — концепт KeenySpace = wikilink traversal в v1
- Real-time collab cursors — никогда (non-goal по vision.md)
- Hosted SaaS — никогда (non-goal)
- Auto-update клиента — не делаем (по vision.md)
- Push страниц клиентом — не существует архитектурно (server-side compile из WAL)
- npm-пакет клиента — не делаем, если не появится отдельный TS клиент
- Plugin system — отложено до v1.5+

#### Existing prototype
- Старые scripts/hooks/launchd plist в `~/Interexy/Metrikus/wiki/scripts` остаются как reference; KeenySpace клиент полностью их заменяет, но сами файлы prototype'а не мигрируются
- Сама Metrikus wiki как операционный сервис — out of scope (будет mothball'ена после миграции данных в KeenySpace workspace)

## Context

### Существующие материалы
В этой директории к моменту инициализации GSD уже существует first-pass design spec:
- `vision.md` — что и зачем, целевая аудитория, ethos, non-goals
- `concepts/workspace-model.md` — workspace = Obsidian vault, blueprints, FS layout
- `concepts/rbac-and-auth.md` — authn (OIDC + API keys); authz отложен
- `concepts/mcp-and-http-surface.md` — FastAPI + FastMCP в одном app, prefixes
- `concepts/client-model.md` — server-driven thin client, hooks integration с Claude Code, post-compact context injection
- `concepts/sync-and-storage.md` — write/read paths, WAL per workspace, conflict semantics
- `concepts/architecture.md` — process composition, deployment shapes, observability, secrets
- `open-questions.md` — отложенные вопросы (authz, license, repo structure до этого момента)
- `plans/post-compact-injection.md` — частный execution plan (уже отражён в client-model.md)

Эти документы — concept-уровень, без implementation-leak. Они не переписываются roadmap'ом, но используются как source of design intent. По итогам first phase implementation ожидается, что concepts/ переедет в `docs/design/` или `.planning/research/` (решение в roadmap).

### Целевая аудитория (из vision.md)
- Small/mid teams (3-30 чел): research labs, security teams, internal platform teams
- Data-sensitive orgs: legal, healthcare, financial, R&D
- Opensource self-hosters в духе Outline / Gitea / Forgejo deployer'ов
- Multi-agent workflow operators: команды, гоняющие несколько агентов параллельно

### Прежний prototype
В `~/Interexy/Metrikus/wiki/scripts` существует working prototype: набор Python hook-скриптов + launchd daemon, который частично закрывает scenario «agent пишет в shared markdown wiki». KeenySpace вырастает из этого опыта; функциональность (compile, ingest, query, hooks) переносится в KeenySpace client+server, prototype-код не мигрируется.

### Ethos (locked)
- Markdown primary, файлы — source of truth
- Obsidian-compatible
- No vendor lock-in
- External identity (OIDC через Ory/Keycloak/Authentik/Zitadel)
- Server-driven thin client
- Linux-style governance: opensource, self-host-first, без built-in billing/telemetry

## Constraints

- **Tech stack (locked):** Python 3.x; FastAPI + FastMCP; Postgres 16+; instructor + pydantic-ai для LLM операций; Loki+Grafana+Prometheus как default observability
- **License:** AGPL-3.0 + CLA (с relicensing right у maintainer'а — позволит при необходимости dual-license / Apache в будущем без переписывания истории)
- **Auth:** OIDC внешний; KeenySpace не имеет собственной auth-системы; v1 поддерживает один провайдер OIDC, выбор будет принят в roadmap
- **Deployment:** server сам TLS не терминирует; ожидает reverse proxy (Caddy/Traefik/nginx) снаружи; v1 = только docker-compose
- **Storage:** один process — один FS root, один Postgres; multi-machine replication out of scope v1
- **Indexing:** в v1 нет full-text/vector index; navigation через wikilink traversal
- **Project mode:** соло-разработка, side-project без deadline → Vertical MVP slicing (early end-to-end working scenarios > complete layers)
- **Repo structure:** monorepo в `keeny-space/` (server + client + helm chart позже + docs)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Source of truth = markdown файлы; сервер = sync/permission/query слой | Obsidian-совместимость, no vendor lock-in, потеря сервера не = потеря данных | — Pending |
| FastAPI + FastMCP в одном app, версионирование через URL prefix | Один process, один port, один TLS endpoint; единый authn middleware | — Pending |
| Multi-tenant abstraction в коде с дня один (но v1 ships single-org single-user) | Чтобы не переделывать data model при v1.5; storage layer уже multi-tenant aware | — Pending |
| FS layout: 1 workspace = 1 директория = 1 Obsidian vault, UUID на диске + slug в API | Stable identity при rename; Obsidian работает без модификаций | — Pending |
| Workspaces — first-class abstraction; blueprints как admin-only template workspaces | Аналог Postgres `template1`; cloning + versioning | — Pending |
| Client заменяет 5 hook-скриптов и launchd plist Metrikus wiki | Прежний prototype доказал концепт, KeenySpace — production-grade переписка | — Pending |
| Identity = External OIDC IdP (Ory / Keycloak / Authentik / Zitadel — выбор TBD) | Не строим свою auth; standards-compliant any-IdP support | — Pending |
| Authorization design отложен до выбора IdP; в v1 = «все authn'd видят всё» | Спека authz зависит от mapping IdP groups → permissions | — Pending |
| WAL per workspace, server-side compile, no client direct page write | Conflict-free model: append к WAL — единственный writeable surface клиента; LLM resolves семантические дубли при compile | — Pending |
| LLM stack server-side: pydantic-ai + instructor, provider-agnostic | Structured outputs + agent abstraction в одном | — Pending |
| Observability: Loki + Grafana + Prometheus default; jsonl на stdout универсален | Стандартный self-host стек, не Loki-специфично на app-уровне | — Pending |
| TLS терминируется снаружи (Caddy/Traefik/nginx), не сервером | Стандартная практика self-host софта (Postgres, Outline, GitLab) | — Pending |
| v1 = docker-compose; helm chart → v1.1 | Минимальный shape для соло-deploy; helm после feedback от первых deployer'ов | — Pending |
| Без vector search в v1; wikilink traversal | Концепт = graph navigation; vector добавим, если traversal не масштабируется | — Pending |
| **License = AGPL-3.0 + CLA** | Self-host-first → AGPL защищает от hosted-SaaS форков; CLA сохраняет relicensing flexibility | — Pending |
| Соло side-project, без deadline → Vertical MVP slicing | Early end-to-end working scenarios > complete horizontal layers; быстрее dogfood | — Pending |
| Migration: только функциональность scripts'ов Metrikus wiki переносится; данные wiki импортируются в KeenySpace workspace как первичный dataset | Prototype код = reference, не код для миграции; данные = реальный test workload | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-09 after initialization*
