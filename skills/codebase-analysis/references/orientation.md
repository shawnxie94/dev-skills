# Codebase Orientation (orientation mode)

Mode reference for the `$codebase-analysis` skill. Read this file only after the router selects `orientation`: building an engineering map of an unfamiliar or partially-known repository before planning or changing code. The output should help the next step operate on real code paths instead of guesses.

## Required Retrieval Backend: CodeGraph

CodeGraph is the primary relationship and flow backend for indexed source code. It stores a local `.codegraph/` SQLite index and needs no API key. Reach it through its **CLI** — the canonical path in every host, including pi, which has no MCP client. The main retrieval primitive is `codegraph explore`: one call can return relevant line-numbered source, call paths, dynamic-dispatch hops, and a change-impact summary.

Install the CLI with the repository's `install.sh`, or directly:

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh

# npm fallback
npm install -g @colbymchenry/codegraph
```

Host wiring is optional and only relevant to hosts CodeGraph itself supports
(Claude Code, Cursor, Codex CLI, opencode, Hermes Agent, Gemini CLI,
Antigravity, Kiro, Copilot):

```bash
codegraph install --target=<id> --yes
```

pi is **not** an install target and has no MCP client: in pi, always use the
CLI. Do not assume a CodeGraph MCP tool exists just because another host has one.

Verify the CLI:

```bash
codegraph --version
codegraph status --json <repo-root>
```

If the CLI is missing entirely, report that CodeGraph is unavailable, fall back
to live-file inspection (`rg --files`, `rg`, manifests, tests), and label the
report as non-graph-backed. Do not imply graph coverage that was not available.

If a project has no `.codegraph/` index, report that state and initialize it only when indexing is in scope:

```bash
cd <repo-root>
codegraph init .
```

`codegraph init` creates the local index and performs the initial full indexing pass. A stale lock blocks indexing: run `codegraph unlock <repo-root>` first. Do not silently claim graph-backed results for an unindexed project.

## Retrieval Workflow

1. Confirm the project path and index state.
   - Run `codegraph status --json <repo-root>` when a local CLI is available.
   - Inspect `initialized`, `pendingChanges`, `index.state`, `index.pendingRefs`, and `index.reindexRecommended`.
   - State the index verdict (indexed / stale / unindexed / CLI unavailable) in the report; it bounds every graph-backed claim.
   - A stale lock blocks indexing: `codegraph unlock <repo-root>`. Long-lived background daemons are managed with `codegraph daemon`.

2. Use the retrieval primitive that matches the question (CLI in every host).
   - General architecture, "how does X work", or an area survey: `codegraph explore "<question>" --path <repo-root>`.
   - Task-scoped context (symbols + relationships + code blocks): `codegraph context "<task>" --path <repo-root>`.
   - Symbol lookup: `codegraph query <symbol> --path <repo-root>`.
   - One symbol with its caller/callee trail: `codegraph node <symbol> --path <repo-root>`.
   - Incoming/outgoing flow: `codegraph callers <symbol> --path <repo-root>` or `codegraph callees <symbol> --path <repo-root>`.
   - Change blast radius: `codegraph impact <symbol> --path <repo-root>`.
   - Affected tests after file changes: `codegraph affected <files...> --path <repo-root>`.
   - File structure: `codegraph files --path <repo-root>`.
   - Where the host wires CodeGraph's MCP server (Claude Code, Codex), the same primitives are exposed as `codegraph_explore` / `codegraph_node`. In pi they do not exist; run the CLI.

3. Treat the returned source as the indexed source, but check freshness signals.
   - `codegraph explore` returns verbatim, line-numbered source for the selected symbols and files; use it directly to understand the flow.
   - If the output marks a file as changed after the last sync, read that specific file directly and run `codegraph sync <repo-root> --quiet` when manual sync is appropriate.
   - Run `codegraph sync <repo-root> --quiet` before retrieval when `status --json` reports pending changes. Use `codegraph index <repo-root> --quiet` for a partial/failed index or when `reindexRecommended` is true.
   - Config files, docs, generated manifests, and exact run commands may not be represented as source symbols; inspect those files directly.

4. Establish the repository shape from live files.
   - Identify language, framework, package manager, and major directories.
   - Note whether the repo is an app, library, service, monorepo, plugin, or mixed workspace.
   - Find install, dev server, build, lint, test, typecheck, migration, and local-service commands from README, manifests, Makefiles, CI, and scripts.

5. Map architecture and risk boundaries.
   - Use `codegraph explore` for cross-module relationships and `codegraph impact` for proposed changes.
   - Verify public contracts, schemas, auth, payments, background jobs, caches, concurrency, and deployment-sensitive claims from live files.
   - Separate confirmed facts from CodeGraph leads and inferences.

6. Produce next-step inputs.
   - Recommend the smallest set of files and commands the next skill should use.
   - State what context should feed `write-trd`, execution-delivery (plan mode), `bug-reproduction`, codebase-analysis (impact mode), or implementation work.

## What To Inspect

Use fast repository inspection for facts CodeGraph does not own:

- File map: `rg --files`, top-level directories, package manifests, and config files.
- Project docs: README, docs, architecture notes, and runbooks.
- Build/runtime: package manager, framework, scripts, Docker, Makefile, and CI config.
- Entry points: app/server/main files, routes, jobs, CLIs, workers, and frontend pages.
- Tests: test directories, test scripts, fixtures, e2e setup, and CI checks.
- Data and integration: schemas, migrations, API clients, external services, queues, caches, and generated artifacts.

Do not create or update `AGENTS.md` as part of this skill. If durable repo guidance seems useful, mention it as a separate recommendation.

## CodeGraph Leads

List the `codegraph explore`, `context`, `query`, `node`, `callers`, `callees`, or `impact` calls that produced the key leads, and state the index verdict (indexed / stale / unindexed / CLI unavailable). Call out which facts were re-verified from live files. Omit the section only if no CodeGraph call was possible, and explain why.

## Output Format

Answer in the user's language unless they request otherwise. Use this structure when practical:

```markdown
## Repository Summary

<What this repo appears to be, based on files>

## Tech Stack

- <Language/framework/package manager/runtime>

## How To Run And Verify

| Purpose | Command | Evidence | Notes |
|---|---|---|---|
| <dev/test/build> | `<command>` | <file> | <confirmed/inferred> |

## Major Modules

| Path | Responsibility | Notes |
|---|---|---|
| <path> | <role> | <important context> |

## Entry Points And Flows

<Main runtime entry points and key data/request/user flows>

## CodeGraph Leads

<Retrieval calls, key results, and live-file verification status>

## Data, Config, And Integrations

<Schemas, migrations, env vars, APIs, queues, caches, storage, generated artifacts>

## Tests And Validation

<Available test layers, gaps, and practical validation path>

## Risk Boundaries

<Areas to handle carefully before editing>

## Recommended Next Reads

- <file or directory and why>

## Inputs For Next Step

<Context that should feed write-trd, execution planning, bug reproduction, impact analysis, or implementation>

## Open Questions

<Unknowns that need confirmation>
```

For small repositories, compress the output. For large repositories, focus on the portions relevant to the user's stated goal and call out unexplored areas.
