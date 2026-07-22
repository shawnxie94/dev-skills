---
name: delivery-estimation-standard
description: Independently estimate a frozen delivery scope in person-months using a shared work-item rubric, optimistic/most-likely/pessimistic values, PERT expected effort, mature-component reuse assumptions, role totals, schedule assumptions, uncertainty, and machine-validatable JSON. Use when one or more Estimation Reviewers must assess the same Requirement Research Packet or settled scope, especially across different models for cross-validation, or when the user asks in Chinese for 独立估时, 人月估算, 交付估时, 交叉估时. Enforce identical inputs and rules, first-pass independence, stable work item IDs, explicit assumptions, reuse-before-custom-build decisions, and reproducible output; do not synthesize other reviewers' estimates.
---

# Delivery Estimation Standard

Use this skill for each independent Estimation Reviewer. Every reviewer must receive the same frozen input, rubric version, prompt contract, and output schema. The intended experimental variable is the reviewer model or runtime, not the evaluation standard.

This skill produces one estimate. It does not compare reviewers, negotiate a consensus, or read another reviewer's numbers during the first pass.

## Independence Protocol

Before estimating, confirm:

- The input has a stable `packet_id` and a `packet_hash` in `sha256:<hex>` form.
- The rubric version is `2.0`.
- The input declares the same `working_days_per_person_month` for every reviewer; use `20` unless the organization has frozen another standard.
- The frozen work item set and IDs are identical for all reviewers.
- No other reviewer's estimate, total, anchor, target budget, desired deadline, or consensus is visible.
- The reviewer identity and model/runtime will be recorded in the output.

If any condition fails, return `not_estimable` with the reason instead of inventing a comparable result. After all first-pass estimates are sealed, the Research Lead may request a focused re-review of flagged items, but must preserve the original result.

## Estimation Boundary

Estimate delivery effort in `person_months`. One person-month means one qualified contributor working full-time for the declared `working_days_per_person_month`; the default is 20 focused working days. Use decimals for smaller work items, for example `0.25` person-month.

Include applicable work across:

- Requirement clarification and solution detail needed to implement the frozen scope.
- UX, API, data, frontend, backend, integration, migration, and infrastructure work.
- Automated tests, manual verification, security, observability, release, documentation, and operational readiness.
- Coordination intrinsic to the work item when it cannot be separated.

Exclude unless the packet includes them:

- Product discovery outside the frozen requirement.
- Organization-wide process change, hiring, procurement, or unrelated platform modernization.
- General contingency applied as an arbitrary percentage.
- Waiting time that consumes no delivery capacity.

Record excluded work and assumptions explicitly.

## Reuse-First Rule

- Preserve the frozen work item's `delivery_strategy`: `reuse`, `extend`, `custom`, or `not_applicable`.
- Prefer an existing internal component, managed service, official SDK/library, or mature maintained open-source component when it satisfies the requirement and constraints.
- Treat `custom` as valid only when the packet cites an explicit self-development requirement or approved custom-build decision and documents why mature options fail relevant criteria. A Reviewer must not turn an architectural gap into an implicit custom build.
- Include component discovery, evaluation, integration, configuration, adaptation, migration, security review, testing, licensing, upgrades, and operations in the estimate. Reuse is not zero effort.
- If the packet does not freeze a strategy for a component-relevant item, report a `scope_gap`; do not let each Reviewer choose a different architecture.

## Scope Integrity

- Estimate every frozen work item exactly once.
- Do not rename, add, remove, merge, or split frozen work item IDs.
- Preserve the packet's work item name, role, and dependency IDs.
- Preserve its delivery strategy, reused component identifiers, and custom-build justification.
- If important work is missing, add it to `scope_gaps` without assigning effort. The Research Lead must revise and re-freeze the packet, then rerun every reviewer.
- If an item cannot be estimated, state the blocking unknown in `scope_gaps`; do not hide it inside a large pessimistic value.

## Estimation Workflow

### 1. Read the frozen scope

- Identify actors, outcomes, acceptance signals, dependencies, complexity drivers, non-functional requirements, and exclusions.
- Extract assumptions that affect effort or sequence.
- Confirm that each dependency refers to a frozen work item.

### 2. Estimate each work item independently

For every item provide:

- `optimistic` (`O`): credible low effort if named assumptions hold; not a theoretical minimum.
- `most_likely` (`M`): effort under the most plausible implementation path and normal friction.
- `pessimistic` (`P`): credible high effort for identified uncertainty; not an unbounded disaster case.
- `expected`: `(O + 4M + P) / 6`, rounded to four decimal places.
- `confidence`: `high`, `medium`, or `low` based on scope and evidence quality.
- Concrete assumptions and uncertainty drivers.
- The frozen delivery strategy and reusable components that the estimate assumes.

Enforce `0 <= O <= M <= P`. Avoid false precision: use values consistent with the available evidence, then let the script calculate and validate derived totals.

### 3. Calculate effort totals

- Sum expected effort by `role` into `role_totals`.
- Sum all expected effort into `total_expected`.
- Do not reduce person-months because items can run in parallel; parallelism affects duration, not effort.
- Do not add a second hidden contingency after PERT.

### 4. Model calendar duration

- Use dependencies, parallelizable items, team capacity, handoffs, and critical path.
- Provide `duration_p50_months` as the most plausible elapsed duration in planning months.
- Provide `duration_p80_months` as a defensible higher-confidence elapsed duration based on named uncertainty; enforce `p80 >= p50`.
- Record the recommended team by role and the critical-path work item IDs.
- Explain meaningful schedule assumptions in top-level `assumptions`.

Duration is not `total_expected / total_headcount` unless the work is actually parallelizable and the assumed skills are available.

### 5. Self-review for bias

Check for:

- Anchoring to a requested date, budget, or another estimate.
- Omitting testing, integration, migration, security, release, or operations work.
- Counting the same shared work in multiple items.
- Treating unfamiliarity as zero effort or padding every item indiscriminately.
- Confusing effort with elapsed duration.
- Unsupported team parallelism or missing dependency constraints.
- Building a custom component without an explicit requirement or approved decision plus a documented mature-component assessment.
- Treating component reuse as zero work or omitting integration, verification, upgrade, licensing, and operating costs.

### 6. Emit and validate JSON

Follow [estimation-output-schema.md](references/estimation-output-schema.md). Save the result, then run:

```bash
python3 <delivery-estimation-standard-skill-dir>/scripts/validate_estimate.py <estimate.json>
```

Resolve the script path relative to this Skill directory. Resolve all validation errors before handing the estimate to the Research Lead.

## Output Format

Emit machine-validatable estimate JSON that conforms to [estimation-output-schema.md](references/estimation-output-schema.md).

Required shape at minimum:

- Top-level metadata: packet identity, reviewer id/model, rubric version, unit, assumptions.
- Per work item: stable ID, O/M/P effort, expected effort, reuse strategy, roles, notes.
- Aggregate totals: expected effort, role totals, calendar duration p50/p80, critical-path IDs.

Validate before handoff:

```bash
python3 <delivery-estimation-standard-skill-dir>/scripts/validate_estimate.py <estimate.json>
```

## Document Artifact Mode

If `.dev-skills/config.toml` enables `[document_artifacts]`, write the estimate to `docs/estimates/` or `document_artifacts.paths.delivery_estimates` when configured. Use a stable name such as `docs/estimates/<packet-id>-<reviewer-id>.json`.

Otherwise, return schema-conformant JSON in chat unless the user requests a file.

## Handoff Rules

- Hand sealed independent outputs to the Research Lead using `synthesize-delivery-estimates` only after all reviewers finish their first pass.
- If packet hash, rubric version, or work item set differs, do not aggregate; request a clean rerun.
- If `scope_gaps` is non-empty and material, return to `requirement-deep-research` or the Requirement & Solution Analyst to revise the packet.
- Do not average or adjust the estimate to match other reviewers.
