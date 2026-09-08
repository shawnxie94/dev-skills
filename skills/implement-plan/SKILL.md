---
name: implement-plan
description: Implement an approved execution plan one verified step at a time, delegating node work to subagents of the current agent. Use when the user asks to implement, execute, carry out, or continue from an approved execution plan, implementation DAG, task plan, or delegated node assignment（按计划实现、开始落地、继续实现）.
---

# Implement Plan

Use this skill to execute an approved implementation plan without drifting from scope. The goal is to move through the plan in small, verified steps and continue automatically through the runnable dependency chain until the requested implementation batch is complete or a genuine blocker requires external input.

## Core Principles

- Follow the plan, but revise it when new evidence invalidates it.
- Implement one phase or DAG node at a time.
- Choose a behavior protection mode before editing.
- Keep edits scoped to the current node.
- Validate after each meaningful step, not only at the end.
- Treat subagent output as candidate work that the main agent must review, merge, and verify.
- Scaffolded code is not implemented. Distinguish "scaffolded" from "verified" in every completion claim and name the end-to-end chain that was actually exercised.
- Enforce the assigned node's `write_ownership`, `forbidden_writes`, dependencies, verification, and feedback requirements when present.
- When agent-brain is present, treat its Task Pack as the outer contract and the selected dev-skill as the inner execution capability.
- Never run multiple coding tasks concurrently in the same worktree or on the same branch.
- Use `prepare-commit` as the final quality gate, not as a substitute for node-level validation.
- Treat node-level validation as an internal checkpoint. Do not stop for user confirmation after every accepted node when the user requested the full plan or feature batch.

## Light Mode

Use light mode when all of these hold:

- No agent-brain Task Pack and no execution-plan unit is linked to the request.
- The change is already specified by the user and touches at most a couple of files.
- No shared contract, schema, migration, generated artifact, or permission boundary is affected.

In light mode: skip Mandatory Plan Preflight and read the relevant code; pick the lightest Behavior Protection Mode; implement; validate the change; then hand off to `prepare-commit`. Keep the output compressed to implemented work, verification, and residual risk.

Escape upward immediately when any of the following appears: shared contracts or schemas are affected, more files than expected change, an outer Task Pack or plan linkage turns out to exist, or the user asks for plan-linked execution. Escalate to the full preflight path before continuing.

## Mandatory Plan Preflight

Before editing any file, require an approved canonical execution plan for every plan-linked or delegated implementation task. The plan may be supplied directly by the user or by `$execution-delivery` (plan-mode artifact or delegate-mode packet), but it must be a file on disk rather than chat-only prose. The Light Mode section above is the only escape.

For an agent-brain Task Pack, verify all of these values before Build:

1. `source_artifacts` contains the canonical execution-plan file (not only PRD/TRD files).
2. The file exists and its current `shasum -a 256` equals `source_plan_sha256`.
3. `plan_id`, `plan_unit_id`, and `base_commit` match the plan and the assigned unit.
4. The plan status is `approved`, or the user explicitly approved it in the current turn.
5. The Task Pack's `allowed_paths`, acceptance checks, and write ownership are a bounded subset of the plan unit.

If any preflight check fails, do not create files, do not infer missing hashes, and do not begin implementation. Report the exact missing or mismatched field and hand off to `$execution-delivery` (plan mode) or `agent-brain` task mode to repair the contract. A generic YAML pass is not sufficient: the linkage and artifact freshness checks are mandatory.

## Assigned Node Boundary

When an execution-plan node, agent-brain Task Pack unit, delegate-mode task packet, or subagent assignment is already defined, treat it as the current-node context:

- Execute only that assigned node and its explicit verification contract.
- Do not scan for, claim, promote, or execute sibling nodes.
- Do not recursively delegate work unless the assignment explicitly grants orchestration responsibility.
- Respect the assignment's scope, dependencies, required skills, write ownership, forbidden writes, status, and feedback format.
- Report newly discovered dependencies or scope gaps to the orchestrating agent instead of expanding the node unilaterally.

Orchestration responsibility is perspective-dependent. When you run as the main agent on a direct user request, the request itself grants orchestration responsibility and you decide subagent delegation yourself; the restrictions above apply when you are executing as an assigned, delegated actor.

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
acceptance lifecycle, and final scope result. This skill owns only the current
plan node's implementation and verification. Run the brain validators and
acceptance commands named by the Task Pack; do not recreate the Task Pack or
replace its evidence with a prose summary. Keep the shared linkage fields
(`plan_id`, `plan_unit_id`, `source_plan_sha256`, `base_commit`, and readiness
identity) unchanged. Use the plan's write ownership and the parallelism rules
below for node execution.

## Parallelism And Worktree Decision

Use this decision order, matching the shared `parallel_mode` contract in `$execution-delivery`:

1. Satisfy dependencies and run impact analysis.
2. If every selected actor is read-only, run them in parallel in the same checkout.
3. If actors write files but execution can be serialized and write ownership is disjoint, reuse one checkout serially.
4. If actors must write simultaneously, require non-overlapping ownership, non-overlapping mutexes, dedicated branches, and dedicated worktrees.
5. If impact is unclear or shared state is involved, keep the work serial and assign one writer.

Each subagent receives only its node contract, required context, exclusions, verification commands, and expected feedback format.

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

## Batch Progression

- The implementation batch is the user's approved goal or the plan phase (for example, Phase A U1–U8), not one `plan_unit_id`.
- After a node passes its required verification, immediately resolve dependencies and execute the next runnable node in the same batch.
- Keep one active host goal for the batch; update progress internally without replacing it with a new per-node user task.
- Return to the user only after the batch-level acceptance passes, or when a genuine blocker is reached: missing/conflicting requirements, unavailable external capability, required human/device action, irreversible external mutation, or exhausted repair/escalation gate.
- A node's `done` state satisfies a dependency checkpoint but does not satisfy the user's overall request.

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
   - If no explicit input is provided, ask for the plan or node assignment before starting.
   - If no approved canonical plan exists, stop and route to `$execution-delivery` (plan mode); light mode (above) applies only to a single-file, already-specified change with no Task Pack plan unit.

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
   - Never delegate nodes that require runtime-reserved tooling such as browser control, desktop control, or visual acceptance gates; perform those verifications as the main agent.
   - Inspect the subagent's scope, claims, and artifacts before applying them.
   - Avoid merging conflicting edits to shared files, public contracts, schemas, migrations, or generated artifacts without explicit ownership.
   - After merging, immediately run the relevant node-level verification.

6. Integrate.
   - After a set of related nodes is complete, run the integration check defined by the plan.
   - Re-run affected tests after resolving merge conflicts or changing shared contracts.

7. Update progress.
   - Mark completed nodes, changed nodes, skipped nodes, and plan deviations, then continue to the next runnable node when continuous batch execution applies.
   - If the plan no longer fits reality, revise the plan before continuing.
   - If a node affects more files, modules, contracts, schemas, config, permissions, or shared state than expected, pause and run `codebase-analysis` (impact mode) before continuing.

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

- If the implementation plan becomes invalid, hand off to `$execution-delivery` (plan mode) to revise sequencing.
- If the plan artifact or hash is missing/stale, hand off to `$execution-delivery` (plan mode) before any repair or code change.
- If scope expands or affected contracts are unclear, hand off to `codebase-analysis` (impact mode).
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

## Batch Updates

- <Dependency satisfied or blocked for the batch, or "None">

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
