---
name: codebase-orientation
description: Build a concise engineering map of an unfamiliar or partially-known repository before planning or changing code. Prefer this skill over direct graphify for first-pass repository orientation, run/test command discovery, entry-point mapping, implementation planning inputs, and current-file verification. Use when the user asks to understand a codebase, orient in a repo, map architecture, identify modules, find entry points, learn how to run or test a project, prepare for PRD/TRD/execution planning against an existing system, or assess where a change should be made. When an existing graphify graph is available, use it only as an optional backend for architecture, relationship, and flow leads, then verify current facts from files. Focus on real files, commands, module responsibilities, data flow, dependencies, validation paths, and risk boundaries without modifying code.
---

# Codebase Orientation

Use this skill to understand a repository before design, planning, debugging, or implementation. The output should help the next step operate on real code paths instead of guesses.

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

Use graphify as an enhancement, not a replacement for live repository inspection. For first-pass repository orientation, this skill remains the owner of the workflow even when graphify is installed.

- If `graphify-out/graph.json` exists and the user's goal involves architecture, module relationships, data flow, call paths, or broad project content, query it first:
  - `graphify query "<user's repository question>"`
  - Use the result to prioritize which files and modules to inspect next.
- Treat graphify results as a map of extracted relationships. Verify current run commands, test commands, entry points, config, schemas, and high-risk claims directly from repository files.
- If graphify output conflicts with live files, trust live files and call out the graph as stale or incomplete.
- If there is no existing graph, do not build one by default during orientation. Recommend graphify only when the repository is large, mixed with substantial docs/media, likely to need repeated exploration, or the user explicitly asks for a graph.
- If `graphify query` is unavailable or fails, continue with normal file-based orientation and mention the fallback.

## Orientation Workflow

1. Check for a graphify backend when useful.
   - If `graphify-out/graph.json` exists and the goal benefits from relationship or flow context, run a graphify query first.
   - Capture useful nodes, paths, communities, or source locations as leads, not final proof.

2. Establish repository shape.
   - Identify language, framework, package manager, and major directories.
   - Note whether the repo is an app, library, service, monorepo, plugin, or mixed workspace.

3. Identify how to run and verify.
   - Find install, dev server, build, lint, test, typecheck, migration, and local service commands.
   - Mark commands as confirmed from files or inferred.

4. Map architecture and ownership.
   - Describe major modules and responsibilities.
   - Identify entry points and how requests, jobs, or user actions flow through the system.

5. Map data and dependencies.
   - Identify databases, schemas, migrations, external APIs, queues, caches, file storage, or generated artifacts.
   - Note integration boundaries and operational dependencies.

6. Identify risk boundaries.
   - Highlight public contracts, shared schemas, auth, payments, migrations, background jobs, caching, concurrency, or deployment-sensitive areas.

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

<If graphify was used, summarize graph-derived leads and which ones were verified from live files. Omit if graphify was not used.>

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
