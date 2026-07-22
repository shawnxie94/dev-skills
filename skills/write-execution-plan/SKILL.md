---
name: write-execution-plan
description: Write an actionable execution plan from a TRD, technical design, or settled implementation scope, including an implementation DAG and optional multi-agent execution plan. Use when the user asks to write an execution plan, implementation plan, task breakdown, development plan, module dependency analysis, DAG, rollout sequence, agent concurrency plan, or uses Chinese requests such as 执行计划, 实施计划, 拆任务, 开发计划, 实施 DAG. Focus on dependency ordering, critical path, risk-first sequencing, validation checkpoints, required capabilities and skills, single-writer boundaries, and bounded execution-actor contracts without writing code.
---

# Write Execution Plan

Use this skill after the TRD or technical direction is clear enough to plan implementation. The goal is to convert design into an executable sequence, not to re-design the system or start coding.

## Core Principles

- Plan from dependencies, not from a flat TODO list.
- Build a lightweight implementation DAG before deciding the work order.
- Put risky or unknown work early enough to validate assumptions before broad implementation.
- Keep write ownership clear. Prefer a single writer for shared files, public interfaces, schemas, migrations, and cross-cutting contracts.
- Assign execution actors only when parallelism reduces time or improves analysis quality without creating merge conflicts or context confusion.
- Give every task required capabilities, required skills, write ownership, forbidden writes, a verification checkpoint, and a handoff-readiness signal.

## Inputs to Look For

Use the TRD, PRD, research brief, existing codebase, issue context, test layout, deployment constraints, and user constraints when available.

Extract:

- Modules, interfaces, data changes, migrations, integrations, and tests.
- Shared contracts: API shapes, schemas, config, permissions, events, generated types.
- Sequencing constraints: deploy order, migration order, feature flags, compatibility needs.
- Risk points: unknown APIs, data quality, concurrency, external services, performance, security, operational risk.
- Validation options: tests, smoke checks, manual flows, logs, metrics, local or staging verification.

## Document Artifact Mode

Before producing the execution plan, check the current working directory for `.dev-skills/config.toml`.

Document artifact mode is enabled only when that file exists and contains:

```toml
[document_artifacts]
enabled = true
```

When document artifact mode is disabled or the config is absent, keep the normal chat-output behavior.

When document artifact mode is enabled:

- Create or update the execution plan as a managed workspace file instead of only writing it in chat.
- Use `plans/` by default, or `document_artifacts.paths.execution_plan` when configured.
- Use a stable, descriptive filename such as `plans/<feature-slug>-execution-plan.md`.
- Include frontmatter with at least `id`, `type: execution_plan`, `status`, `created_at`, `updated_at`, `sources`, and `related`.
- Link source PRD/TRD paths in `related` when they exist.
- Include a `Remote Handoff Inputs` section that identifies which plan nodes can be delegated to a remote Codex and what context, exclusions, verification commands, and acceptance criteria the remote task needs.
- Keep the final chat response to the file path, status, and concise summary; do not duplicate the full document unless the user asks.
- If the file cannot be written while the mode is enabled, report the blocker instead of falling back to chat-only output.

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
   - If implementation units or dependencies are uncertain, run `change-impact-analysis` before finalizing the DAG.

4. Choose sequencing.
   - Prefer thin vertical slices when useful.
   - Put contract/schema decisions before dependent work.
   - Put spike or proof-of-risk tasks before broad implementation.
   - Separate setup, implementation, integration, verification, and cleanup.

5. Decide actor assignment and parallelization.
   - Choose among the local lead, local subagent, managed agent, remote worker, or unassigned actor.
   - Prefer delegated actors for independent read-only analysis, isolated modules, tests, documentation, or clearly bounded implementation.
   - Avoid concurrent writes to the same files, public contracts, database schemas, generated artifacts, or migration paths unless ownership is explicit.

6. Create per-actor execution contracts when delegation is recommended.
   - Each actor contract must define objective, scope, inputs, required capabilities, required skills, write ownership, forbidden writes, steps, verification, expected output, acceptance criteria, and handoff readiness.
   - Keep execution prompts narrow and avoid leaking expected answers.

7. Define verification and handoff.
   - Attach verification to each phase or DAG node.
   - State what the coordinating actor should inspect before accepting delegated output.
   - In document artifact mode, write the plan and remote handoff inputs to the execution plan file before the final response.

## Handoff Rules

- If the plan is approved for delegation to another machine, remote Codex, managed-agent issue, squad child issue, GitHub Issue, or task file, hand off to `prepare-remote`.
- If the plan is accepted and implementation should begin, hand off to `implement-plan`.
- If implementation units, dependencies, or shared-write boundaries are unclear, hand off to `change-impact-analysis`.
- If the plan is for a refactor, ensure `refactor-plan` has defined behavior protection first.

## Execution Actor Decision Rules

Recommend delegated actors when:

- Tasks are dependency-light and can be validated independently.
- Work is read-only research, codebase scanning, test gap analysis, or isolated module implementation.
- The expected output can be structured and reviewed by the coordinating actor.
- There is little risk of multiple agents editing the same shared files or contracts.

Avoid delegation when:

- Requirements or technical boundaries are still unclear.
- Tasks are tightly coupled or require continuous local debugging.
- Work touches one central module, public interface, database schema, migration, or generated artifact.
- The result cannot be objectively reviewed by the coordinating actor.

When in doubt, delegate analysis and keep shared code-writing with one explicitly assigned actor.

## Output Format

Answer in the user's language unless they request otherwise. Use this structure when practical:

```markdown
## Implementation Goal

<What will be implemented and what done means>

## Implementation Units

| ID | Unit | Description | Actor | Risk |
|---|---|---|---|---|
| U1 | <Name> | <Scope> | Local lead / Local subagent / Managed agent / Remote worker / Unassigned | Low/Med/High |

### Node Contract: U1

- Required capabilities: <reasoning, repository access, browser, domain knowledge, or other needs>
- Required skills: <skill names or "None">
- Write ownership: <allowed paths, modules, contracts, or "Read only">
- Forbidden writes: <explicit exclusions>
- Verification: <command, check, or evidence>
- Handoff readiness: <observable conditions required before downstream actors can start>

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

## Actor Parallelization Plan

Recommendation: <Delegate / Keep serial / Delegate analysis only>

Reasoning:
- <Why parallelism helps or hurts>

## Per-Actor Execution Contracts

### Actor: <Name or managed-platform role>

Objective: <What this actor should achieve>

Scope: <Files, modules, docs, or questions in scope>

Inputs: <TRD sections, files, constraints, raw artifacts>

Exclusions: <What not to modify or assume>

Steps:
1. <Step>
2. <Step>

Expected output: <Structured artifact or summary>

Acceptance criteria: <How the coordinating actor will judge usefulness>

Handoff readiness: <What must be true before the result can be accepted or downstream work starts>

## Verification Plan

<Tests, checks, manual validation, logs, metrics, or review gates>

## Open Questions and Risks

<Decisions or risks that must be resolved during execution>
```

For small changes, compress the DAG and actor sections. If delegation is not useful, say so explicitly and keep the plan serial.
