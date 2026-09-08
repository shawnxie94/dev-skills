---
name: implement-plan
description: Execute an approved whole-goal batch plan or an assigned parallel-DAG node without changing the selected execution strategy. Use when the user asks to implement, execute, carry out, or continue from an approved execution plan, batch goal, implementation DAG, or delegated task assignment（按计划实现、开始落地、继续实现）.
---

# Implement Plan

Use this skill to execute an approved implementation plan without drifting from
scope. Consume and preserve the plan's `orchestration_mode`,
`execution_target`, and `execution_backend`; do not
re-plan, create a DAG, or silently change who executes the work.

## Core Principles

- Follow the plan, but route material changes back to planning when new
  evidence invalidates it.
- In `batch`, implement the complete approved goal in one active goal and
  return only after the whole goal reaches a final state.
- In `parallel_dag`, implement only the assigned node and its explicit node
  acceptance; never claim sibling nodes.
- Choose a behavior protection mode before editing.
- Keep edits scoped to the whole batch or assigned node, as selected by the
  plan.
- Validate internal steps as needed, but expose one final batch result or one
  final node result to the coordinator.
- When this skill runs as a subagent, the subagent owns implementation and
  internal verification. The coordinating agent owns waiting and acceptance;
  it must not edit or repair implementation files in the same delegated loop.
- Scaffolded code is not implemented. Distinguish "scaffolded" from "verified" in every completion claim and name the end-to-end chain that was actually exercised.
- Enforce the assigned node's `write_ownership`, `forbidden_writes`, dependencies, verification, and feedback requirements when present.
- When agent-brain is present, treat its Task Pack as the outer contract and the selected dev-skill as the inner execution capability.
- Never run multiple coding tasks concurrently in the same worktree or on the same branch.
- Use `prepare-commit` as the final quality gate, not as a substitute for node-level validation.
- Treat node-level validation as an internal checkpoint only in
  `parallel_dag`. A `batch` plan has one final acceptance scope; do not stop for
  user confirmation after internal steps.

## Light Mode

Use light mode when all of these hold:

- No agent-brain Task Pack and no execution-plan unit is linked to the request.
- The change is already specified by the user and touches at most a couple of files.
- No shared contract, schema, migration, generated artifact, or permission boundary is affected.
- The user selected `execution_target=current_session` or no subagent handoff
  is involved.

In light mode, the current session may implement directly: skip Mandatory Plan
Preflight and read the relevant code; pick the lightest Behavior Protection
Mode; implement; validate the change; then hand off to `prepare-commit`. Keep
the output compressed to implemented work, verification, and residual risk.

Escape upward immediately when any of the following appears: shared contracts or schemas are affected, more files than expected change, an outer Task Pack or plan linkage turns out to exist, or the user asks for plan-linked execution. Escalate to the full preflight path before continuing.

## Mandatory Plan Preflight

Before editing any file, require an approved canonical execution plan for every
plan-linked or delegated implementation task. The plan may be supplied directly
by the user or by `$execution-delivery` (plan-mode artifact or delegate-mode
packet), but it must be a file on disk rather than chat-only prose. The plan
must declare `orchestration_mode: batch|parallel_dag`; legacy plans without it
must return to `$execution-delivery` for classification instead of being
silently interpreted. The Light Mode section above is the only escape.

For an agent-brain Task Pack, verify all of these values before Build:

1. `source_artifacts` contains the canonical execution-plan file (not only PRD/TRD files).
2. The file exists and its current `shasum -a 256` equals `source_plan_sha256`.
3. `plan_id`, `plan_unit_id`, and `base_commit` match the plan and the assigned unit.
4. The plan status is `approved`, or the user explicitly approved it in the current turn.
5. The Task Pack's `allowed_paths`, acceptance checks, and write ownership are a bounded subset of the plan unit or whole-goal root.
6. If `execution_target=subagent`, `execution_backend` is present and is either
   `codex_subagent` or `zcode_mcp`; never switch the selected adapter.

If any preflight check fails, do not create files, do not infer missing hashes, and do not begin implementation. Report the exact missing or mismatched field and hand off to `$execution-delivery` (plan mode) or `agent-brain` task mode to repair the contract. A generic YAML pass is not sufficient: the linkage and artifact freshness checks are mandatory.

## Assigned Node Boundary

When an execution-plan node, agent-brain Task Pack unit, delegate-mode task
packet, or subagent assignment is already defined, treat it as the current
execution context:

- In `batch`, execute the complete approved plan and its final acceptance
  contract. Internal steps are not separate parent-agent tasks.
- In `parallel_dag`, execute only that assigned node and its explicit
  verification contract. Do not scan for, claim, promote, or execute sibling
  nodes.
- Do not recursively delegate work unless the assignment explicitly grants orchestration responsibility.
- Respect the assignment's scope, dependencies, required skills, write ownership, forbidden writes, status, and feedback format.
- Report newly discovered dependencies or scope gaps to the orchestrating agent instead of expanding the node unilaterally.

Orchestration responsibility is perspective-dependent. When this skill runs as
the selected `current_session` target, the current agent may implement the
approved plan. When it runs as a `subagent`, it implements the assigned whole
batch or node and does not create more agents. A coordinating parent in
`subagent` mode only delegates, waits, and accepts; it does not perform the
implementation or piecemeal repair itself.

## Context And Output Budget

Keep the active turn to the smallest useful projection:

- Start with task scope, current node, changed-file names/stat, and the next
  verification target.
- Use `git diff --name-only` then `git diff --stat`; read the full diff only
  for the affected files or when a check is disputed.
- Passing commands contribute status and counts only. Keep stdout/stderr in
  the command or acceptance log; surface a bounded failure tail when action
  is needed.
- Do not repeat fresh acceptance, Context Pack, or handoff evidence merely to
  restamp a node. Re-open the durable artifact only when its hash, scope, or
  result is stale or inconsistent.

## Agent-brain Contract Bridge

When agent-brain is present, it owns the outer Task Pack, allowed paths,
acceptance lifecycle, and final scope result. This skill owns the selected
whole-batch or node implementation and verification. Run the brain validators
and acceptance commands named by the Task Pack; do not recreate the Task Pack
or replace its evidence with a prose summary. Keep the shared linkage fields
(`plan_id`, `plan_unit_id`, `source_plan_sha256`, `base_commit`,
`orchestration_mode`, `execution_target`, `execution_backend`, and readiness
identity) unchanged.

## Parallelism And Worktree Decision

Use the plan's high-level `orchestration_mode` first. `execution_backend`
identifies the subagent adapter and is not a worktree setting. `parallel_mode`
remains the lower-level worktree and write-isolation contract:

1. For `batch`, use one actor and one serial implementation context. Internal
   implementation steps may be ordered and verified, but they are not separate
   delegated tasks or parent-agent interaction points.
2. For `parallel_dag`, satisfy dependencies and run impact analysis before
   starting the assigned node.
3. If selected actors are read-only, they may share a checkout in parallel.
4. If actors write files but execution can be serialized and ownership is
   disjoint, reuse one checkout serially.
5. If actors must write simultaneously, require non-overlapping ownership,
   mutexes, dedicated branches, and dedicated worktrees.
6. If impact is unclear or shared state is involved, keep the work serial and
   assign one writer.

Each subagent receives only its whole-goal batch contract or assigned node
contract, required context, exclusions, verification commands, and expected
feedback format.

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

## Batch and DAG Progression

- In `batch`, the implementation batch is the complete approved goal. Keep one
  active host goal, execute the internal sequence without creating parent-agent
  interaction points, and return only when the whole goal reaches a final
  `completed`, `blocked`, or `failed` state.
- In `parallel_dag`, the implementation batch is the assigned plan node. Keep
  one active goal for that node, execute only its scope, and return after its
  node-level acceptance or an explicit blocker. Never claim sibling nodes.
- A `batch` result is not complete merely because an internal step passes. A
  `parallel_dag` node result is not the final feature result; the coordinator
  performs integration acceptance after all required nodes return.
- Do not stop for user confirmation after internal steps. Human input is only a
  blocker when the plan or packet explicitly requires it.

## Long-Running Work

For large implementations, run under one explicit goal so progress and
completion state remain stable across long work:

- If the user already started a `/goal`, use the approved plan as the goal
  blueprint.
- For a delegated `batch`, the subagent's goal covers the complete plan, not
  one generated node.
- For a delegated `parallel_dag`, the subagent's goal covers only the assigned
  node.
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
   - Identify the source plan, `orchestration_mode`, `execution_target`,
     `execution_backend`,
     whole-goal or assigned-node scope, expected behavior, verification mode,
     and done criteria.
   - If no explicit input is provided, ask for the approved plan or assignment
     before starting.
   - If no approved canonical plan exists, stop and route to
     `$execution-delivery` (plan mode); light mode applies only to a single,
     already-specified current-session change with no Task Pack plan unit.
   - If the plan lacks `orchestration_mode`, do not infer it; route back to
     `$execution-delivery` for classification.

2. Prepare verification.
   - For `batch`, identify the complete-goal verification and final acceptance
     scope. Internal checks may run during implementation, but they do not
     become parent-agent handoffs.
   - For `parallel_dag`, identify the assigned node's acceptance and any
     coordinator-owned integration check.
   - For TDD or regression work, prefer seeing the test fail before implementing
     when practical.

3. Implement the selected scope.
   - In `batch`, read the relevant files and complete the entire approved plan
     under the one goal. Keep all edits within the whole-goal ownership.
   - In `parallel_dag`, read the relevant files and implement only the assigned
     node. Keep all edits within node ownership.
   - Avoid opportunistic feature work, unrelated refactors, or new delegation.

4. Run internal verification.
   - Run the checks required by the plan or packet and fix failures caused by
     the selected scope when possible.
   - Record commands and outcomes in the task evidence.
   - Do not treat a child self-report as the coordinator's canonical acceptance
     evidence; the coordinator may re-run the final acceptance.

5. Return one final execution result.
   - Return `completed` only when the whole batch goal or assigned node has
     reached its declared implementation endpoint and required internal checks
     have run.
   - Return `blocked` for a missing decision, unavailable capability, required
     human/device action, or dependency that cannot be satisfied safely.
   - Return `failed` for an unresolved implementation or verification failure,
     preserving the current branch state and the complete failure evidence.
   - Include changed files, tests/checks run, deviations, residual risks,
     blockers, attempt number, and commit/PR reference when applicable.

6. Handle invalidated scope.
   - If new evidence changes the plan's scope, contracts, dependencies, or
     ownership, stop and report the complete discrepancy to the coordinator.
   - Do not repair the plan, create a new DAG, or ask for piecemeal parent
     interaction from inside the implementation run.

7. Finish the local lifecycle.
   - Run final relevant validation for `current_session`; for `subagent`, leave
     coordinator-owned final acceptance to the parent.
   - Before claiming completion, list the verified chain: commands run, what
     they proved, and any path that remains scaffolded or unverified. A passing
     build or created files are not evidence that the full runtime chain works.
   - Summarize implementation, verification, deviations, residual risk, and
     the next acceptance handoff.

## Record the Run

After a whole batch or assigned node finishes (including blocked or abandoned
outcomes), append a short feedback-loop event:

```bash
python3 <dev-skills>/scripts/record_skill_run.py \
  --skill implement-plan \
  --status completed \
  --validation pass \
  --task-type implementation \
  --next-handoff acceptance \
  --friction <short-tag> \
  --feedback <short non-sensitive note>
```

Record `blocked` and `abandoned` outcomes too; they are the most useful signals
for future retrospectives.

## Handoff Rules

- If the implementation plan becomes invalid, hand off to `$execution-delivery` (plan mode) to revise sequencing.
- If the plan artifact or hash is missing/stale, hand off to `$execution-delivery` (plan mode) before any repair or code change.
- If scope expands or affected contracts are unclear, hand off to `codebase-analysis` (impact mode).
- If `execution_target=current_session` implementation completes, hand off to
  `prepare-commit` when the user requests commit preparation.
- If `execution_target=subagent` implementation completes, return the final
  result to the coordinating agent; do not merge, create a repair prompt, or
  start sibling work from inside the child run.

## Output Format

Answer in the user's language unless they request otherwise. Use concise progress updates during work. At the end, use:

```markdown
## Execution Result

- status: `completed` | `blocked` | `failed`
- orchestration_mode: `batch` | `parallel_dag`
- execution_target: `current_session` | `subagent`
- execution_backend: `codex_subagent` | `zcode_mcp`
- attempt: `1` | `2`

## Implemented Scope

- <Complete approved goal for batch, or assigned node for parallel_dag>

## Verification

- `<command or manual check>`: <result>

## Plan Deviations

- <Deviation and why it was necessary, or "None">

## Acceptance Handoff

- <For current_session: final acceptance result. For subagent: coordinator must run final acceptance.>

## Changed Files And Evidence

- Changed files: <paths>
- Tests/checks run: <commands and results>
- Commit/PR: <reference or "None">

## Blocking Conditions And Deviations

- Deviations: <None or complete list>
- Blockers: <None or complete list>

## Residual Risk

- <Risk or "No known residual risk beyond normal review">

## Next Gate

<Coordinator acceptance, repair packet, `$execution-delivery` plan repair,
`prepare-commit`, or user decision after the second failed attempt.>
```

For small changes, compress the output but keep implemented work, verification, deviations, and residual risk.
