---
name: prepare-remote
description: Prepare approved implementation plans, DAG nodes, or settled task scopes for remote Codex execution by creating bounded handoff task packets. Use when the user wants to delegate work to another machine, remote Codex instance, GitHub Issue, task file, or parallel implementation worker after PRD/TRD/execution planning is complete. Focus on source artifact links, scope, exclusions, dependencies, write ownership, verification commands, acceptance criteria, blocking conditions, and feedback format without implementing code.
---

# Prepare Remote

Use this skill to convert an approved execution plan or settled implementation node into one or more remote execution task packets. The output should be narrow enough that a remote Codex can execute it without redoing product discovery or expanding scope.

## Core Principles

- Treat the handoff packet as the contract between planning and execution.
- Preserve traceability to PRD, TRD, execution plan, issues, decisions, and code context.
- Keep every remote task bounded by scope, exclusions, write ownership, verification, and acceptance criteria.
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
- DAG nodes, dependencies, critical path, risk-first nodes, and shared-write nodes.
- Modules, files, APIs, schemas, migrations, generated artifacts, and config that each task may touch.
- Verification commands, manual checks, fixtures, logs, or PR review gates.
- Target repo, target branch, branch naming, PR expectations, and feedback format.

## Feature Task Groups

When multiple tasks belong to the same requirement or feature:

- Assign the same `parallel_group` and a stable `feature` value to all tasks.
- Assign a `phase` that reflects the DAG layer, such as `contract`, `backend`, `frontend`, `integration`, or `cleanup`.
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

Before producing handoff tasks, check the current working directory for `.dev-skills/config.toml`.

Document artifact mode is enabled only when that file exists and contains:

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
- Include frontmatter with at least `id`, `type: remote_task`, `status`, `created_at`, `updated_at`, `sources`, `related`, `feature`, `phase`, `depends_on`, `unblocks`, `parallel_group`, `write_ownership`, `forbidden_writes`, `mutex`, `branch`, and `worktree`.
- Keep the final chat response to created or updated file paths, statuses, and concise summary.
- If a required file cannot be written while the mode is enabled, report the blocker instead of falling back to chat-only output.

## Handoff Workflow

1. Confirm readiness.
   - Identify whether the source plan is approved, draft, or ambiguous.
   - If approval is ambiguous, write draft tasks only; do not place tasks in `ready`.
   - If a task depends on another task that is not already done, accepted, merged, or explicitly satisfied, do not place it in `ready`; mark it `blocked` or keep it in draft.
   - If the implementation plan is missing or too vague, hand off to `write-execution-plan`.

2. Select remote task units.
   - Start from execution plan DAG nodes.
   - Group tightly coupled nodes into one task when separating them would create coordination overhead.
   - Split independent nodes when each can be verified and reviewed separately.
   - Keep shared contracts, schemas, migrations, generated artifacts, and cross-cutting config under a single writer.

3. Define dependency and parallelism rules.
   - Build the feature group DAG before writing task files.
   - List `Depends On` for every task.
   - List `Unblocks` for tasks that enable downstream work.
   - List `Can Run In Parallel With` only when write ownership does not overlap.
   - List `Must Not Run In Parallel With` for shared files, public contracts, database migrations, generated artifacts, or unclear boundaries.
   - Assign a `parallel_group` when multiple tasks belong to the same approved plan.
   - Define `mutex` values for shared resources that must not be edited concurrently, such as `api-schema`, `db-migration`, `generated-types`, `package-lock`, or a concrete path glob.

4. Define write ownership.
   - Specify allowed paths, modules, APIs, config, tests, and docs.
   - Specify forbidden writes for shared contracts, unrelated modules, migrations, lockfiles, generated artifacts, or files owned by another task.
   - If write ownership cannot be made clear, keep the task serial and mark the risk.

5. Define branch and worktree isolation.
   - Assign one branch per remote task, such as `task/<remote-task-id>`.
   - Recommend one git worktree per task when tasks may run concurrently, such as `.worktrees/<remote-task-id>`.
   - Do not allow two tasks to run concurrently in the same working tree or on the same branch.
   - Shared contract, schema, migration, generated artifact, dependency manifest, and lockfile tasks should be serial unless the plan explicitly assigns single-writer ownership.

6. Write the task packet.
   - Include source artifacts, objective, scope, exclusions, required context, implementation instructions, verification, acceptance criteria, blocking conditions, and feedback format.
   - Include branch and PR expectations when known.
   - Keep instructions concrete enough for `implement-plan` to start without further discovery beyond reading the referenced files.

7. Define execution feedback.
   - Require remote Codex to report changed files, tests run, result, deviations, blockers, and PR or commit reference.
   - Require blockers to preserve current branch state and explain the missing decision or failing check.

8. Finish with routing.
   - If tasks are draft, state what approval is needed before moving them to ready.
   - If tasks are blocked by dependencies, state which upstream task or merge must complete first.
   - If tasks are ready, state the recommended claim or execution order.
   - State the promotion rule for downstream tasks, for example "after `task/api-contract` is accepted, promote `task/backend` and `task/frontend` to ready."
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
feature: <feature-id>
phase: <contract|backend|frontend|integration|cleanup>
depends_on: []
unblocks: []
parallel_group: <group-id>
mutex: []
branch: task/<remote-task-id>
worktree: .worktrees/<remote-task-id>
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

## Dependencies And Parallelism

- Feature: <feature-id>
- Phase: <phase>
- Depends on: <tasks or "None">
- Unblocks: <tasks or "None">
- Can run in parallel with: <tasks or "None">
- Must not run in parallel with: <tasks or "None">
- Mutex: <shared resources or "None">

## Branch And Worktree

- Branch: `task/<remote-task-id>`
- Worktree: `.worktrees/<remote-task-id>`
- Concurrency rule: do not execute this task in the same worktree or branch as another active task.

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
