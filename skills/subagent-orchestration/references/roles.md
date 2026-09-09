# Logical Subagent Roles

Roles are stable capability contracts. Runtime agent names, model choices, and
execution modes are resolved separately by the adapter.

## Initial role registry

| Role | Purpose | Write policy | Context default | Output contract |
|---|---|---|---|---|
| `scout` | Map local code, entry points, callers, data flow, and risks | Read-only | `fresh` | Files/line ranges, confirmed facts, risks, start-here handoff |
| `researcher` | Gather external or document evidence | Read-only; may write research artifacts | `fresh` | Claims, sources, evidence quality, uncertainty, artifact references |
| `oracle` | Challenge a plan or decision | Read-only | `fresh` | Alternatives, objections, missing assumptions, recommendation |
| `worker` | Execute an approved mutating goal or plan unit, including bounded installs/configuration | Scoped writes or system-side effects; one writer per ownership boundary | `fresh` or explicit `fork` | Status, changed files/system effects, tests, deviations, blockers, residual risks |
| `reviewer` | Review code, plans, or implementation against a contract | Read-only by default | `fresh` | Findings with severity and evidence, verdict, recommended fixes |
| `evidence-auditor` | Verify claims, citations, and source support | Read-only | `fresh` | Claim/source matrix, support status, contradictions, open gaps |
| `verifier` | Execute acceptance commands and compress proof | No file edits unless explicitly approved | `fresh` | Commands, exit codes, evidence paths, scope, unverified boundaries |

`verifier` is a follow-up role. Prefer the coordinator's acceptance commands or
`reviewer` until verbose validation output creates a demonstrated context or
observability problem.

## Role invariants

- A role cannot widen its own write ownership or choose a sibling's work.
- A worker is a leaf executor and cannot create another subagent unless the
  approved orchestration contract explicitly grants that capability.
- Reviewers and auditors do not become implementers because they find a defect;
  return a repair packet to the coordinator.
- Researcher output must distinguish confirmed evidence, inference, and open
  questions. Do not return source dumps as the primary result.
- Scout output is a handoff, not a second architecture or implementation plan.
- Oracle output challenges the decision; the coordinator remains the decision
  owner.

## Role selection matrix

| Need | Role | Avoid |
|---|---|---|
| Understand an unfamiliar local area | `scout` | Sending the full repository to a worker |
| Collect many web/document sources | `researcher` | Pasting raw pages into the coordinator context |
| Verify an action before execution | `evidence-auditor` | Giving the auditor ownership of the installation/configuration |
| Check whether a decision is sound | `oracle` | Asking the implementer to approve its own plan |
| Modify files under an approved scope | `worker` | Giving write access to scouts/reviewers |
| Find correctness/security/scope defects | `reviewer` | Treating a review as acceptance evidence |
| Validate important research claims | `evidence-auditor` | Trusting a single source or researcher prose |
| Install/configure or perform another bounded mutation | `worker` | Delegating side effects to a read-only role |
| Run long or noisy acceptance checks | `verifier` | Returning complete logs inline |

## Existing profile migration

Runtime-specific profiles may shadow package builtins. During migration, inspect
the resolved profile rather than assuming a package builtin is active. Existing
Pi `planner` profiles may remain as compatibility files, but canonical planning
stays with `$execution-delivery`; `delegate` remains an orchestration mechanism,
not a normal child role.
