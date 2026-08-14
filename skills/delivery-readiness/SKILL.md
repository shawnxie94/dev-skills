---
name: delivery-readiness
description: Assess whether a delivery artifact is complete and safe to hand off across PRD, TRD, execution plan, implementation, verification, and release stages. Use when a team is about to move between delivery stages, when PRD/TRD/plan content may be incomplete or contradictory, or when a change needs a repeatable assess → repair → reassess loop with traceable blockers, hashes, and evidence.
---

# Delivery Readiness

Use this skill as the cross-stage quality gate for a delivery, not as a replacement for PRD, TRD, execution planning, implementation, or release operations. It answers “can this stage safely hand off to the next one?” and leaves the source artifact owned by the skill that created it.

## Modes

Choose one mode explicitly:

- `assess`: read the source artifacts and produce one complete assessment. This is read-only.
- `gate`: evaluate one named transition and return `ready` or `blocked`. This is read-only.
- `loop`: run assess → classify → repair → hash → full reassess until `ready` or `blocked`. Repair is allowed only when the user explicitly authorizes it, for example `loop --repair`.
- `trace`: inspect requirement → design → plan → acceptance coverage and contradictions without changing artifacts.

If the user asks only whether something is ready, use `gate` or `assess`; do not silently enter repair mode. If they ask to “fix until ready”, use `loop --repair` and preserve every iteration.

## Stage matrix

Evaluate the stage that is actually being crossed. Do not mark an artifact ready merely because the file exists.

| Gate | Must be closed before handoff |
| --- | --- |
| `prd_to_trd` | product goal, scope/non-scope, user scenarios, observable acceptance, relevant NFRs, edge/failure behavior, permissions, dependencies, and product decisions |
| `trd_to_plan` | architecture ownership, module boundaries, interfaces, data/state, migration/compatibility, failure/retry/concurrency, security, observability, testing, rollback, and technical decisions |
| `plan_to_build` | approved canonical plan, stable plan ID, base commit, current plan SHA, DAG/dependencies, write ownership, allowed paths, acceptance IDs, verification commands, and Task Pack linkage |
| `implementation_to_verify` | changed-file scope, implementation-to-plan traceability, unit acceptance evidence, known deviations, and residual risks |
| `verify_to_release` | candidate identity, quality-gate evidence, smoke checks, approvals, runbook, rollback path, observation window, and release risks |

## Core workflow

1. Identify the feature, current stage, target gate, owner, and whether repair is authorized.
2. Locate the canonical source artifacts. Read the complete relevant PRD, TRD, plan, Task Pack, implementation diff, or verification result; do not rely on summaries alone.
3. Record each source artifact as `{name, uri, sha256}`. A changed source hash invalidates the previous readiness result and all downstream conclusions.
4. Build a traceability table. Every material requirement needs a design/plan/acceptance destination appropriate to the current gate. A missing destination is a finding, not an assumption.
5. Check contradictions, unresolved decisions, unsupported assumptions, missing failure paths, and evidence gaps. Separate facts, inference, and open questions.
6. Assign stable issue IDs in the form `DR-<AREA>-<NNN>`. Reuse an existing ID when the same issue remains; mark it `resolved`, `accepted_risk`, or `regressed` instead of deleting it.
7. Write the assessment with `status: ready` only when every finding is `resolved` or explicitly `accepted_risk`, no blocker is active, and the next owner/action is clear. Otherwise write `status: blocked` with `waiting_on: human` or `external` where appropriate.

The report should normally be `docs/reviews/<feature>-readiness.yaml` when document artifacts are enabled. For an agent-brain plan-linked Build, use the agent-brain readiness-report protocol and include its SHA-256 in the Task Pack `source_artifacts` and readiness fields.

## Loop semantics

The loop is a controlled convergence process, not repeated prompting:

```text
read all inputs
  → assess and assign stable issue IDs
  → if ready: stop
  → if blocked by a human/external decision: stop and escalate
  → if repair authorized: make the smallest source-artifact repair
  → recompute every affected source hash
  → reassess the complete gate, including previously passing checks
```

Stop with `blocked` when any of these occurs:

- the source artifact did not change after a proposed repair;
- the same issue regressed or the issue set repeats without progress;
- a business, security, compatibility, or release decision belongs to a human;
- required credentials, environment, external service, or evidence are unavailable;
- the explicit iteration/time/token budget is exhausted.

Never “repair” by weakening an acceptance criterion, deleting a finding, changing the target stage, or inventing evidence. If a risk is consciously accepted, record the decision owner, reason, scope, and expiry/revisit condition.

## Findings and evidence contract

Each finding should contain:

```yaml
id: DR-TRD-001
severity: blocker       # blocker | warning | info
status: open            # open | in_progress | resolved | accepted_risk | blocked | regressed
title: "Retry owner is not defined"
evidence: "TRD section 6 describes retry behavior but names no owner"
next_action: "Ask the technical owner to choose scheduler or worker ownership"
```

Use deterministic evidence whenever possible: file/section references, source hashes, test commands, diff scope, API/schema inspection, or deployment observations. AI judgment can identify a risk or propose a repair, but it cannot substitute for a command result, artifact identity, or human approval.

## Handoff rules

- PRD authors run `gate --stage prd_to_trd` before invoking `$write-trd`.
- TRD authors run `gate --stage trd_to_plan` before invoking `$write-execution-plan`.
- Plan authors run `gate --stage plan_to_build` before invoking agent-brain or `$implement-plan`.
- Implementation and release owners use the later gates to prevent unverified work from being treated as complete.
- A blocked report is a valid output. Return the exact issue IDs, missing evidence, owner, and next action; do not hand off as if the stage passed.

When agent-brain is in use, its Task Pack remains the outer scope contract and this report is the readiness input. Do not create a second acceptance truth in the skill. The canonical execution plan remains the sequencing truth.

## Output format

Return a concise summary plus the durable report path:

```text
status: ready | blocked
stage: <gate>
iteration: <n>
source_artifacts: <paths and SHA-256>
resolved_or_accepted: <issue IDs>
open_blockers: <issue IDs and evidence>
traceability: <covered / missing counts>
next_action: <proceed, repair, request_human, or wait_external>
report: <path>
```

For `ready`, state exactly what downstream handoff is now allowed. For `blocked`, state what must change and who must decide it. Keep the full finding list in the report rather than hiding it in chat.
