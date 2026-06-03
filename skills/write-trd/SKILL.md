---
name: write-trd
description: Turn a PRD, settled product requirements, or feature scope into a concise Technical Requirements / Technical Design Document (TRD). Use when the user asks to write a TRD, technical design, technical requirements document, 技术方案, 技术设计文档, or to convert product requirements into implementation-ready technical design inputs. Focus on architecture boundaries, data model, APIs, state flow, security, error handling, observability, compatibility, migration, testing strategy, and write-execution-plan inputs without decomposing into detailed tasks or writing code.
---

# Write TRD

Use this skill after the PRD or product requirements are clear enough to design technically. The TRD should bridge product requirements and execution planning: it defines how the system should be shaped, what contracts must exist, and what risks must be handled before implementation.

## Core Principles

- Start from requirements. Do not invent product scope beyond the PRD unless you mark it as an assumption or open question.
- Design boundaries before internals. Clarify modules, ownership, interfaces, data, and responsibilities before implementation details.
- Make tradeoffs explicit. Record important alternatives and why the selected approach fits the constraints.
- Preserve compatibility. Call out existing API, data, config, migration, rollout, and rollback constraints.
- Design for operation. Include failure handling, observability, security, and testability, not only the happy path.
- Stop before task planning. Leave step-by-step implementation sequencing to `write-execution-plan`.

## Inputs to Look For

Use the PRD, prior discussion, research brief, existing codebase, API docs, schemas, architecture notes, or operational constraints when available.

Extract:

- Product goals, non-goals, and acceptance criteria.
- User flows and system workflows.
- Functional and non-functional requirements.
- Existing architecture, modules, interfaces, data models, and dependencies.
- Security, privacy, compliance, reliability, performance, and observability constraints.
- Migration, rollout, compatibility, and rollback constraints.

## TRD Workflow

1. Restate the technical goal.
   - Connect the design to the PRD goal.
   - Identify non-goals so the technical scope does not expand.

2. Map system context.
   - Identify affected components, data stores, external services, users, and integration points.
   - Note existing constraints from the codebase or platform.

3. Define the proposed design.
   - Specify module boundaries and responsibilities.
   - Define key interfaces, APIs, events, data models, or configuration contracts.
   - Describe state flow and important lifecycle transitions.

4. Address quality attributes.
   - Cover relevant security, privacy, performance, reliability, scalability, compatibility, accessibility, and observability concerns.

5. Plan compatibility and migration.
   - Call out deploy order, data migration, feature flags, backfill, fallback, and rollback needs when relevant.

6. Define verification strategy.
   - List unit, integration, e2e, migration, performance, security, or observability checks required by the design.

7. Prepare `write-execution-plan` inputs.
   - Summarize implementation slices, sequencing constraints, dependencies, and unresolved decisions without turning them into a full task plan.

If affected modules, contracts, data flow, or compatibility risks are unclear, run `change-impact-analysis` before finalizing the TRD.

## Handoff Rules

- If the TRD is accepted and implementation sequencing is needed, hand off to `write-execution-plan`.
- If impact scope is unclear, hand off to `change-impact-analysis`.
- If the user asks to implement directly, recommend `write-execution-plan` first unless the change is trivial.

## TRD Checklist

Use the relevant parts of this checklist:

- Architecture: components, ownership, boundaries, dependency direction.
- Interfaces: API routes, request/response shapes, events, SDKs, CLI/config contracts.
- Data: schemas, storage, indexes, migration, retention, privacy, lineage.
- State: lifecycle, transitions, idempotency, retries, concurrency, transactions.
- Security: authentication, authorization, validation, secrets, audit trail, PII exposure.
- Reliability: failure modes, fallbacks, degradation, timeouts, rate limits, rollback.
- Observability: logs, metrics, traces, alerts, dashboards, operational runbooks.
- Compatibility: backward compatibility, deploy order, old/new version coexistence.
- Testing: coverage strategy, fixtures, test data, regression cases, non-functional checks.
- Open decisions: assumptions, tradeoffs, unresolved constraints, research gaps.

## Output Format

Answer in the user's language unless they request otherwise. Use this structure when practical:

```markdown
# TRD: <Feature or System Name>

## Background and Goals

<PRD context, technical goal, and non-goals>

## System Context

<Affected components, external dependencies, data stores, and current constraints>

## Proposed Design

### Components and Responsibilities

<Modules, ownership, and boundaries>

### Interfaces and Contracts

<APIs, events, schemas, config, or other contracts>

### Data and State

<Data model, storage, state flow, lifecycle, idempotency, migration considerations>

## Quality Attributes

<Security, privacy, reliability, performance, compatibility, accessibility, observability>

## Compatibility, Migration, and Rollback

<Deploy order, migration path, fallback, feature flags, rollback>

## Testing and Verification

<Tests and checks required to trust this design>

## Tradeoffs and Alternatives

<Options considered and why this design is preferred>

## Open Questions

<Decisions that must be resolved before implementation>

## Execution Plan Inputs

<Implementation slices, dependencies, sequencing constraints, and risks for the next planning step>
```

For small features, compress sections while preserving system context, proposed design, risks, testing, and open questions.
