# Requirement Research Packet Template

```markdown
---
id: <packet-id>
type: requirement_research
status: draft | ready_for_prd | ready_for_solution | ready_for_estimation
version: <version>
created_at: <YYYY-MM-DD>
updated_at: <YYYY-MM-DD>
research_cutoff: <YYYY-MM-DD>
estimation:
  rubric_version: "2.0"
  unit: person_months
  working_days_per_person_month: 20
sources: []
related: {}
---

# <Requirement> Research Packet

## Decision To Support

<Decision, intended consumers, and completion criteria.>

## Scope And Constraints

- In scope:
- Out of scope:
- Constraints:
- Assumptions:

## Executive Findings

| Finding | Evidence IDs | Confidence | Decision impact |
| --- | --- | --- | --- |

## Actors And Functional Scope

| Capability ID | Actor | Trigger | Functional outcome | Key rules | Acceptance signal |
| --- | --- | --- | --- | --- | --- |

## Business Flows

### Current Flow

<Actors, steps, handoffs, exceptions, and pain points.>

### Target Flow

<Actors, steps, decisions, alternate paths, failures, and operational ownership.>

## System Boundaries

| System / component | Responsibility | Owns data | Integrates with | Boundary notes |
| --- | --- | --- | --- | --- |

## Technical Options

| Option | Strategy | Mature component / service | Fits when | Benefits | Costs / risks | Evidence IDs | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Mature Component Reuse Assessment

| Need | Candidate | Type | Maturity evidence | Fit gaps | Security / compliance / license | Operations / lock-in / cost | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |

Decision must be `reuse`, `extend`, `custom`, or `not_applicable`. Use `custom` only when the requirement explicitly requires self-development. If documented candidates fail material criteria, keep the item open until the decision owner approves and records an explicit custom-build requirement.

## Non-Functional And Operational Requirements

<Security, privacy, compliance, reliability, performance, observability, scalability, support, and cost.>

## Frozen Estimation Work Items

| ID | Name | Outcome | Role / discipline | Depends on | Delivery strategy | Reused component | Custom-build justification | Acceptance signal | Complexity drivers | Exclusions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W001 | <name> | <observable outcome> | <role> | <IDs or none> | <reuse / extend / custom / not_applicable> | <component + version/tier or none> | <explicit requirement or approved decision record; required for custom> | <signal> | <drivers> | <excluded work> |

Do not include effort, duration, points, or target dates in this table.

## Dependencies And Risks

| ID | Type | Description | Impact | Mitigation / decision owner |
| --- | --- | --- | --- | --- |

## Evidence Matrix

<Rows following evidence-matrix.md.>

## Counter-Evidence And Failure Modes

<Evidence and scenarios that challenge the preferred direction.>

## Open Decisions And Research Gaps

| Question | Why it matters | Blocking? | Owner | Next evidence / action |
| --- | --- | --- | --- | --- |

## Readiness

- PRD readiness: ready | not ready — <reason>
- Solution readiness: ready | not ready — <reason>
- Estimation readiness: ready | not ready — <reason>
- Evidence limitations:
```

## Readability note for publishers

When publishing to an issue thread (e.g. Multica), attach this full packet as the SoT file and put only a short Decision Card in the comment. Inside the file, keep estimator-critical sections easy to scan first; long evidence extracts and deep notes may follow as appendix-style detail without removing required sections.

When the packet is frozen for estimation, compute the SHA-256 of the exact file or input bundle outside this self-referential content and give the same `packet_hash` to every reviewer.
