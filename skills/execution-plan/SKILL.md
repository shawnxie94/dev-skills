---
name: execution-plan
description: Turn a TRD, technical design, or settled implementation scope into an actionable execution plan with an implementation DAG and optional subagent parallelization plan. Use when the user asks for an execution plan, implementation plan, task breakdown, development plan, module dependency analysis, DAG, rollout sequence, or subagent concurrency plan. Focus on dependency ordering, critical path, risk-first sequencing, validation checkpoints, single-writer boundaries, and per-subagent execution plans without writing code.
---

# Execution Plan

Use this skill after the TRD or technical direction is clear enough to plan implementation. The goal is to convert design into an executable sequence, not to re-design the system or start coding.

## Core Principles

- Plan from dependencies, not from a flat TODO list.
- Build a lightweight implementation DAG before deciding the work order.
- Put risky or unknown work early enough to validate assumptions before broad implementation.
- Keep write ownership clear. Prefer a single writer for shared files, public interfaces, schemas, migrations, and cross-cutting contracts.
- Use subagents only when parallelism reduces time or improves analysis quality without creating merge conflicts or context confusion.
- Give every task a verification checkpoint and completion signal.

## Inputs to Look For

Use the TRD, PRD, research brief, existing codebase, issue context, test layout, deployment constraints, and user constraints when available.

Extract:

- Modules, interfaces, data changes, migrations, integrations, and tests.
- Shared contracts: API shapes, schemas, config, permissions, events, generated types.
- Sequencing constraints: deploy order, migration order, feature flags, compatibility needs.
- Risk points: unknown APIs, data quality, concurrency, external services, performance, security, operational risk.
- Validation options: tests, smoke checks, manual flows, logs, metrics, local or staging verification.

## Planning Workflow

1. Restate the implementation goal.
   - Connect the plan to the TRD and define what will be considered done.

2. Identify implementation units.
   - Split work into coherent units: contracts, data, backend, frontend, integrations, tests, docs, deployment.
   - Keep units small enough to verify, but not so small that the plan becomes noise.

3. Build the implementation DAG.
   - List each unit and its dependencies.
   - Mark the critical path.
   - Mark risky nodes that should be validated early.
   - Mark shared-write nodes that should not be implemented concurrently.

4. Choose sequencing.
   - Prefer thin vertical slices when useful.
   - Put contract/schema decisions before dependent work.
   - Put spike or proof-of-risk tasks before broad implementation.
   - Separate setup, implementation, integration, verification, and cleanup.

5. Decide subagent parallelization.
   - Determine whether subagents are useful.
   - Prefer subagents for independent read-only analysis, isolated modules, tests, documentation, or clearly bounded implementation.
   - Avoid concurrent writes to the same files, public contracts, database schemas, generated artifacts, or migration paths unless ownership is explicit.

6. Create per-subagent execution plans when subagents are recommended.
   - Each subagent plan must define objective, scope, inputs, exclusions, steps, expected output, and acceptance criteria.
   - Keep subagent prompts narrow and avoid leaking expected answers.

7. Define verification and handoff.
   - Attach verification to each phase or DAG node.
   - State what the main agent should inspect before accepting subagent output.

## Subagent Decision Rules

Recommend subagents when:

- Tasks are dependency-light and can be validated independently.
- Work is read-only research, codebase scanning, test gap analysis, or isolated module implementation.
- The expected output can be structured and reviewed by the main agent.
- There is little risk of multiple agents editing the same shared files or contracts.

Avoid subagents when:

- Requirements or technical boundaries are still unclear.
- Tasks are tightly coupled or require continuous local debugging.
- Work touches one central module, public interface, database schema, migration, or generated artifact.
- The result cannot be objectively reviewed by the main agent.

When in doubt, use subagents for analysis and keep code-writing with the main agent.

## Output Format

Answer in the user's language unless they request otherwise. Use this structure when practical:

```markdown
## Implementation Goal

<What will be implemented and what done means>

## Implementation Units

| ID | Unit | Description | Owner | Risk |
|---|---|---|---|---|
| U1 | <Name> | <Scope> | Main/Subagent/Unassigned | Low/Med/High |

## Implementation DAG

| Unit | Depends On | Why |
|---|---|---|
| U2 | U1 | <Dependency reason> |

Critical path: <U1 -> U2 -> U4>
Risk-first nodes: <U3, U5>
Shared-write nodes: <U1, U2>

## Execution Sequence

1. <Step, units covered, verification checkpoint>
2. <Step, units covered, verification checkpoint>
3. <Step, units covered, verification checkpoint>

## Subagent Parallelization Plan

Recommendation: <Use subagents / Do not use subagents / Use only for analysis>

Reasoning:
- <Why parallelism helps or hurts>

## Per-Subagent Plans

### Subagent: <Name>

Objective: <What this subagent should achieve>

Scope: <Files, modules, docs, or questions in scope>

Inputs: <TRD sections, files, constraints, raw artifacts>

Exclusions: <What not to modify or assume>

Steps:
1. <Step>
2. <Step>

Expected output: <Structured artifact or summary>

Acceptance criteria: <How the main agent will judge usefulness>

## Verification Plan

<Tests, checks, manual validation, logs, metrics, or review gates>

## Open Questions and Risks

<Decisions or risks that must be resolved during execution>
```

For small changes, compress the DAG and subagent sections. If no subagents are useful, say so explicitly and keep the plan serial.
