---
name: execution-delivery
description: Turn a settled TRD, technical design, or implementation scope into an executable delivery contract, in two modes. `plan` (default) writes the canonical execution plan — DAG, critical path, risk-first sequencing, verification checkpoints, no code（执行计划、实施计划、拆任务、开发计划）; `delegate` converts an approved plan or DAG node into bounded handoff task packets for remote workers, agent issues, or task files（远端交接、远程任务、委派任务、任务包）.
---

# Execution Delivery

Route the request to one mode, load only that mode's reference, and produce only that mode's artifact. Neither mode implements code.

## Mode Selection

| Mode | Use When | Do Not Use When | Reference |
|---|---|---|---|
| `plan` | TRD or technical direction is clear enough to sequence implementation into units, dependencies, and actor contracts | Requirements or technical boundaries are still unclear; the plan is already approved and only handoff packets are needed | [references/plan.md](references/plan.md) |
| `delegate` | An approved canonical plan or settled DAG node must be handed to a remote worker, managed-agent issue, or task file | The plan is draft, missing, or too vague; implementation should start locally without a packet | [references/delegate.md](references/delegate.md) |

Decision rules:

- Default to `plan`. Enter `delegate` only when the source plan is approved, or the user explicitly accepts draft-only packets.
- Do not run both modes in one turn: writing the plan and delegating it are two steps with approval in between.
- If the DAG is missing, stale, or ambiguous during delegation, hand back to `plan` mode instead of inventing a second DAG.

## Shared Execution Contract

Every plan node and task packet carries the same linkage fields; do not rename or drop them between modes:

- Identity: `plan_id`, `source_plan_sha256` (SHA-256 of the complete canonical plan file, never stored in its own frontmatter), `base_commit`, `task_id` (outer Task Pack or issue id when present), `plan_unit_id`.
- Provenance: `source_artifacts`, `source_hash`, `source_task_pack_sha256`, `acceptance_ids`, `evidence_required`.
- Boundaries: `write_ownership`, `forbidden_writes`, `mutex`, `required_capabilities`, `required_skills`.
- Concurrency: `parallel_mode` is one of `read_only_parallel`, `serial_same_worktree`, `concurrent_write_worktree`, `serial_shared_writer`, decided after impact analysis. Read-only tasks may share a checkout; serializable disjoint writes may reuse one checkout under orchestration; simultaneous writes require dedicated branch and worktree; shared contracts, schemas, migrations, generated artifacts, dependency manifests, and lockfiles stay serial single-writer.

The canonical plan artifact lives on disk for implementation-bound work — normally `docs/plans/<feature-slug>-execution-plan.md` (or the configured execution-plan path) with `status: approved` before handoff. Chat-only prose is not a handoff.

`agent-brain` owns the outer Task Pack, allowed paths, acceptance lifecycle, and Done gate. `delivery-readiness` owns the cross-stage `plan_to_build` gate. Emit the shared fields and hand off; do not duplicate those contracts inside this skill.

Document artifact mode: check `.agent/config.toml`, falling back to `.dev-skills/config.toml` only when the former does not exist. When `[document_artifacts] enabled = true`, write plan and task files to the configured paths (`docs/plans/`, `tasks/draft|ready|blocked/`) with stable filenames and metadata frontmatter, and keep the chat reply to paths, statuses, and a concise summary. If a required file cannot be written while the mode is enabled, report the blocker instead of falling back to chat-only output.

## Handoff Map

- `plan` → approved for delegation: this skill's `delegate` mode; accepted for local implementation: agent-brain task mode (Task Pack), then `$implement-plan`; units, dependencies, or shared-write boundaries unclear: `codebase-analysis` (impact mode); refactor sequencing: `$refactor-plan` must have defined behavior protection first.
- `delegate` → local implementation of a packet: `$implement-plan`; plan unclear or too vague: back to `plan` mode; blast radius unclear: `codebase-analysis` (impact mode).
- `$implement-plan` → plan invalid or hash stale: back to `plan` mode before any repair or code change.
