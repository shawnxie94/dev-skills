---
name: implement-plan
description: Implement an approved execution plan one verified step at a time. Use when the user asks to implement, execute, carry out, or continue from a write-execution-plan output, implementation DAG, task plan, or subagent plan. Focus on verification-first development, TDD/regression/characterization test selection, scoped edits, goal-backed long-running work, subagent output review and merge, node-level validation, integration validation, progress updates, and final handoff to prepare-commit.
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
- Use `prepare-commit` as the final quality gate, not as a substitute for node-level validation.

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
   - If no plan exists, ask for or create a `write-execution-plan` first unless the work is trivial.

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
   - Summarize implementation, verification, deviations, residual risk, and recommended `prepare-commit` scope.

## Handoff Rules

- If the implementation plan becomes invalid, hand off to `write-execution-plan` to revise sequencing.
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
