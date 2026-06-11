---
name: codebase-orientation
description: Build a concise engineering map of an unfamiliar or partially-known repository before planning or changing code. Requires the `graphify` CLI (PyPI package `graphifyy`) as the relationship/flow backend; use it for run/test command discovery, entry-point mapping, implementation planning inputs, and current-file verification. Use when the user asks to understand a codebase, orient in a repo, map architecture, identify modules, find entry points, learn how to run or test a project, prepare for PRD/TRD/execution planning against an existing system, or assess where a change should be made. Run `graphify query` against `graphify-out/graph.json` for architecture, module relationships, data flow, and call-path leads, then verify current facts from files. If `graphify` is not installed or no graph exists, build one with `graphify update <path>` (AST-only) or `graphify extract <path>` (semantic) instead of falling back silently. Focus on real files, commands, module responsibilities, data flow, dependencies, validation paths, and risk boundaries without modifying code.
---

# Codebase Orientation

Use this skill to understand a repository before design, planning, debugging, or implementation. The output should help the next step operate on real code paths instead of guesses.

## Required Dependency: Graphify

This skill treats `graphify` as a **hard dependency**, not an optional enhancement. The orientation workflow asks architectural, relationship, data-flow, and call-path questions against a pre-built `graph.json` instead of re-grepping the whole tree. "Installing codebase-orientation" is therefore only complete once `graphify` is also installed and a graph has been produced for the target repository.

**Install the CLI** (the PyPI package is `graphifyy`, the CLI command is `graphify`):

```bash
# recommended
uv tool install graphifyy
# alternatives
pipx install graphifyy
pip install --user graphifyy
```

Verify:

```bash
graphify --version             # expect 0.8.x or later
graphify query --help          # confirm the query subcommand is registered
```

If `graphify` is missing when this skill runs:

1. Stop and tell the user: `codebase-orientation` requires the `graphify` CLI; do not silently fall back to file-only inspection.
2. Offer to install it via the `$skill-installer` skill or by running `uv tool install graphifyy` directly with user approval.
3. After install, build a graph for the target repository before re-running the workflow:

   ```bash
   cd <repo-root>
   graphify update .                    # AST-only pass, no LLM needed
   # or for a full semantic graph (slower, needs an LLM backend):
   graphify extract . --backend <openai|anthropic|gemini|kimi|deepseek|ollama>
   ```

Reference: [safishamsi/graphify](https://github.com/safishamsi/graphify) (active development branch `v8`).

## Core Principles

- Prefer evidence from files over assumptions.
- Start broad, then narrow toward the user's goal.
- Identify real entry points, runtime paths, data flow, and validation commands.
- Keep the pass read-only unless the user explicitly asks for setup or edits.
- Separate confirmed facts from inferences and open questions.
- Produce context that can feed `write-trd`, `write-execution-plan`, `bug-reproduction`, or implementation work.

## What To Inspect

Use fast repository inspection first:

- File map: `rg --files`, top-level directories, package manifests, config files.
- Project docs: README, docs, architecture notes, runbooks.
- Build/runtime: package manager, framework, scripts, Docker, Makefile, CI config.
- Entry points: app/server/main files, routes, jobs, CLIs, workers, frontend pages.
- Tests: test directories, test scripts, fixtures, e2e setup, CI checks.
- Data and integration: schemas, migrations, API clients, external services, queues, caches.
- Configuration: env vars, secrets references, feature flags, deployment config.

Do not create or update `AGENTS.md` as part of this skill. If durable repo guidance seems useful, mention it as a separate recommendation.

## Graphify Backend

Use graphify as the primary relationship/flow backend. For first-pass repository orientation, this skill remains the owner of the workflow — it asks the questions, verifies facts in live files, and produces the engineering map. Graphify supplies extracted nodes, edges, communities, and call paths so you do not have to rebuild them by hand.

- If `graphify-out/graph.json` already exists, query it before reading files broadly:
  - `graphify query "<user's repository question>"` — BFS traversal for relationship/flow questions.
  - `graphify path "<node-a>" "<node-b>"` — shortest path between two nodes.
  - `graphify explain "<node>"` — plain-language summary of a node and its neighbors.
  - `graphify affected "<node-or-change>"` — reverse traversal to find blast radius.
  - `graphify diagnose multigraph` — same-endpoint edge collapse risk in the current graph.
  - Use the results to prioritize which files and modules to inspect next.
- If `graph.json` does **not** exist, build it before relying on the backend:
  - `graphify update <path>` — AST-only pass, no LLM, no API key required.
  - `graphify extract <path> --backend <name>` — full semantic pass, requires an LLM API key.
  - For very large repos, `graphify extract --no-cluster` first, then `graphify cluster-only <path>`.
- Treat graphify results as a map of extracted relationships. Verify current run commands, test commands, entry points, config, schemas, and high-risk claims directly from repository files.
- If graphify output conflicts with live files, trust live files and call out the graph as stale or incomplete.
- If `graphify query` fails (parse error, missing node, backend not configured), surface the failure and rerun with a simpler question or rebuild the graph with `graphify update`; do not silently fall back to file-only orientation.

## Orientation Workflow

1. Confirm graphify is available and the graph is current.
   - Run `graphify --version` and `graphify query --help`; if either fails, follow the install steps in `Required Dependency: Graphify` before continuing.
   - If `graphify-out/graph.json` is missing or older than the working tree, run `graphify update <path>` (no LLM) or `graphify extract <path>` (semantic) first, then proceed.
   - If the graph is current, run an initial `graphify query` aligned with the user's stated goal to surface nodes, communities, and call paths as leads (not final proof).

2. Establish repository shape.
   - Identify language, framework, package manager, and major directories.
   - Note whether the repo is an app, library, service, monorepo, plugin, or mixed workspace.

3. Identify how to run and verify.
   - Find install, dev server, build, lint, test, typecheck, migration, and local service commands.
   - Mark commands as confirmed from files or inferred.

4. Map architecture and ownership.
   - Describe major modules and responsibilities.
   - Use `graphify query` and `graphify path` to confirm cross-module relationships and entry points before reporting them.

5. Map data and dependencies.
   - Identify databases, schemas, migrations, external APIs, queues, caches, file storage, or generated artifacts.
   - Note integration boundaries and operational dependencies.

6. Identify risk boundaries.
   - Highlight public contracts, shared schemas, auth, payments, migrations, background jobs, caching, concurrency, or deployment-sensitive areas.
   - Use `graphify affected` to estimate blast radius for proposed changes.

7. Produce next-step inputs.
   - Recommend which files to read next for the user's goal.
   - State what context should feed TRD, execution planning, debugging, or implementation.

## Handoff Rules

- If the user needs a technical design after orientation, hand off to `write-trd`.
- If the user needs implementation sequencing, hand off to `write-execution-plan`.
- If the user reported broken behavior, hand off to `bug-reproduction`.
- If the orientation reveals a concrete change with unclear affected modules or contracts, hand off to `change-impact-analysis`.

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

## Graphify Leads

<List the graphify queries, paths, explains, or affected calls that produced the key leads, and call out which facts were re-verified from live files. Omit only if no graphify call was made.>

## Data, Config, And Integrations

<Schemas, migrations, env vars, APIs, queues, caches, storage, generated artifacts>

## Tests And Validation

<Available test layers, gaps, and practical validation path>

## Risk Boundaries

<Areas to handle carefully before editing>

## Recommended Next Reads

- <file or directory and why>

## Inputs For Next Step

<Context that should feed write-trd, write-execution-plan, bug reproduction, or implementation>

## Open Questions

<Unknowns that need confirmation>
```

For small repositories, compress the output. For large repositories, focus on the portions relevant to the user's stated goal and call out unexplored areas.
