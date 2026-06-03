---
name: refactor-plan
description: Plan and guide safe code refactors before implementation. Use when the user asks to refactor, reorganize, simplify, decouple, extract modules, reduce duplication, improve maintainability, migrate implementation structure, or clean up technical debt. Emphasize behavior preservation, scope control, risk assessment, characterization tests, incremental execution, verification, and rollback points.
---

# Refactor Plan

Use this skill to keep refactoring deliberate and safe. A refactor should improve structure while preserving externally visible behavior unless the user explicitly asks for behavior changes.

## Core Principles

- Preserve behavior first. Treat changed behavior as a product change, not as incidental cleanup.
- Move in small steps. Prefer reversible edits with a clear verification point after each step.
- Separate mechanical changes from semantic changes. Rename, move, extract, and reformat separately from logic changes.
- Protect existing behavior before changing structure. Use existing tests, characterization tests, or explicit manual checks.
- Prefer compatibility during risky migrations. Use parallel change or branch by abstraction when callers, APIs, data models, or deployment order may be affected.
- Let complexity drive process weight. Small local refactors need a short plan; cross-module or behavior-adjacent refactors need explicit risk and rollback handling.

## Refactor Types

Classify the request before planning:

- Mechanical cleanup: renames, moves, formatting, import organization, simple extraction.
- Local structure improvement: split functions, remove duplication, clarify module boundaries, improve naming.
- Behavior-adjacent refactor: error handling, state flow, async logic, caching, permissions, data shape, validation, or public API internals.
- Architectural migration: replace implementations, introduce abstraction layers, split packages or services, migrate storage, or change cross-module dependencies.

The higher the type, the more strongly you should require behavior protection, staged rollout, and rollback points.

## Risk Checklist

Check the areas touched by the refactor:

- Public contracts: exported APIs, routes, CLI flags, config keys, serialized fields, database schemas.
- Data and state: migrations, cache keys, retries, idempotency, state transitions, background jobs.
- Security and access control: authn, authz, validation, sensitive logs, privilege boundaries.
- Concurrency and timing: async ordering, shared mutable state, timers, queues, locks, transactions.
- Runtime and deployability: environment differences, feature flags, deploy order, rollback path.
- Tests and observability: coverage gaps, brittle tests, logs, metrics, and diagnosability.

Before refactoring shared interfaces, data models, module boundaries, generated artifacts, or widely used utilities, run `change-impact-analysis`.

## Handoff Rules

- If the refactor plan is accepted and should be implemented, hand off to `implement-plan`.
- If the refactor touches broad callers or shared contracts, hand off to `change-impact-analysis`.
- After implementation, hand off to `prepare-commit`.

## Planning Workflow

Before editing, produce a compact plan when the refactor is non-trivial:

1. State the refactor goal and the behavior that must remain unchanged.
2. Identify the refactor type and risk level.
3. Inspect the relevant code paths and existing tests.
4. Define behavior protection:
   - existing tests to rely on,
   - characterization tests to add,
   - or manual verification steps when tests are not practical.
5. Split the work into small steps with a verification point for each step.
6. Mark mechanical changes and semantic changes separately.
7. Identify compatibility strategy when needed:
   - parallel change for public contracts,
   - branch by abstraction for risky implementation replacement,
   - or Mikado-style prerequisite steps when dependencies block the target refactor.
8. Define completion criteria and leftover cleanup items.

Use this format for the plan:

```markdown
## Refactor Goal

<What improves, and what behavior must not change>

## Refactor Type

<Mechanical cleanup / Local structure improvement / Behavior-adjacent refactor / Architectural migration>

## Behavior Protection

<Existing tests, characterization tests, or manual verification>

## Risk Points

<Public contracts, data/state, security, concurrency, deployability, test gaps>

## Execution Steps

1. <Step, why it is safe, and how to verify it>
2. <Step, why it is safe, and how to verify it>
3. <Step, why it is safe, and how to verify it>

## Completion Criteria

<Observable conditions that mean the refactor is done>
```

## Execution Rules

When the user asks you to implement the refactor, follow the plan unless new evidence invalidates it.

- Read the relevant code before editing.
- Keep edits scoped to the refactor goal.
- Avoid opportunistic feature work.
- Prefer one coherent change at a time.
- Run the smallest relevant tests after each meaningful step when practical.
- If a planned step becomes unsafe, stop and revise the plan instead of forcing the refactor through.
- Report actual changes, verification results, behavior changes if any, and residual risk at the end.

If the user asks only for a refactor plan, stop after the plan and do not edit files.
