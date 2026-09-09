---
name: codebase-analysis
description: Map a repository, read it deeply, or assess what a concrete change affects. Three mutually exclusive modes, one per turn — `orientation`（了解代码库、梳理架构、找入口、怎么跑）, `deep-dive`（深入讲解、深度解读、deep-dive、写深度笔记）, `impact`（影响面、改动范围、影响分析）. Use before design, planning, debugging, implementation, or commit.
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

- Verify index or retrieval results against live files; never treat an index as a substitute for current-file facts.
- CodeGraph is reached through its **CLI** (`codegraph ...`); that is the canonical path in every host, including pi, which exposes no MCP client. `codegraph_explore` / `codegraph_node` are MCP tool names available only where the host wires CodeGraph's MCP server (Claude Code, Codex); never call them by name elsewhere and never invent a tool name for a command you can run.
- Declare index state before claiming graph-backed results: `codegraph status --json <repo-root>` (`initialized`, `pendingChanges`, `index.state`, `index.reindexRecommended`). A missing CLI, missing index, or stale index changes the report, not just the workflow.
- CodeGraph usage details live in [references/orientation.md](references/orientation.md) and [references/deep-dive.md](references/deep-dive.md); impact mode starts with `codegraph impact` and `codegraph affected` on an indexed project.
- Analyze only what was asked: a repository map, a deep reading of chosen core paths, or one concrete change — not the whole system plus every dependency.
- Separate confirmed facts from leads and inferences.
- Produce one artifact: an orientation map, an impact report, or a deep-dive note. Do not emit more than one.

Document artifact mode: check `.agent/config.toml`, falling back to `.dev-skills/config.toml` only when the former does not exist. When `[document_artifacts] enabled = true`, prefer returning the map or report in chat unless the user asks for a managed file; these artifacts are decision inputs, not canonical delivery documents. The `deep-dive` mode is the exception by design: its canonical artifact is the durable learning note in the user's learning-notes folder, independent of workspace artifact mode.

## Record the Run

After an orientation, deep-dive, or impact run finishes (including a blocked
outcome), append one feedback event so `skill-retrospective` has evidence:

```bash
python3 <dev-skills>/scripts/record_skill_run.py \
  --skill codebase-analysis \
  --status completed \
  --validation pass \
  --task-type orientation \
  --next-handoff write-trd
```

Use the mode you actually ran as `--task-type` (`orientation`, `deep-dive`, or
`impact`).

## Handoff Map

- `orientation` → technical direction needed: `$write-trd`; planning against the mapped system: execution-delivery (plan mode); a suspected bug on a path found here: `$bug-reproduction`.
- `deep-dive` → the note is archived in the user's learning-notes folder and registered in its notes index (`~/Developer/learn/notes/INDEX.md`); further work on the now-understood system: `$write-trd` or execution-delivery (plan mode); a suspected bug found while reading: `$bug-reproduction`; a shallower re-run for quick reference: `orientation`.
- `impact` → design changes required: `$write-trd`; task ordering or dependencies change: execution-delivery (plan mode); refactor-specific impact: `$refactor-plan`; discovered during implementation: back to `$implement-plan` with updated scope; discovered before commit: back to `$prepare-commit` with validation recommendations.
- Any mode: mapping or impact-scanning a large repository is context-heavy. Delegate the read to `$subagent-orchestration` with a `scout` (fresh context) and keep only the bounded map, impact list, or note path; the coordinating agent must not re-read the repository to "verify" the report, only the cited paths.
