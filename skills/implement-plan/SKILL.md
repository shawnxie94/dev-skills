---
name: implement-plan
description: Execute an approved batch plan or an assigned parallel-DAG node without changing the selected execution strategy（按计划实现、开始落地、继续实现）. Use for an approved execution plan, batch goal, implementation DAG, or delegated task assignment; small already-specified changes use its light mode.
---

# Implement Plan

Use this skill to execute an approved implementation plan without drifting from
scope. Consume and preserve the plan's `orchestration_mode`,
`execution_target`, and `execution_backend`; do not
re-plan, create a DAG, or silently change who executes the work.

## Core Principles

- Follow the plan, but route material changes back to planning when new
  evidence invalidates it.
- Inside the approved scope, prefer the minimum viable implementation that
  satisfies acceptance (see Minimum Viable Implementation Ladder); this never
  authorizes shrinking the approved scope.
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
  it must not implement feature work or repair implementation files beyond the
  bounded `root_fix` exception (mechanical compile/lint/test fixes inside
  `allowed_paths`, recorded in the round ledger) in the same delegated loop.
  Role selection, Runtime adapter, context policy, and recovery come from
  `$subagent-orchestration`; this skill remains the worker execution contract.
- A subagent running this skill is a leaf executor: it must not call, spawn, or delegate to another subagent. Report any orchestration need to the coordinating agent.
- If the user specified a subagent model, provider, runtime, or thinking level, use that exact choice. If it is unavailable or unsupported, return a user-visible blocker instead of switching models or providers.
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
6. If `execution_target=subagent`, `execution_backend` is present and is one of
   `zcode_subagent`, `codex_subagent`, `zcode_mcp`, or `pi_subagent`, matching the
   current harness; never switch the selected adapter. When the selected
   backend is `pi_subagent`, the packet must also carry the resolved logical
   role/profile and `subagent_scope` (`user`, `project`, or `both`; default
   `user`). Resolve the official Pi SDK child-session lifecycle through
   `$subagent-orchestration` before Build.

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
- A `batch` result is not complete because an internal step passed, and a
  `parallel_dag` node result is not the final feature result; the coordinator
  owns integration acceptance. Do not stop for user confirmation after
  internal steps unless the plan or packet explicitly requires it.

Orchestration responsibility is perspective-dependent. When this skill runs as
the selected `current_session` target, the current agent may implement the
approved plan. When it runs as a `subagent`, it implements the assigned whole
batch or node and does not create more agents. A coordinating parent in
`subagent` mode only delegates, waits, and accepts; it does not perform the
implementation or piecemeal repair itself.

## Context And Output Budget

The hot/warm/cold budget is owned by agent-brain `task-loop.md`; the repo-level
short-output convention is in this repository's README. Inside a Build run:

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
identifies the subagent adapter and is not a worktree setting. The
`parallel_mode` taxonomy, mutexes, and write-ownership rules are owned by
`$execution-delivery` (Shared Execution Contract); worktree location, branch
naming, and `cleanup-run` behavior are owned by agent-brain `task-loop.md`. Do
not restate or re-decide either contract here. Execution-side rules:

1. `batch`: one actor and one serial implementation context. Ordered internal
   steps are not delegated tasks or parent-agent interaction points.
2. `parallel_dag`: satisfy dependencies and run impact analysis before starting
   the assigned node; never touch a sibling node.
3. Read-only actors may share a checkout. Serialized writes with disjoint
   ownership may reuse one checkout. Simultaneous writes require non-overlapping
   ownership, a mutex, a dedicated branch, and a dedicated worktree.
4. Unclear impact or shared state: keep the work serial with one writer. Never
   let two agents edit the same checkout at once; merge isolated results in
   dependency order and rebase dependents after a merge.

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

## Minimum Viable Implementation Ladder

Inside the approved scope, prefer the smallest implementation that satisfies the
plan's acceptance checks. Before writing new code, climb this ladder and stop at
the first rung that solves the real problem:

1. Does this need to exist at all? Drop speculative or unrequested work.
2. Does the codebase already implement it? Reuse the existing helper, module, or pattern.
3. Does the standard library provide it?
4. Does the native platform or framework provide it?
5. Does an already-installed dependency solve it?
6. Can it be expressed as one clear line or a small local change?
7. Only then: write the minimum new code that works.

Scope authority is a hard boundary:

- The ladder optimizes **how** the approved scope is implemented. It never
  authorizes shrinking, skipping, deferring, or silently reinterpreting work
  that the plan, Task Pack, or node acceptance requires.
- If a rung suggests planned work is unnecessary or replaceable, do not decide
  unilaterally. Report it as a scope finding and route back to
  `$execution-delivery` (plan mode) or the coordinating agent. A silent scope
  cut is a contract violation, not a saving.
- The ladder never overrides the chosen Behavior Protection Mode. Never simplify
  away validation, error handling, security, accessibility, migrations, or the
  plan's required tests.
- Record material ladder outcomes (reused component, dropped local abstraction,
  stdlib or existing dependency instead of a new one) under `Plan Deviations`.
  Keep trivial reuse decisions out of the report.

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
   - When the repository has a `.codegraph/` index, locate code through the
     CodeGraph CLI before broad grep/read: `codegraph context "<task>"` or
     `codegraph explore "<question>"`, then `codegraph impact <symbol>` and
     `codegraph affected <files>` for blast radius. Verify graph output against
     live files. If the CLI or index is unavailable, say so and fall back to
     `rg` plus direct reads.
   - Climb the Minimum Viable Implementation Ladder inside the selected scope;
     it optimizes implementation, not scope.
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
- If the delegated runtime, role, lifecycle, or context policy is unclear, hand off to `$subagent-orchestration` before implementation.
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
- execution_backend: `zcode_subagent` | `codex_subagent` | `zcode_mcp` | `pi_subagent`
- logical_role: `<resolved by $subagent-orchestration when target=subagent>`
- subagent_scope: `user` | `project` | `both` (Pi only)
- context_policy: `fresh` | `fork` | `retained_resume`
- lifecycle_policy: `<foreground/background, timeout, status/wait, stop/resume, failure handling>`
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

<Coordinator acceptance, round packet, `$execution-delivery` plan repair,
`prepare-commit`, or user decision after the round budget is exhausted.>
```

For small changes, compress the output but keep implemented work, verification, deviations, and residual risk.
