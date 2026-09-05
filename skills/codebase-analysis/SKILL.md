---
name: codebase-analysis
description: Understand a repository or analyze the blast radius of a concrete change before design, planning, debugging, implementation, or commit — or produce a study-grade reading of how it works and why. Three mutually exclusive modes. `orientation` maps an unfamiliar or partially-known repository — tech stack, run/test commands, modules, entry points, data flow, risk boundaries — backed by CodeGraph when a project index exists; use for 了解代码库, 代码库导向, 梳理架构, 找入口, 怎么跑. `deep-dive` produces a study-grade architectural walkthrough — core loops, execution harness, module design, design philosophy — and archives it as a durable learning note; use for 深入讲解, 深度解读, 深入剖析, deep-dive, core loop walkthrough, design ideas, 写深度笔记. `impact` analyzes what a proposed change, current diff, refactor, API/schema/config/dependency change, or bug fix affects — modules, contracts, data, config, tests, compatibility risks; use for 影响面, 改动范围, 影响分析, 会不会影响. Do not load more than one mode by default — orientation answers "what is this system and how does it run", deep-dive answers "how does it really work and why is it designed that way", impact answers "what does this change affect".
---

# Codebase Analysis

Route the request to exactly one mode and load only that mode's reference. Neither mode implements changes.

## Mode Selection

| Mode | Use When | Do Not Use When | Reference |
|---|---|---|---|
| `orientation` | The repository, module layout, entry points, or run/test commands are unknown; preparing for design, planning, or debugging against an existing system | The user asks about the effect of a specific known change, or explicitly wants depth | [references/orientation.md](references/orientation.md) |
| `deep-dive` | The user explicitly wants depth — core-loop walkthrough, harness, design ideas, tradeoffs — or a durable deep-dive note archived to a notes folder | The user only needs a quick map or run/entry info, or asks about a specific change's effect | [references/deep-dive.md](references/deep-dive.md) |
| `impact` | A concrete change, diff, API/schema/config/dependency change, or bug fix exists and its affected modules, contracts, data, or tests are unclear | The goal is general repository understanding with no specific change | [references/impact.md](references/impact.md) |

Decision rules:

- The modes are mutually exclusive by default. Do not chain one mode into another inside one turn.
- Sequential combination across separate steps is for known pairings only: orientation before impact for a high-risk change in an unfamiliar repository; orientation before deep-dive when the repository is unknown but the user explicitly asked for the study-grade reading.
- `orientation` vs `deep-dive` is a depth axis, not a topic axis: quick map with chat output → orientation; explicit depth request (深入讲解/深度解读/design ideas) or a notes-archive deliverable → deep-dive.
- If a bug reproduction or refactor already knows the affected paths, go straight to impact; if the user only asks "how does this work", stay in orientation; if they ask how it works *in depth* or want a study note, go to deep-dive.

## Shared Rules (both modes)

- Verify index or retrieval results against live files; never treat an index as a substitute for current-file facts. CodeGraph usage details live in [references/orientation.md](references/orientation.md) and [references/deep-dive.md](references/deep-dive.md); impact mode can use `codegraph impact` and `codegraph affected` on an indexed project.
- Analyze only what was asked: a repository map, a deep reading of chosen core paths, or one concrete change — not the whole system plus every dependency.
- Separate confirmed facts from leads and inferences.
- Produce one artifact: an orientation map, an impact report, or a deep-dive note. Do not emit more than one.

Document artifact mode: check `.agent/config.toml`, falling back to `.dev-skills/config.toml` only when the former does not exist. When `[document_artifacts] enabled = true`, prefer returning the map or report in chat unless the user asks for a managed file; these artifacts are decision inputs, not canonical delivery documents. The `deep-dive` mode is the exception by design: its canonical artifact is the durable learning note in the user's learning-notes folder, independent of workspace artifact mode.

## Handoff Map

- `orientation` → technical direction needed: `$write-trd`; planning against the mapped system: execution-delivery (plan mode); a suspected bug on a path found here: `$bug-reproduction`.
- `deep-dive` → the note is archived in the user's learning-notes folder and registered in its notes index (`~/Developer/learn/notes/INDEX.md`); further work on the now-understood system: `$write-trd` or execution-delivery (plan mode); a suspected bug found while reading: `$bug-reproduction`; a shallower re-run for quick reference: `orientation`.
- `impact` → design changes required: `$write-trd`; task ordering or dependencies change: execution-delivery (plan mode); refactor-specific impact: `$refactor-plan`; discovered during implementation: back to `$implement-plan` with updated scope; discovered before commit: back to `$prepare-commit` with validation recommendations.
