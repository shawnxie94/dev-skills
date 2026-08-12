---
name: implement-plan
description: Implement an approved execution plan or remote handoff task one verified step at a time. Use when the user asks to implement, execute, carry out, or continue from a write-execution-plan output, implementation DAG, task plan, subagent plan, or tasks/ready remote task packet, or uses Chinese requests such as 按计划实现, 开始落地, 实现任务包, 继续实现. When invoked in a repository without an explicit plan, check the workspace ready-task directory, resolve dependencies and write conflicts, and execute only runnable tasks. Focus on verification-first development, TDD/regression/characterization test selection, scoped edits, task write-ownership enforcement, branch/worktree isolation for concurrent tasks, node-level validation, integration validation, progress updates, and final handoff to prepare-commit.
---

# Implement Plan

Use this skill to execute an approved implementation plan without drifting from scope. The goal is to move through the plan in small, verified steps.

## Core Principles

- Follow the plan, but revise it when new evidence invalidates it.
- Implement one phase or DAG node at a time.
- Choose a behavior protection mode before editing.
- Keep edits scoped to the current node.
- Validate after each meaningful step, not only at the end.
- Treat subagent output as candidate work that the main agent must review, merge, and verify.
- Scaffolded code is not implemented. Distinguish "scaffolded" from "verified" in every completion claim and name the end-to-end chain that was actually exercised.
- Enforce remote task `write_ownership`, `forbidden_writes`, dependencies, verification, and feedback requirements when present.
- When agent-brain is present, treat its Task Pack as the outer contract and the selected dev-skill as the inner execution capability.
- Never run multiple coding tasks concurrently in the same worktree or on the same branch.
- Use `prepare-commit` as the final quality gate, not as a substitute for node-level validation.

## Mandatory Plan Preflight

Before reading a ready task as runnable or editing any file, require an approved canonical execution plan for every implementation-bound task. The plan may be supplied directly by the user, by `write-execution-plan`, or by a remote task packet, but it must be a file on disk rather than chat-only prose.

For an agent-brain Task Pack, verify all of these values before Build:

1. `source_artifacts` contains the canonical execution-plan file (not only PRD/TRD files).
2. The file exists and its current `shasum -a 256` equals `source_plan_sha256`.
3. `plan_id`, `plan_unit_id`, and `base_commit` match the plan and the assigned unit.
4. The plan status is `approved`, or the user explicitly approved it in the current turn.
5. The Task Pack's `allowed_paths`, acceptance checks, and write ownership are a bounded subset of the plan unit.

If any preflight check fails, do not create files, do not infer missing hashes, and do not begin implementation. Report the exact missing or mismatched field and hand off to `write-execution-plan` or `agent-brain` task mode to repair the contract. A generic YAML pass is not sufficient: the linkage and artifact freshness checks are mandatory.

## Managed Task Boundary

When a managed-agent platform, squad child issue, concrete GitHub Issue, task packet, or implementation DAG node is already assigned, treat it as the current-node context:

- Execute only that assigned node and its explicit verification contract.
- Do not scan for, claim, promote, or execute sibling ready tasks.
- Do not recursively delegate work unless the assignment explicitly grants orchestration responsibility.
- Respect the platform's scope, dependencies, required skills, write ownership, forbidden writes, status, and feedback format.
- Report newly discovered dependencies or scope gaps to the external orchestrator instead of expanding the node unilaterally.

Use Remote Task Bootstrap only when no explicit assigned plan, issue, task packet, or current-node context exists.

## Remote Task Bootstrap

When this skill is invoked in a repository without an explicit plan, assigned managed-platform issue, task path, or current-node context:

1. Check the current working directory for `.dev-skills/config.toml`.
   - If `document_artifacts.paths.task_ready` is configured, use that as the ready-task directory.
   - Otherwise use `tasks/ready/`.
2. Look for ready remote task packets in that directory.
   - If exactly one task exists, read it and treat it as the source plan.
   - If multiple ready tasks exist, read all of them, resolve dependencies, detect write conflicts, and build a runnable set before deciding execution.
   - If no ready task exists, continue normal input confirmation and ask for a plan or task.
3. Resolve dependencies.
   - Treat `parallel_group` and `feature` as the task group boundary for one requirement or feature.
   - A task is runnable only when every `depends_on` item is already accepted, merged, or explicitly marked satisfied.
   - Treat `done` as "implementation branch completed", not as dependency satisfaction, unless the task or repo policy explicitly says done is integrated.
   - If a dependency is not present locally and is not explicitly marked satisfied, treat it as unresolved.
   - If a `ready` task has unmet dependencies, do not execute it; report that it should be moved back to draft/blocked or wait for the dependency.
4. Detect conflicts and mutual exclusion.
   - Treat overlapping `write_ownership` entries as a conflict unless the plan explicitly assigns non-overlapping subpaths.
   - Treat matching `mutex` values as a conflict.
   - Treat public contracts, schemas, migrations, generated artifacts, dependency manifests, lockfiles, and shared config as serial unless single-writer ownership is explicit.
5. Analyze impact and choose execution mode.
   - Classify each task as read-only, serial-write, or concurrent-write before creating branches or worktrees.
   - Trace direct and indirect impact: callers, shared contracts, generated artifacts, test fixtures, config, lockfiles, and runtime state; path disjointness alone is insufficient.
   - Read-only analysis may run in parallel in the same checkout when no task writes files.
   - Independent code tasks may reuse one checkout only when the orchestrator serializes their writes; never let two agents write the same checkout simultaneously.
   - Require a dedicated branch and worktree only for genuinely simultaneous write tasks, or when the impact analysis cannot prove safe serialization.
   - If exactly one runnable task remains, execute it in the current worktree only if the worktree is clean and the branch matches the task or can be safely created.
   - If multiple runnable tasks remain and subagents are available, use read-only parallelism or isolated worktrees according to the impact result.
   - If separate worktrees are unavailable, keep code writes serial; read-only analysis can still run in parallel.
   - If multiple runnable tasks conflict, execute them serially in dependency or merge order.
6. Before editing code, validate each selected task packet.
   - Require status to be `ready` or clearly approved for execution.
   - Read all `Required Context`, `sources`, and `related` artifacts that exist.
   - Confirm the assigned actor has the task's `required_capabilities` and `required_skills`; otherwise report the mismatch instead of silently omitting the required workflow.
   - Respect `depends_on`; if an unmet dependency is obvious, stop and report the blocker.
   - Treat `write_ownership` as the allowed edit scope and `forbidden_writes` as hard exclusions unless the user explicitly overrides them.
   - Use the task packet's branch/worktree fields when present.
7. Use the task packet's `Verification`, `Acceptance Criteria`, `Blocking Conditions`, and `Delivery And Feedback` sections as the implementation contract.

### Agent-brain Contract Bridge

When the current task has an agent-brain run directory or Task Pack:

1. Validate the Task Pack strictly before editing; require non-empty `allowed_paths` and at least one acceptance check.
2. Run the Mandatory Plan Preflight. A Task Pack with `plan_unit_id` but missing or stale `plan_id` / `source_plan_sha256` / `base_commit` is blocked even if `validate-task-pack` returns OK.
3. Confirm `required_skills` includes the skills needed by this node and that `plan_unit_id` / `task_id` match the assigned handoff.
4. Treat Task Pack `acceptance` as canonical. The generated Acceptance Pack must carry the matching source hash.
5. Run acceptance and scope checks through the brain scripts. Manual checks are `pending` until explicitly acknowledged.
6. Report Done only when machine evidence says `overall: pass` (or the user explicitly owns a residual-risk skip); do not convert a host goal or prose summary into Done.
7. Before starting parallel work, verify normalized write ownership, mutex, branch, worktree, and base commit; overlapping or unisolated writes are serial blockers, while read-only tasks do not require worktrees.

## Parallelism And Worktree Decision

Use this decision order:

1. Satisfy dependencies and run impact analysis.
2. If every selected actor is read-only, run them in parallel in the same checkout.
3. If actors write files but execution can be serialized and write ownership is disjoint, reuse one checkout serially.
4. If actors must write simultaneously, require non-overlapping ownership, non-overlapping mutexes, dedicated branches, and dedicated worktrees.
5. If impact is unclear or shared state is involved, keep the work serial and assign one writer.

For every mode, each actor receives only its task packet, required context, exclusions, verification commands, and expected feedback format.

Recommended isolation pattern:

```text
main worktree
  -> read-only analysis in parallel
  -> serial code writes when impact is low and ownership is disjoint

.worktrees/<task-a>
  -> branch task/<task-a>

.worktrees/<task-b>
  -> branch task/<task-b>
```

Do not let two agents edit the same checkout simultaneously. Merge isolated results through PRs or serial review in dependency order. After a dependency task merges, rebase or recreate dependent task worktrees before continuing.

## Task Group Progression

For multiple tasks from the same requirement:

- Use `parallel_group` or `feature` to identify the group.
- Keep only currently runnable tasks in `tasks/ready/`.
- Keep approved but dependency-blocked tasks in `tasks/blocked/` when available, otherwise keep them in draft with `status: blocked`.
- Do not execute blocked tasks even if they are part of the same feature group.
- After a task finishes implementation, mark it `done` or report it as done, but do not automatically satisfy dependencies unless the task is accepted, merged, or explicitly approved as satisfying its dependents.
- After a dependency is accepted or merged, scan blocked tasks in the same feature group:
  - Promote tasks whose `depends_on` entries are all satisfied.
  - Keep tasks blocked when any dependency remains unresolved.
  - Run conflict and mutex checks again before executing newly promoted tasks.
- When downstream tasks depend on upstream code, prefer creating or rebasing their worktrees from the updated base branch after the upstream merge. Avoid stacked branches unless the task packet explicitly requires them.
- Use a final integration task when multiple branches complete one feature; it should verify the merged result rather than add broad new scope.

## Long-Running Work

For large implementations, prefer running under an explicit user goal so progress and completion state remain stable across long work:

- If the user already started a `/goal`, use the execution plan as the goal blueprint.
- If the task spans multiple modules, long validation loops, or subagent work, recommend using `/goal` before starting.
- Do not make small changes heavy by forcing goal tracking.

## Behavior Protection Modes

Before implementation, choose the lightest protection mode that fits the task:

- TDD: for new behavior that can be specified before implementation.
- Regression test: for bug fixes after reproduction.
- Characterization test: for refactors or legacy behavior that must be preserved.
- Existing coverage: when relevant tests already protect the behavior.
- Manual verification: for UI, external dependency, or hard-to-automate paths.

If no test is practical, state the manual verification path and residual risk before editing.

## Implementation Workflow

1. Confirm inputs.
   - Identify the source plan, current node, scope, expected behavior, verification mode, and done criteria.
   - If no explicit input is provided, run the remote task bootstrap before asking for more context.
   - If no approved canonical plan exists, stop and route to `write-execution-plan`; “trivial” applies only to a single-file, already-specified change with no Task Pack plan unit.

2. Prepare verification.
   - Write or identify the focused test/check/manual validation for the node.
   - For TDD or regression work, prefer seeing the test fail before implementing when practical.

3. Implement the node.
   - Read relevant files before editing.
   - Keep changes local to the current node.
   - Avoid opportunistic feature work or unrelated refactors.

4. Validate the node.
   - Run the node's smallest relevant verification.
   - Fix failures caused by the node before moving on.
   - Record commands and outcomes.

5. Merge subagent output when applicable.
   - When the execution plan includes subagent plans and subagent tools are available, the main agent may launch subagents for the approved current node.
   - Pass only the scoped inputs, exclusions, expected output format, and acceptance criteria from the plan.
   - Do not leak expected answers, hidden assumptions, or unrelated repository context into subagent prompts.
   - Inspect the subagent's scope, claims, and artifacts before applying them.
   - Avoid merging conflicting edits to shared files, public contracts, schemas, migrations, or generated artifacts without explicit ownership.
   - After merging, immediately run the relevant node-level verification.

6. Integrate.
   - After a set of related nodes is complete, run the integration check defined by the plan.
   - Re-run affected tests after resolving merge conflicts or changing shared contracts.

7. Update progress.
   - Mark completed nodes, changed nodes, skipped nodes, and plan deviations.
   - If the plan no longer fits reality, revise the plan before continuing.
   - If a node affects more files, modules, contracts, schemas, config, permissions, or shared state than expected, pause and run `change-impact-analysis` before continuing.

8. Finish.
   - Run final relevant validation.
   - Before claiming a node or plan complete, list the verified chain: commands run, what they proved, and any path that remains scaffolded or unverified. A passing build or created files are not evidence that the full runtime chain works.
   - Summarize implementation, verification, deviations, residual risk, and recommended `prepare-commit` scope.

## Record the Run

After a node or phase finishes (including blocked or abandoned outcomes), append
a short feedback-loop event:

```bash
python3 <dev-skills>/scripts/record_skill_run.py \
  --skill implement-plan \
  --status completed \
  --validation pass \
  --task-type implementation \
  --next-handoff prepare-commit \
  --friction <short-tag> \
  --feedback <short non-sensitive note>
```

Record `blocked` and `abandoned` outcomes too; they are the most useful signals
for future retrospectives.

## Handoff Rules

- If the implementation plan becomes invalid, hand off to `write-execution-plan` to revise sequencing.
- If the plan artifact or hash is missing/stale, hand off to `write-execution-plan` before any repair or code change.
- If scope expands or affected contracts are unclear, hand off to `change-impact-analysis`.
- If implementation completes, hand off to `prepare-commit`.

## Output Format

Answer in the user's language unless they request otherwise. Use concise progress updates during work. At the end, use:

```markdown
## Implemented

- <Completed node or phase>

## Verification

- `<command or manual check>`: <result>

## Plan Deviations

- <Deviation and why it was necessary, or "None">

## Task Group Updates

- <Dependency satisfied, downstream tasks promoted/blocked, or "None">

## Subagent Merge Notes

- <Merged subagent work, review result, and post-merge validation, or "Not used">

## Remaining Work

- <Incomplete nodes, follow-up cleanup, or "None">

## Residual Risk

- <Risk or "No known residual risk beyond normal review">

## Next Gate

Run `prepare-commit` on the final diff before commit.
```

For small changes, compress the output but keep implemented work, verification, deviations, and residual risk.
