# Execution Target and Delegation (delegate mode)

Mode reference for the `$execution-delivery` skill. Read this file only after
the router selects `delegate`: route an approved execution plan to the current
session or a subagent. A subagent target receives one whole-goal packet for a
`batch` plan, or bounded node packets for a `parallel_dag` plan. The target may
be a local child, remote Codex, managed-agent issue, squad child issue, GitHub
Issue, or workspace task file. This mode does not implement code.

## Core Principles

- Treat the handoff packet as the contract between planning and execution.
- Preserve traceability to PRD, TRD, execution plan, issues, decisions, and code context.
- Preserve the plan's `orchestration_mode`: do not create a DAG for a `batch` plan or a second DAG for a `parallel_dag` plan.
- Require an explicit execution target: `current_session` or `subagent`. Do not silently turn a routing request into remote execution.
- Keep every subagent task bounded by scope, exclusions, write ownership, verification, and acceptance criteria.
- Preserve required capabilities and required skills from the source execution-plan node when the target platform supports them.
- Preserve the shared contract fields defined in the router: `plan_id`, `source_plan_sha256`, `base_commit`, `task_id`, `plan_unit_id`, `source_artifacts`, `source_hash`, `source_task_pack_sha256`, `acceptance_ids`, and `evidence_required`.
- Preserve `orchestration_mode`, `execution_target`, and `execution_backend` in
  the packet. `execution_backend` is required only when the target is
  `subagent`; it must be `codex_subagent` or `zcode_mcp`. Do not reuse
  agent-brain's `execution_mode` task lane for the plan shape or adapter.
- Split parallel tasks only when the approved `parallel_dag` has clear dependencies and write boundaries.
- Put only currently executable parallel tasks in `ready`; tasks with unmet dependencies must stay draft or blocked.
- For a delegated `batch`, create one ready task for the whole goal rather than unrelated serial tasks.
- Do not implement code or redesign the feature; if the plan is unclear, hand back to plan mode or `codebase-analysis` (impact mode).
- Do not mark a subagent task ready unless the user or source artifact clearly indicates approval and the execution target is explicit.
- A subagent handoff is one goal and one final return by default. The coordinating agent waits for a terminal `completed`, `blocked`, or `failed` result; only `completed` starts acceptance. If acceptance fails, it may issue one consolidated repair packet; a second failed attempt or unresolved blocker escalates to the user.

## Inputs to Look For

Use the execution plan, TRD, PRD, issue context, codebase analysis, implementation DAG, user approval, target repository, branch policy, test commands, and existing task files when available.

Extract:

- Source artifacts and their file paths.
- Approved scope and explicit non-goals.
- The plan's `orchestration_mode`, selected or pending `execution_target`, and whole-goal or node-level handoff inputs.
- For `parallel_dag`: DAG nodes, dependencies, critical path, risk-first nodes, shared-write nodes, and per-node handoff inputs.
- For `batch`: the single root unit, internal sequence, final acceptance scope, and complete-goal handoff inputs.
- Required capabilities and required skills for the whole actor or each execution-plan node.
- Task Pack linkage and canonical acceptance ids for the whole goal or each execution-plan node.
- Plan hash, Task Pack hash, Acceptance Pack path/hash, and baseline commit when available.
- Modules, files, APIs, schemas, migrations, generated artifacts, and config that each task may touch.
- Verification commands, manual checks, fixtures, logs, or PR review gates.
- Target repo, target branch, branch naming, PR expectations, and feedback format.

## Target Routing

The delegate mode has two execution targets:

- `current_session`: route the approved plan directly to `$implement-plan` in
  the current session. Do not create a remote task packet. If the plan is
  `batch`, the current session owns the whole implementation and final
  acceptance. If the user requested `parallel_dag` but no additional actors
  are available, report that true parallelism cannot occur and ask to downgrade
  to `batch` or choose `subagent`.
- `subagent`: create a task packet for a child actor. For `batch`, the packet
  covers the complete goal and has one final acceptance scope. For
  `parallel_dag`, create one packet per runnable node and preserve the source
  dependencies.

## Subagent Backend Matrix And Runtime Adapters

`execution_backend` selects the runtime adapter after
`execution_target=subagent` has been chosen. Both adapters execute the packet;
neither adapter's success declaration is the final acceptance. The coordinator
waits for an explicit `completed` result before running canonical acceptance.
The protocols below describe supported integrations; they do not imply that
the current environment exposes every named tool.

| Backend | Dispatch | Long wait / status | One consolidated repair | Runtime boundary |
|---|---|---|---|---|
| `codex_subagent` | `multi_agent_v1__spawn_agent` with one complete goal or assigned DAG node | `multi_agent_v1__wait_agent`; bounded wait, no busy polling | `multi_agent_v1__send_input` to the same agent, once, with the complete repair packet | Codex child implementation and internal verification |
| `zcode_mcp` | `mcp__zcode_codex__zcode_dispatch` | `wait_ms` and terminal status; inspect with `zcode_status`, `zcode_messages`, or `zcode_diff` only when needed | `zcode_continue` once on the same task with the complete repair packet | ZCode code implementation and repository tests when explicitly available |

### `codex_subagent`

- Call `multi_agent_v1__spawn_agent` once for a `batch` whole-goal packet, or
  once per runnable `parallel_dag` node. The child receives one active goal and
  must not return after an internal step.
- Wait with `multi_agent_v1__wait_agent` for a bounded interval. Do not use
  repeated status retrieval or busy polling while the agent is unchanged.
- Require the final child response to include `completed`, `blocked`, or
  `failed`, plus changed files, tests, deviations, blockers, and `attempt`.
- Only after `completed`, run the coordinator's acceptance. If it fails, send
  one complete consolidated repair through `multi_agent_v1__send_input` to the
  same agent. A second failure or unresolved blocker goes to the user.

### `zcode_mcp`

- Call `mcp__zcode_codex__zcode_dispatch` with at least these mappings:
  `objective`, `implementation_paths`, `workspace_path`,
  `implementation_plan`, `acceptance`, `constraints`, `execution_mode`, and
  `workspace_mode`. Preserve the plan's `orchestration_mode`,
  `execution_target`, `execution_backend`, and linkage metadata in the
  implementation plan or constraints payload.
- Use `wait_ms` and the adapter's terminal status. Use `zcode_status`,
  `zcode_messages`, and `zcode_diff` only when a terminal result needs
  clarification or acceptance evidence is missing; do not turn these into
  periodic polling.
- Require a final `completed`, `blocked`, or `failed` response containing
  changed files, tests, deviations, blockers, and `attempt`. A successful
  ZCode response is still only an execution result, not coordinator acceptance.
- After a failed coordinator acceptance, call `zcode_continue` at most once
  with one complete consolidated repair packet. If ZCode requests permission
  or user input through `zcode_respond`, do not auto-approve; return a user
  blocker. Use `zcode_stop` only when the user or coordinator explicitly asks
  to stop.
- ZCode may implement code and run repository tests. Browser, desktop,
  visual, and other host-only acceptance capabilities remain with the
  coordinating session unless the adapter explicitly declares that capability
  and the approved plan authorizes it.

The adapter contract is:

```text
dispatch once → bounded wait → explicit terminal result → coordinator acceptance
                         ↘ one consolidated repair → bounded wait → acceptance
```

Do not claim that `codex_subagent` or `zcode_mcp` is available merely because
the protocol supports it. If the named runtime tool is unavailable, report a
blocked handoff and let the user choose another target/backend.

The target choice may be recorded in the plan when known, but `delegate` must
obtain it before creating a ready packet or starting current-session
implementation.

## Parallel DAG Task Groups

Use this section only when the approved plan has `orchestration_mode:
parallel_dag` and the target is `subagent`:

- Start from the source execution plan DAG. If the DAG is missing, stale, or
  ambiguous, hand back to plan mode instead of inventing a new one.
- Assign the same `parallel_group` and a stable `feature` value to all tasks.
- Assign a `phase` that reflects the DAG layer, such as `contract`, `backend`,
  `frontend`, `integration`, or `cleanup`.
- Preserve the execution plan unit IDs in each task packet with `plan_unit_id`.
- Put only root nodes with no unmet dependencies in `ready`.
- Put approved downstream nodes in `blocked` until their dependencies are
  accepted or merged.
- Add `unblocks` to each task when completing it can make downstream tasks
  runnable.
- Prefer a contract-first split when possible:

```text
contract/schema/API task
  -> backend task
  -> integration task

contract/schema/API task
  -> frontend task
  -> integration task
```

Do not use stacked branches by default. Prefer accepting the dependency task,
then creating or rebasing downstream task branches from the updated base
branch.

## Document Artifact Mode

Follow the shared document-artifact rules in the router SKILL.md. Subagent task
files use `tasks/draft/` by default, `tasks/ready/` only when explicitly
approved for subagent execution, and `tasks/blocked/` for approved but
dependency-blocked parallel tasks (or keep them in draft with `status:
blocked` when the blocked directory is not configured). A current-session
target does not need a task file. Use stable filenames such as
`tasks/draft/<feature-slug>-whole-goal.md` or
`tasks/draft/<feature-slug>-backend.md`.

## Handoff Workflow

1. Confirm readiness and target.
   - Identify whether the source plan is approved, draft, or ambiguous.
   - Read `orchestration_mode` and obtain `execution_target=current_session`
     or `execution_target=subagent`. If either decision is missing, return the
     decision needed and stop.
   - When the target is `subagent`, obtain
     `execution_backend=codex_subagent` or `execution_backend=zcode_mcp`.
     A current-session handoff leaves `execution_backend` unset or empty; never
     infer a backend from the word subagent.
   - If approval is ambiguous, write draft tasks only; do not place tasks in `ready`.
   - If a `parallel_dag` task depends on another task that is not already done,
     accepted, merged, or explicitly satisfied, do not place it in `ready`;
     mark it `blocked` or keep it in draft.
   - If the implementation plan is missing or too vague, hand off to plan mode.

2. Route the target.
   - For `current_session`, hand the approved plan directly to `$implement-plan`
     and record that no subagent packet was created.
   - For `subagent` + `batch`, create exactly one whole-goal task packet.
   - For `subagent` + `parallel_dag`, select runnable nodes from the source
     DAG. Preserve DAG unit IDs and dependencies; group tightly coupled nodes
     only when the mapping does not change dependency semantics.
   - Dispatch each subagent packet through the selected backend adapter. If
     the adapter runtime is unavailable, leave the handoff blocked rather than
     claiming that dispatch occurred.
   - Keep shared contracts, schemas, migrations, generated artifacts, and
     cross-cutting config under a single writer.
   - If mapping would change the source DAG shape or acceptance semantics, hand
     back to plan mode.

3. Define dependency and parallelism rules.
   - For `batch`, record `Depends On: None`, `Can Run In Parallel With: None`,
     and the serial writer rule; do not invent node dependencies.
   - For `parallel_dag`, reuse the source DAG before writing task files.
   - List `Depends On`, `Unblocks`, and parallel-safe peers for every task.
   - List `Must Not Run In Parallel With` for shared files, public contracts,
     database migrations, generated artifacts, or unclear boundaries.
   - Assign a `parallel_group` and `mutex` values when multiple tasks belong to
     the same approved plan. Record the low-level `parallel_mode` for each
     task.

4. Define write ownership.
   - Specify allowed paths, modules, APIs, config, tests, and docs.
   - Specify forbidden writes for shared contracts, unrelated modules, migrations, lockfiles, generated artifacts, or files owned by another task.
   - If write ownership cannot be made clear, keep the task serial and mark the risk.

5. Define branch and worktree isolation after impact analysis.
   - A current-session target does not need a subagent branch or worktree.
   - Read-only parallel tasks do not need a branch or worktree.
   - Serial tasks with disjoint ownership may reuse the current checkout; the orchestrator must serialize writes.
   - Assign one branch and one git worktree per task only when tasks must write simultaneously, such as `task/<remote-task-id>` and `.worktrees/<remote-task-id>`.
   - Do not allow two write agents to run concurrently in the same working tree or on the same branch.
   - Shared contract, schema, migration, generated artifact, dependency manifest, and lockfile tasks should be serial unless the plan explicitly assigns single-writer ownership.

6. Write the subagent task packet when the target is `subagent`.
   - Include source artifacts, objective, whole-goal or node scope, exclusions,
     required context, implementation instructions, verification, acceptance
     criteria, blocking conditions, and feedback format.
   - Include branch and PR expectations when known.
   - When the target uses agent-brain, create or update its Task Pack from this packet; do not make the remote Markdown acceptance list a second source of truth.
   - Keep instructions concrete enough for `$implement-plan` to start without
     further discovery beyond reading the referenced files.
   - For a `batch` packet, require one active goal covering the complete plan;
     internal steps and checks must not trigger parent-agent interaction.

7. Define execution feedback and waiting.
   - Require the subagent to report changed files, tests run, result, deviations,
     blockers, attempt number, and PR or commit reference.
   - Require the subagent to return only after the whole `batch` goal or
     assigned DAG node has reached an explicit `completed`, `blocked`, or
     `failed` state, unless a human decision is required.
   - The coordinating agent must use the runtime's bounded wait mechanism when
     available, avoid repeated polling or unchanged-context reads, and not
     start acceptance until the subagent explicitly returns `completed`.
     `blocked` and `failed` are terminal reports for repair or escalation, not
     acceptance passes.
   - Require blockers to preserve current branch state and explain the missing
     decision or failing check.

8. Define the repair limit.
   - If final batch acceptance or DAG integration acceptance fails, the
     coordinating agent creates one repair packet containing all known findings,
     failed checks, expected corrections, and the same overall acceptance.
   - Retry the same goal at most once. Do not send piecemeal repair prompts.
   - If the second attempt fails or remains blocked, stop automation and return
     the evidence and choices to the user.

9. Finish with routing.
   - If tasks are draft, state what approval is needed before moving them to ready.
   - If tasks are blocked by dependencies, state which upstream task or merge must complete first.
   - If tasks are ready, state the recommended claim or execution order.
   - State the promotion rule for downstream tasks, for example "after `task/api-contract` is accepted, promote `task/backend` and `task/frontend` to ready."
   - State any mapping from execution plan units to remote tasks.
   - If `execution_target=current_session`, hand off to `$implement-plan`.
     Otherwise leave the subagent task ready for pickup.

## Task Packet Format

Use this structure unless the user provides a stricter format:

```markdown
---
id: <remote-task-id>
type: remote_task
status: draft
created_at: <date>
updated_at: <date>
orchestration_mode: batch | parallel_dag
execution_target: subagent
execution_backend: codex_subagent | zcode_mcp
acceptance_scope: batch | node_and_batch
attempt_policy:
  max_attempts: 2
  repair: consolidated_repair_packet
  escalate_after_exhaustion: user_decision
sources:
  - <source artifact path or issue>
related:
  prd: <path>
  trd: <path>
  execution_plan: <path>
plan_unit_id: <root for batch, or execution-plan-unit-id for parallel_dag>
plan_id: <stable execution plan id>
source_plan_sha256: <sha256 of the canonical execution plan>
base_commit: <commit from which the task must start>
task_id: <outer Task Pack or issue id>
feature: <feature-id>
phase: <contract|backend|frontend|integration|cleanup>
depends_on: []
unblocks: []
parallel_group: <group-id>
required_capabilities:
  - <capability required by the source plan node>
required_skills:
  - <skill name required by the source plan node>
source_artifacts:
  - <PRD/TRD/execution plan/Task Pack path>
source_hash: <sha256 of the canonical source artifact or Task Pack>
source_task_pack_sha256: <sha256 of the canonical Task Pack, or "not applicable">
acceptance_ids:
  - <canonical acceptance id>
evidence_required:
  - <acceptance.json, test report, scope result, or manual acknowledgement>
mutex: []
parallel_mode: <read_only_parallel|serial_same_worktree|concurrent_write_worktree|serial_shared_writer>
branch: <required only for concurrent_write_worktree>
worktree: <required only for concurrent_write_worktree>
write_ownership:
  - <allowed path or module>
forbidden_writes:
  - <forbidden path or module>
---

# Subagent Task: <Title>

## Objective

<One concrete implementation outcome.>

## Scope

- <In-scope work>

## Exclusions

- <Out-of-scope work>

## Required Context

- <Files, docs, issues, or commands to inspect first>

## Required Capabilities And Skills

- Capabilities: <tool access, domain knowledge, or execution ability>
- Skills: <skill names or "None">

## Dependencies And Parallelism

- Orchestration mode: <batch|parallel_dag>
- Execution target: `subagent`
- Execution backend: `codex_subagent` | `zcode_mcp`
- Acceptance scope: <batch|node_and_batch>
- Plan unit: <root for batch, or execution-plan-unit-id for parallel_dag>
- Feature: <feature-id>
- Phase: <phase>
- Depends on: <tasks or "None">
- Unblocks: <tasks or "None">
- Can run in parallel with: <tasks or "None">
- Must not run in parallel with: <tasks or "None">
- Mutex: <shared resources or "None">

## Branch And Worktree

- Parallel mode: <read_only_parallel|serial_same_worktree|concurrent_write_worktree|serial_shared_writer>
- Branch: `<branch or None>`
- Worktree: `<worktree or None>`
- Concurrency rule: read-only tasks may share a checkout; serial-write tasks may reuse a checkout only under orchestration; simultaneous write tasks require separate branch/worktree.

## Write Ownership

- Allowed writes: <paths/modules>
- Forbidden writes: <paths/modules>

## Execution Steps

For `batch`, execute the complete approved plan in this one goal. Internal
steps may be sequential, but must not trigger parent-agent interaction.

1. <Step>
2. <Step>

## Verification

- `<command>`: <expected result>

## Acceptance Criteria

- <Observable pass/fail condition>

For `batch`, these are the complete-goal acceptance conditions. For
`parallel_dag`, these are the assigned node conditions; the coordinating actor
also performs final integration acceptance.

## Task Contract Bridge

- If agent-brain is used, the Task Pack is the outer contract and its `acceptance` list is canonical.
- Copy this packet's `orchestration_mode`, `execution_target`,
  `execution_backend`, `plan_id`, `source_plan_sha256`, `base_commit`, `task_id`,
  `source_artifacts`,
  `source_hash`, `source_task_pack_sha256`, `acceptance_ids`,
  `required_skills`, and `plan_unit_id` into the Task Pack linkage fields.
- Generate the compatibility Acceptance Pack from the Task Pack and retain its source hash; do not edit acceptance checks independently on the remote side.
- Evidence must identify a path, overall status, exit codes, git head, changed files, and source hashes; manual checks must record explicit acknowledgement.
- Done requires passing acceptance evidence plus a clean scope check. A text claim that tests passed is not evidence.

## Blocking Conditions

- <When remote Codex should stop and report back>

## Delivery And Feedback

- Changed files:
- Tests run:
- Result: `completed` | `blocked` | `failed`
- Attempt: `1` | `2`
- Deviations:
- Blockers:
- PR/commit:
```

## Output Format

Answer in the user's language unless they request otherwise. Prefer:

```markdown
## Execution Handoff

- orchestration_mode: `batch` | `parallel_dag`
- execution_target: `current_session` | `subagent`
- execution_backend: `codex_subagent` | `zcode_mcp`
- approval: `<pending|approved>`

If `execution_target=current_session`, report the direct `$implement-plan`
handoff and do not create a remote task table. If `execution_target=subagent`,
use the table below.

## Prepared Subagent Tasks

| Task | Status | Path/Issue | Depends On | Parallel Group |
|---|---|---|---|---|
| <task> | <draft/ready> | <path or issue> | <deps> | <group> |

## Execution Order

<For batch: one whole-goal task. For parallel_dag: claim order, merge order,
and parallel-safe groups.>

## Approval Needed

<Execution target, plan approval, or downstream dependency confirmation; or
"None".>

## Notes

<Residual risks, shared-write warnings, or missing context.>
```

For a batch target, the table contains one whole-goal task and one final
acceptance scope. For a parallel DAG, state node dependencies, node acceptance,
and final integration acceptance. For one small task, compress the table but
still state status, path or issue, dependencies, and approval state.
