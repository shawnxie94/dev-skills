---
name: change-impact-analysis
description: Analyze the blast radius of a proposed change, current diff, refactor, API change, schema change, config change, dependency change, or bug fix before design, planning, implementation, or commit. Use when the user asks what a change affects, whether a change is safe, which modules or callers are impacted, what tests are needed, or when another skill finds unclear affected modules, contracts, data flow, compatibility, shared state, migrations, permissions, caching, or config. Focus on direct and indirect impact, contracts, data, config, tests, compatibility risks, scope boundaries, and next-step inputs.
---

# Change Impact Analysis

Use this skill to understand the impact of a concrete change before designing, planning, implementing, refactoring, or committing it. The goal is to expose affected modules, contracts, tests, and risks so later work does not miss hidden dependencies.

## Core Principles

- Analyze a specific change, not the whole repository.
- Follow real references, callers, data flow, and runtime boundaries.
- Separate direct impact from indirect impact.
- Treat public contracts, schemas, permissions, config, migrations, caches, and shared utilities as high-risk boundaries.
- Recommend scope changes when the impact is larger or smaller than expected.
- Do not implement the change; produce inputs for the next skill or decision.

## What To Inspect

Use the relevant context:

- Proposed requirement, PRD, TRD, execution plan, bug reproduction, refactor plan, or current diff.
- Code references, imports, callers, route maps, event handlers, jobs, commands, and tests.
- API contracts, request/response shapes, schemas, migrations, config keys, env vars, feature flags.
- Data flow, cache keys, permissions, state transitions, generated artifacts, external integrations.
- Existing tests, fixtures, e2e flows, CI checks, and manual validation paths.

## Analysis Workflow

1. Define the change.
   - State what is being changed and why.
   - Identify the source of truth: requirement, diff, file, API, schema, config, or bug.

2. Find direct impact.
   - Identify files, modules, functions, routes, schemas, configs, and tests directly touched or expected to change.

3. Find indirect impact.
   - Trace callers, consumers, downstream workflows, generated artifacts, caches, permissions, jobs, and external integrations.

4. Classify risk.
   - Mark API, data, config, permission, migration, concurrency, cache, and deployment-sensitive risks.
   - Note compatibility concerns and old/new behavior coexistence.

5. Define validation scope.
   - Recommend tests and checks required to trust the change.
   - Identify missing test coverage or manual verification needs.

6. Produce next-step inputs.
   - State whether the TRD, execution plan, refactor plan, implementation scope, or commit scope should expand, shrink, or stay unchanged.

## Handoff Rules

- If the impact requires design changes, hand off to `write-trd`.
- If the impact changes task ordering or dependencies, hand off to `write-execution-plan`.
- If the impact is refactor-specific, hand off to `refactor-plan`.
- If the impact is discovered during implementation, hand off back to `implement-plan` with updated scope.
- If the impact is discovered before commit, hand off back to `prepare-commit` with validation recommendations.

## Output Format

Answer in the user's language unless they request otherwise. Use this structure when practical:

```markdown
## Change Summary

<The proposed change, current diff, or behavior being analyzed>

## Direct Impact

| Area | Files / Modules | Why |
|---|---|---|
| <area> | <paths> | <reason> |

## Indirect Impact

<Callers, consumers, downstream workflows, data flow, generated artifacts, external integrations>

## Contract / Data / Config Impact

<APIs, schemas, migrations, env vars, config keys, permissions, cache keys, serialization>

## Test Impact

<Tests to run, tests to add, fixtures, e2e/manual verification>

## Compatibility Risks

<Backward compatibility, old/new coexistence, rollout, rollback, hidden dependencies>

## Scope Recommendation

<Expand, shrink, or keep scope; boundaries that should not be changed opportunistically>

## Inputs For Next Step

<What to pass to write-trd, write-execution-plan, refactor-plan, implement-plan, prepare-commit, or bug-reproduction>
```

For small changes, compress the output while preserving direct impact, indirect impact, validation, and risks.
