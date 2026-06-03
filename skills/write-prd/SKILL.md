---
name: write-prd
description: Turn already-discussed or mostly-settled requirements into a concise Product Requirements Document (PRD). Use when the user asks to write, draft, refine, or formalize a PRD, product requirements document, 需求文档, 产品需求文档, or to convert research notes, requirement discussions, feature ideas, or stakeholder decisions into a structured requirements artifact. Focus on scope, user scenarios, functional requirements, non-functional requirements, acceptance criteria, dependencies, open questions, and design inputs without drifting into technical implementation.
---

# Write PRD

Use this skill after the problem and rough requirements have been discussed enough to document. This is not an open-ended discovery skill; use it to crystallize settled requirements into a PRD and clearly mark what remains unresolved.

## Core Principles

- Capture decisions, not guesses. If a requirement is missing, mark it as an assumption or open question instead of silently inventing it.
- Keep the PRD implementation-neutral. Describe user value, behavior, constraints, and acceptance criteria; leave architecture and task planning to later skills.
- Make scope explicit. Define in-scope, out-of-scope, MVP, and follow-up items so implementation does not drift.
- Make behavior testable. Requirements should be specific enough to produce acceptance tests or review checks.
- Preserve traceability. Carry forward relevant research inputs, stakeholder decisions, constraints, and unresolved risks.

## Inputs to Look For

Use the user's message, prior discussion, research briefs, existing docs, issues, prototypes, screenshots, or code context when available.

Extract:

- Product goal and target users.
- User scenarios and workflows.
- Functional requirements.
- Non-functional requirements: performance, reliability, security, privacy, accessibility, compatibility, observability.
- Business rules, permissions, edge cases, and failure handling.
- Metrics, success criteria, or launch constraints.
- Dependencies, assumptions, risks, and unresolved questions.

## PRD Workflow

1. Restate the product goal.
   - Explain what problem the PRD is solving and for whom.
   - Keep it concrete and avoid marketing language.

2. Define scope.
   - Separate MVP scope, out-of-scope items, and later phases.
   - Call out constraints that affect implementation choices.

3. Describe user scenarios.
   - Use user journeys or scenario bullets.
   - Include normal flow, edge cases, and failure handling when relevant.

4. Write requirements.
   - Use clear, testable statements.
   - Group requirements by capability, workflow, or actor.
   - Include acceptance criteria for important behaviors.

5. Add non-functional requirements.
   - Include only relevant constraints, but do not ignore security, data, operations, and observability for risky systems.

6. Identify gaps.
   - List open questions, assumptions, risks, and decisions needed before technical design or implementation.

7. Produce design inputs.
   - Summarize what the technical design or execution plan must consider next.

## Handoff Rules

- If technical design is requested after the PRD, hand off to `write-trd`.
- If affected modules, data, contracts, or compatibility risks are unclear, hand off to `change-impact-analysis`.
- If the user asks to implement immediately, recommend `write-trd` and `write-execution-plan` first unless the change is trivial.

## Output Format

Answer in the user's language unless they request otherwise. Use this structure when practical:

```markdown
# PRD: <Feature or Product Name>

## Background

<Why this is needed and what context matters>

## Goals

- <Goal>

## Non-Goals

- <Explicitly out-of-scope item>

## Users and Scenarios

- <User / scenario / workflow>

## Requirements

### <Capability or Workflow>

- <Requirement>
- Acceptance criteria:
  - <Observable pass/fail condition>

## Non-Functional Requirements

- <Performance, security, privacy, reliability, compatibility, accessibility, observability, or operational constraints>

## Dependencies and Constraints

- <External systems, data, policy, timeline, platform, or organizational constraints>

## Open Questions

- <Question or assumption that needs confirmation>

## Risks

- <Product, technical, operational, data, compliance, or delivery risk>

## Design Inputs

- <Inputs that should feed technical design or execution planning>
```

For small features, compress sections instead of forcing a long document. If the user asks for implementation after the PRD, stop after the PRD unless they explicitly ask to continue into design or coding.
