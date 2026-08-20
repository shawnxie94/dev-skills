---
name: codebase-orientation
description: Build a concise engineering map of an unfamiliar or partially-known repository before planning or changing code. Uses CodeGraph as the relationship and flow backend when a project index exists, with the codegraph CLI and MCP explore tool as the primary retrieval path. Use when the user asks to understand a codebase, orient in a repo, map architecture, identify modules, find entry points, learn how to run or test a project, prepare for PRD/TRD/execution planning against an existing system, assess where a change should be made, or uses Chinese requests such as 了解代码库, 代码库导向, 梳理架构, 找入口, 怎么跑. Query the local .codegraph index first, verify facts from live files and configs, and never treat an index as a substitute for current-file verification.
---

# Codebase Orientation

Use this skill to understand a repository before design, planning, debugging, or implementation. The output should help the next step operate on real code paths instead of guesses.

## Required Retrieval Backend: CodeGraph

CodeGraph is the primary relationship and flow backend for indexed source code. It stores a local `.codegraph/` SQLite index, has no API-key requirement, and keeps the index fresh through its file watcher when the MCP server is running. The main retrieval primitive is `codegraph_explore`: one call can return relevant line-numbered source, call paths, dynamic-dispatch hops, and a change-impact summary.

Install the CLI with the repository's `install.sh`, or directly:

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh

# npm fallback
npm install -g @colbymchenry/codegraph
```

Connect it to Codex when the local agent configuration is not already managed:

```bash
codegraph install --target=codex --yes
```

Verify the CLI:

```bash
codegraph --version
codegraph status --json <repo-root>
```

If a project has no `.codegraph/` index, report that state and initialize it only when indexing is in scope:

```bash
cd <repo-root>
codegraph init .
```

`codegraph init` creates the local index and performs the initial full indexing pass. Do not silently claim graph-backed results for an unindexed project.

## Retrieval Workflow

1. Confirm the project path and index state.
   - Run `codegraph status --json <repo-root>` when a local CLI is available.
   - Inspect `initialized`, `pendingChanges`, `index.state`, `index.pendingRefs`, and `index.reindexRecommended`.
   - If the MCP server is available, `codegraph_explore` is the first call for source-structure questions. Pass `projectPath` when querying a project other than the MCP server's default project.

2. Use the retrieval primitive that matches the question.
   - General architecture, "how does X work", or an area survey: `codegraph_explore` with a natural-language question or a bag of symbol/file names.
   - A shell-only or subagent environment: `codegraph explore "<question>" --path <repo-root>`.
   - Symbol lookup: `codegraph query <symbol> --path <repo-root>`.
   - Incoming/outgoing flow: `codegraph callers <symbol> --path <repo-root>` or `codegraph callees <symbol> --path <repo-root>`.
   - Change blast radius: `codegraph impact <symbol> --path <repo-root>`.
   - Affected tests after file changes: `codegraph affected <files...> --path <repo-root>`.
   - File structure: `codegraph files --path <repo-root>`.

3. Treat the returned source as the indexed source, but check freshness signals.
   - `codegraph_explore` returns verbatim, line-numbered source for the selected symbols and files; use it directly to understand the flow.
   - If the response marks a file as changed after the last sync, read that specific file directly and run `codegraph sync <repo-root>` when manual sync is appropriate.
   - For CLI-only workflows, run `codegraph sync <repo-root> --quiet` before retrieval when `status --json` reports pending changes. Use `codegraph index <repo-root> --quiet` for a partial/failed index or when `reindexRecommended` is true.
   - Config files, docs, generated manifests, and exact run commands may not be represented as source symbols; inspect those files directly.

4. Establish the repository shape from live files.
   - Identify language, framework, package manager, and major directories.
   - Note whether the repo is an app, library, service, monorepo, plugin, or mixed workspace.
   - Find install, dev server, build, lint, test, typecheck, migration, and local-service commands from README, manifests, Makefiles, CI, and scripts.

5. Map architecture and risk boundaries.
   - Use `codegraph_explore` for cross-module relationships and `codegraph impact` for proposed changes.
   - Verify public contracts, schemas, auth, payments, background jobs, caches, concurrency, and deployment-sensitive claims from live files.
   - Separate confirmed facts from CodeGraph leads and inferences.

6. Produce next-step inputs.
   - Recommend the smallest set of files and commands the next skill should use.
   - State what context should feed `write-trd`, `write-execution-plan`, `bug-reproduction`, `change-impact-analysis`, or implementation work.

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

List the `codegraph_explore`, `codegraph query`, `callers`, `callees`, or `impact` calls that produced the key leads. Call out which facts were re-verified from live files. Omit the section only if no CodeGraph call was possible, and explain why.

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

<Context that should feed write-trd, write-execution-plan, bug reproduction, change-impact-analysis, or implementation>

## Open Questions

<Unknowns that need confirmation>
```

For small repositories, compress the output. For large repositories, focus on the portions relevant to the user's stated goal and call out unexplored areas.
