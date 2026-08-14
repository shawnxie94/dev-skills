---
name: prepare-remote
description: Prepare approved implementation plans, DAG nodes, or settled task scopes for delegated execution by creating bounded handoff task packets. Use when the user wants to delegate work to another machine, remote Codex instance, managed-agent issue, squad child issue, GitHub Issue, task file, or parallel implementation worker after PRD/TRD/execution planning is complete, or uses Chinese requests such as 远端交接, 远程任务, 委派任务, 任务包. Focus on source artifact links, scope, exclusions, dependencies, required skills, write ownership, verification commands, acceptance criteria, blocking conditions, and feedback format without implementing code.
---

# Prepare Remote

Use this skill to convert an approved execution plan or settled implementation node into one or more delegated execution task packets. The target may be a remote Codex, managed-agent issue, squad child issue, GitHub Issue, or workspace task file. The output should be narrow enough that the assigned actor can execute it without redoing product discovery or expanding scope.

## Core Principles

- Treat the handoff packet as the contract between planning and execution.
- Preserve traceability to PRD, TRD, execution plan, issues, decisions, and code context.
- Reuse the `write-execution-plan` DAG as the source of truth; do not create a second independent DAG.
- Keep every remote task bounded by scope, exclusions, write ownership, verification, and acceptance criteria.
- Preserve required capabilities and required skills from the source execution-plan node when the target platform supports them.
- Preserve the outer task contract: `plan_id`, `source_plan_sha256`, `base_commit`, `task_id`, `source_artifacts`, `source_hash`, `source_task_pack_sha256`, `acceptance_ids`, and `evidence_required`.
- Split parallel tasks only when dependencies and write boundaries are clear.
- Put only currently executable tasks in `ready`; tasks with unmet dependencies must stay draft or blocked.
- Model multiple tasks from the same requirement as one feature task group with a DAG, not as unrelated ready tasks.
- Do not implement code or redesign the feature; if the plan is unclear, hand back to `write-execution-plan` or `change-impact-analysis`.
- Do not mark a task ready for remote execution unless the user or source artifact clearly indicates approval.

## Inputs to Look For

Use the execution plan, TRD, PRD, issue context, codebase orientation, implementation DAG, user approval, target repository, branch policy, test commands, and existing task files when available.

Extract:

- Source artifacts and their file paths.
- Approved scope and explicit non-goals.
- Execution plan DAG nodes, dependencies, critical path, risk-first nodes, shared-write nodes, and remote handoff inputs.
- Required capabilities and required skills for each execution-plan node.
- Task Pack linkage and canonical acceptance ids for each execution-plan node.
- Plan hash, Task Pack hash, Acceptance Pack path/hash, and baseline commit when available.
- Modules, files, APIs, schemas, migrations, generated artifacts, and config that each task may touch.
- Verification commands, manual checks, fixtures, logs, or PR review gates.
- Target repo, target branch, branch naming, PR expectations, and feedback format.

## Feature Task Groups

When multiple tasks belong to the same requirement or feature:

- Start from the source execution plan DAG. If the DAG is missing, stale, or ambiguous, hand back to `write-execution-plan` instead of inventing a new one.
- Assign the same `parallel_group` and a stable `feature` value to all tasks.
- Assign a `phase` that reflects the DAG layer, such as `contract`, `backend`, `frontend`, `integration`, or `cleanup`.
- Preserve the execution plan unit IDs in each task packet with `plan_unit_id`.
- Put only root nodes with no unmet dependencies in `ready`.
- Put approved downstream nodes in `blocked` until their dependencies are accepted or merged.
- Add `unblocks` to each task when completing it can make downstream tasks runnable.
- Prefer a contract-first split when possible:

```text
contract/schema/API task
  -> backend task
  -> integration task

contract/schema/API task
  -> frontend task
  -> integration task
```

Do not use stacked branches by default. Prefer merging or accepting the dependency task, then creating or rebasing downstream task branches from the updated base branch.

## Document Artifact Mode

Before producing handoff tasks, check `.agent/config.toml`. If it exists, use
its `[document_artifacts]` section; only when it does not exist should a
standalone dev-skills workspace fall back to `.dev-skills/config.toml`.

Document artifact mode is enabled when the first available config contains:

```toml
[document_artifacts]
enabled = true
```

When document artifact mode is disabled or the config is absent, keep the normal chat-output behavior.

When document artifact mode is enabled:

- Create or update remote handoff task files instead of only writing them in chat.
- Use `tasks/draft/` by default, or `document_artifacts.paths.task_draft` when configured.
- Use `tasks/ready/` only when the task is explicitly approved for remote execution, or `document_artifacts.paths.task_ready` when configured.
- Use `tasks/blocked/` for approved but dependency-blocked tasks when `document_artifacts.paths.task_blocked` is configured or the default directory exists; otherwise keep them in draft with `status: blocked`.
- Use stable, descriptive filenames such as `tasks/draft/<feature-slug>-backend.md`.
- Include frontmatter with at least `id`, `type: remote_task`, `status`, `created_at`, `updated_at`, `sources`, `related`, `plan_id`, `plan_unit_id`, `source_plan_sha256`, `base_commit`, `task_id`, `source_artifacts`, `source_hash`, `source_task_pack_sha256`, `acceptance_ids`, `evidence_required`, `feature`, `phase`, `depends_on`, `unblocks`, `parallel_group`, `parallel_mode`, `required_capabilities`, `required_skills`, `write_ownership`, `forbidden_writes`, `mutex`, `branch`, and `worktree`.
- Keep the final chat response to created or updated file paths, statuses, and concise summary.
- If a required file cannot be written while the mode is enabled, report the blocker instead of falling back to chat-only output.

## Handoff Workflow

1. Confirm readiness.
   - Identify whether the source plan is approved, draft, or ambiguous.
   - If approval is ambiguous, write draft tasks only; do not place tasks in `ready`.
   - If a task depends on another task that is not already done, accepted, merged, or explicitly satisfied, do not place it in `ready`; mark it `blocked` or keep it in draft.
   - If the implementation plan is missing or too vague, hand off to `write-execution-plan`.

2. Select remote task units.
   - Start from execution plan DAG nodes and `Remote Handoff Inputs`.
   - Preserve DAG unit IDs and dependencies when mapping units to remote tasks.
   - Group tightly coupled nodes into one task when separating them would create coordination overhead.
   - Split independent nodes when each can be verified and reviewed separately.
   - Keep shared contracts, schemas, migrations, generated artifacts, and cross-cutting config under a single writer.
   - If grouping or splitting changes the source DAG shape, record the mapping and reason; if the change alters dependencies, hand back to `write-execution-plan`.

3. Define dependency and parallelism rules.
   - Reuse the source execution plan DAG before writing task files.
   - List `Depends On` for every task.
   - List `Unblocks` for tasks that enable downstream work.
   - List `Can Run In Parallel With` only when write ownership does not overlap.
   - List `Must Not Run In Parallel With` for shared files, public contracts, database migrations, generated artifacts, or unclear boundaries.
   - Assign a `parallel_group` when multiple tasks belong to the same approved plan.
   - Define `mutex` values for shared resources that must not be edited concurrently, such as `api-schema`, `db-migration`, `generated-types`, `package-lock`, or a concrete path glob.
   - Record the impact decision for each task: `read_only_parallel`, `serial_same_worktree`, `concurrent_write_worktree`, or `serial_shared_writer`.

4. Define write ownership.
   - Specify allowed paths, modules, APIs, config, tests, and docs.
   - Specify forbidden writes for shared contracts, unrelated modules, migrations, lockfiles, generated artifacts, or files owned by another task.
   - If write ownership cannot be made clear, keep the task serial and mark the risk.

5. Define branch and worktree isolation after impact analysis.
   - Read-only parallel tasks do not need a branch or worktree.
   - Serial tasks with disjoint ownership may reuse the current checkout; the orchestrator must serialize writes.
   - Assign one branch and one git worktree per task only when tasks must write simultaneously, such as `task/<remote-task-id>` and `.worktrees/<remote-task-id>`.
   - Do not allow two write agents to run concurrently in the same working tree or on the same branch.
   - Shared contract, schema, migration, generated artifact, dependency manifest, and lockfile tasks should be serial unless the plan explicitly assigns single-writer ownership.

6. Write the task packet.
   - Include source artifacts, objective, scope, exclusions, required context, implementation instructions, verification, acceptance criteria, blocking conditions, and feedback format.
- Include branch and PR expectations when known.
- When the target uses agent-brain, create or update its Task Pack from this packet; do not make the remote Markdown acceptance list a second source of truth.
   - Keep instructions concrete enough for `implement-plan` to start without further discovery beyond reading the referenced files.

7. Define execution feedback.
   - Require remote Codex to report changed files, tests run, result, deviations, blockers, and PR or commit reference.
   - Require blockers to preserve current branch state and explain the missing decision or failing check.

8. Finish with routing.
   - If tasks are draft, state what approval is needed before moving them to ready.
   - If tasks are blocked by dependencies, state which upstream task or merge must complete first.
   - If tasks are ready, state the recommended claim or execution order.
   - State the promotion rule for downstream tasks, for example "after `task/api-contract` is accepted, promote `task/backend` and `task/frontend` to ready."
   - State any mapping from execution plan units to remote tasks.
   - If implementation should begin on the current machine, hand off to `implement-plan`; otherwise leave the task ready for remote pickup.

## Task Packet Format

Use this structure unless the user provides a stricter format:

```markdown
---
id: <remote-task-id>
type: remote_task
status: draft
created_at: <date>
updated_at: <date>
sources:
  - <source artifact path or issue>
related:
  prd: <path>
  trd: <path>
  execution_plan: <path>
plan_unit_id: <execution-plan-unit-id>
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

# Remote Task: <Title>

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

- Plan unit: <execution-plan-unit-id>
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

1. <Step>
2. <Step>

## Verification

- `<command>`: <expected result>

## Acceptance Criteria

- <Observable pass/fail condition>

## Task Contract Bridge

- If agent-brain is used, the Task Pack is the outer contract and its `acceptance` list is canonical.
- Copy this packet's `plan_id`, `source_plan_sha256`, `base_commit`, `task_id`, `source_artifacts`, `source_hash`, `source_task_pack_sha256`, `acceptance_ids`, `required_skills`, and `plan_unit_id` into the Task Pack linkage fields.
- Generate the compatibility Acceptance Pack from the Task Pack and retain its source hash; do not edit acceptance checks independently on the remote side.
- Evidence must identify a path, overall status, exit codes, git head, changed files, and source hashes; manual checks must record explicit acknowledgement.
- Done requires passing acceptance evidence plus a clean scope check. A text claim that tests passed is not evidence.

## Blocking Conditions

- <When remote Codex should stop and report back>

## Delivery And Feedback

- Changed files:
- Tests run:
- Result:
- Deviations:
- Blockers:
- PR/commit:
```

## Output Format

Answer in the user's language unless they request otherwise. Prefer:

```markdown
## Prepared Remote Tasks

| Task | Status | Path/Issue | Depends On | Parallel Group |
|---|---|---|---|---|
| <task> | <draft/ready> | <path or issue> | <deps> | <group> |

## Execution Order

<Claim order, merge order, and parallel-safe groups.>

## Approval Needed

<What must be confirmed before draft tasks become ready, or "None".>

## Notes

<Residual risks, shared-write warnings, or missing context.>
```

For one small task, compress the table but still state status, path or issue, dependencies, and approval state.
