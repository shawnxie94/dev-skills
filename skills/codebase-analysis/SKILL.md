---
name: codebase-analysis
description: Understand a repository or analyze the blast radius of a concrete change before design, planning, debugging, implementation, or commit. Two mutually exclusive modes. `orientation` maps an unfamiliar or partially-known repository — tech stack, run/test commands, modules, entry points, data flow, risk boundaries — backed by CodeGraph when a project index exists; use for 了解代码库, 代码库导向, 梳理架构, 找入口, 怎么跑. `impact` analyzes what a proposed change, current diff, refactor, API/schema/config/dependency change, or bug fix affects — modules, contracts, data, config, tests, compatibility risks; use for 影响面, 改动范围, 影响分析, 会不会影响. Do not load both modes by default — orientation answers "what is this system and how does it run", impact answers "what does this change affect".
---

# Codebase Analysis

Route the request to exactly one mode and load only that mode's reference. Neither mode implements changes.

## Mode Selection

| Mode | Use When | Do Not Use When | Reference |
|---|---|---|---|
| `orientation` | The repository, module layout, entry points, or run/test commands are unknown; preparing for design, planning, or debugging against an existing system | The user asks about the effect of a specific known change | [references/orientation.md](references/orientation.md) |
| `impact` | A concrete change, diff, API/schema/config/dependency change, or bug fix exists and its affected modules, contracts, data, or tests are unclear | The goal is general repository understanding with no specific change | [references/impact.md](references/impact.md) |

Decision rules:

- The two modes are mutually exclusive by default. Do not chain orientation into impact, or impact into orientation, inside one turn.
- Combine them only when a high-risk change lands in an unfamiliar repository: run orientation first, report its map, then run impact in a separate step against the identified paths.
- If a bug reproduction or refactor already knows the affected paths, go straight to impact; if the user only asks "how does this work", stay in orientation.

## Shared Rules (both modes)

- Verify index or retrieval results against live files; never treat an index as a substitute for current-file facts. CodeGraph usage details live in [references/orientation.md](references/orientation.md); impact mode can use `codegraph impact` and `codegraph affected` on an indexed project.
- Analyze only what was asked: a repository map or one concrete change — not the whole system plus every dependency.
- Separate confirmed facts from leads and inferences.
- Produce one artifact: an orientation map or an impact report. Do not emit both.

Document artifact mode: check `.agent/config.toml`, falling back to `.dev-skills/config.toml` only when the former does not exist. When `[document_artifacts] enabled = true`, prefer returning the map or report in chat unless the user asks for a managed file; these artifacts are decision inputs, not canonical delivery documents.

## Handoff Map

- `orientation` → technical direction needed: `$write-trd`; planning against the mapped system: execution-delivery (plan mode); a suspected bug on a path found here: `$bug-reproduction`.
- `impact` → design changes required: `$write-trd`; task ordering or dependencies change: execution-delivery (plan mode); refactor-specific impact: `$refactor-plan`; discovered during implementation: back to `$implement-plan` with updated scope; discovered before commit: back to `$prepare-commit` with validation recommendations.
