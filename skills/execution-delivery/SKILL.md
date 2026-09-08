---
name: execution-delivery
description: Turn a settled TRD, technical design, or implementation scope into an executable delivery contract, in two modes. `plan` (default) first assesses whether parallel execution is worthwhile, then writes either a whole-goal batch plan or a parallel DAG plan — no code（执行计划、实施计划、拆任务、开发计划）; `delegate` routes an approved plan to the current session or a subagent and produces bounded handoff packets when needed（远端交接、远程任务、委派任务、任务包）.
---

# Execution Delivery

Route the request to one mode, load only that mode's reference, and produce only that mode's artifact. Neither mode implements code. A plan request has a user decision gate: first assess parallelism, then generate the selected plan shape after the user chooses.

## Mode Selection

| Mode | Use When | Do Not Use When | Reference |
|---|---|---|---|
| `plan` | TRD or technical direction is clear enough to assess parallelism and produce a batch or parallel-DAG execution plan | Requirements or technical boundaries are still unclear; the plan is already approved and only execution routing is needed | [references/plan.md](references/plan.md) |
| `delegate` | An approved canonical plan must be routed to the current session or a subagent; packet files are needed only for subagent execution | The plan is draft, missing, or too vague; plan shape or execution target is still undecided | [references/delegate.md](references/delegate.md) |

Decision rules:

- Default to `plan`. Enter `delegate` only when the source plan is approved, or the user explicitly accepts draft-only packets.
- `plan` must begin with a lightweight parallelism assessment. Recommend `batch` unless independent work and meaningful time savings justify parallelism. If the user has not chosen `batch` or `parallel_dag`, return the assessment and stop; do not write an approved execution plan.
- Do not run plan generation and delegation in one turn by default: the selected plan shape and the approved plan are inputs to the later delegate decision.
- `batch` is a single whole-goal plan with one root unit and one final acceptance scope. Do not manufacture a DAG merely to describe serial implementation steps.
- `parallel_dag` is opt-in after the user chooses parallel execution. It requires dependencies, actor contracts, write ownership, and per-node acceptance plus final integration acceptance.
- `delegate` must preserve the selected plan shape and must obtain an execution target: `current_session` or `subagent`. Never silently turn `delegate` into remote execution.
- If a parallel plan is missing, stale, or ambiguous during delegation, hand back to plan mode instead of inventing a second DAG. A batch plan must not be rejected merely because it has no DAG.

## Shared Execution Contract

Every plan node and task packet carries the same linkage fields; do not rename or drop them between modes:

- Identity: `plan_id`, `source_plan_sha256` (SHA-256 of the complete canonical plan file, never stored in its own frontmatter), `base_commit`, `task_id` (outer Task Pack or issue id when present), `plan_unit_id`.
- Provenance: `source_artifacts`, `source_hash`, `source_task_pack_sha256`, `acceptance_ids`, `evidence_required`.
- Boundaries: `write_ownership`, `forbidden_writes`, `mutex`, `required_capabilities`, `required_skills`.
- Orchestration: `orchestration_mode` is `batch` or `parallel_dag`; `execution_target` is `current_session` or `subagent` once delegate routing is selected. These are distinct from agent-brain's `execution_mode` task lane and the lower-level `parallel_mode` worktree taxonomy.
- Concurrency: `parallel_mode` is one of `read_only_parallel`, `serial_same_worktree`, `concurrent_write_worktree`, `serial_shared_writer`, decided after impact analysis. Read-only tasks may share a checkout; serializable disjoint writes may reuse one checkout under orchestration; simultaneous writes require dedicated branch and worktree; shared contracts, schemas, migrations, generated artifacts, dependency manifests, and lockfiles stay serial single-writer.

The canonical plan artifact lives on disk for implementation-bound work — normally `docs/plans/<feature-slug>-execution-plan.md` (or the configured execution-plan path) with `status: approved` before handoff. Chat-only prose is not a handoff.

`agent-brain` owns the outer Task Pack, allowed paths, acceptance lifecycle, and Done gate. `delivery-readiness` owns the cross-stage `plan_to_build` gate. Emit the shared fields and hand off; do not duplicate those contracts inside this skill.

Document artifact mode: check `.agent/config.toml`, falling back to `.dev-skills/config.toml` only when the former does not exist. When `[document_artifacts] enabled = true`, write plan and task files to the configured paths (`docs/plans/`, `tasks/draft|ready|blocked/`) with stable filenames and metadata frontmatter, and keep the chat reply to paths, statuses, and a concise summary. If a required file cannot be written while the mode is enabled, report the blocker instead of falling back to chat-only output.

## Handoff Map

- `plan` → approved with `orchestration_mode=batch|parallel_dag`: `delegate` for execution-target routing; accepted current-session implementation: agent-brain task mode (Task Pack), then `$implement-plan`; units, dependencies, or shared-write boundaries unclear: `codebase-analysis` (impact mode); refactor sequencing: `$refactor-plan` must have defined behavior protection first.
- `delegate` → `execution_target=current_session`: hand off the approved plan to `$implement-plan`; `execution_target=subagent`: create one whole-goal packet for `batch` or node packets for `parallel_dag`, then hand the packet to the child actor; plan unclear or too vague: back to `plan` mode; blast radius unclear: `codebase-analysis` (impact mode).
- `$implement-plan` → plan invalid or hash stale: back to `plan` mode before any repair or code change.

For subagent execution, the default contract is one goal and one final return. The coordinating agent waits for a terminal `completed`, `blocked`, or `failed` result; only `completed` starts batch or integration acceptance. A failed acceptance may receive at most one consolidated repair packet. A second failed attempt, or an unresolved blocker after the retry, ends the automated loop and returns the decision to the user.
