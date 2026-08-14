---
name: synthesize-delivery-estimates
description: Compare three or more sealed person-month delivery estimates produced independently from the same frozen requirement packet and shared rubric. Use when a Research Lead must validate unit and mature-component strategy consistency, calculate per-work-item medians and ranges, detect material divergence, identify likely assumption or scope causes, produce a consensus review report, or uses Chinese requests such as 综合估时, 估时评审, 估时汇总, 离散度分析. Do not create a fourth estimate or silently average incompatible inputs.
---

# Synthesize Delivery Estimates

Use this skill only after three or more Estimation Reviewers have completed sealed first-pass outputs using `delivery-estimation-standard`. The Research Lead evaluates consistency, divergence, assumptions, and confidence; the lead does not produce another independent estimate.

## Core Rules

- Preserve every original estimate unchanged.
- Validate structural and arithmetic correctness before comparison.
- Compare only estimates with the same `packet_id`, `packet_hash`, `rubric_version`, `unit`, `working_days_per_person_month`, and frozen work item set.
- Use the median as a robust comparison center, not as automatic truth.
- Flag meaningful divergence and investigate its cause at work-item level.
- Distinguish scope disagreement, assumption disagreement, model reasoning variance, and arithmetic error.
- Do not hide disagreement by averaging totals or selecting the preferred deadline.

## Inputs

Require:

- Three or more sealed estimate JSON files.
- The exact frozen Requirement Research Packet matching `packet_hash`.
- The estimation rubric version used by all reviewers.
- Reviewer/model identities and any declared runtime differences.

Reject comparison when reviewer IDs are duplicated, hashes, rubric versions, person-month definitions, delivery strategies, reusable components, or work item sets differ. If the packet changed, rerun all reviewers against the new frozen version.

## Workflow

### 1. Validate each estimate

Run the validator from `delivery-estimation-standard` against each file:

```bash
python3 <delivery-estimation-standard-skill-dir>/scripts/validate_estimate.py <estimate.json>
```

Do not aggregate invalid estimates. Ask the originating reviewer to correct arithmetic or schema errors without seeing the other reviewers' estimates.

### 2. Generate deterministic comparison data

Run:

```bash
python3 <synthesize-delivery-estimates-skill-dir>/scripts/aggregate_estimates.py estimate-a.json estimate-b.json estimate-c.json --output comparison.json
```

The default divergence threshold is 30%. Override it only when the Research Lead records a reason:

```bash
python3 <synthesize-delivery-estimates-skill-dir>/scripts/aggregate_estimates.py estimate-*.json --threshold 25
```

For each work item and total metric, the script reports reviewer values, median, minimum, maximum, and:

```text
divergence_pct = (maximum - minimum) / median * 100
```

If the median is zero while any value is non-zero, divergence is undefined and review is always required.

### 3. Review divergence from the bottom up

Start with flagged work items, then inspect totals and durations. For each flagged item compare:

- O/M/P shape and confidence.
- Assumptions and uncertainty drivers.
- Interpretation of acceptance signals and non-functional requirements.
- Dependency, role, team-capacity, and parallelism assumptions.
- Reuse, extension, or custom-build assumptions and whether integration effort was included.
- Evidence gaps or missing scope reported in `scope_gaps`.

Do not diagnose disagreement from `total_expected` alone; different item-level errors can cancel out.

### 4. Classify the resolution path

- `calculation_error`: correct the originating estimate, preserving an audit trail.
- `packet_mismatch`: reject the set and rerun all reviewers on one frozen packet.
- `scope_gap`: return the packet to `requirement-deep-research`, revise, re-freeze, and rerun all reviewers.
- `assumption_mismatch`: Research Lead chooses or clarifies an assumption, then requests a focused re-review from all affected reviewers.
- `reuse_strategy_mismatch`: return to the Requirement & Solution Analyst to freeze the mature component or justified custom-build decision, then rerun all reviewers.
- `legitimate_uncertainty`: keep the range visible and plan a spike, discovery task, or explicit reserve decision.
- `model_variance`: preserve the distribution when inputs and reasoning are otherwise aligned; do not force false consensus.

### 5. Produce the lead report

Use [consensus-report-template.md](references/consensus-report-template.md). The report must include:

- Comparability checks and reviewer/model matrix.
- Work-item medians, ranges, divergence, and flagged items.
- Aggregate effort and duration comparison.
- Root cause and resolution for each material disagreement.
- Scope gaps and assumptions requiring owner decisions.
- Confidence and a recommended planning range or follow-up action.

A planning range is a Lead decision based on the reviewed evidence. Label it as a synthesis decision, not a fourth reviewer estimate.

## Output Format

Produce:

1. Machine comparison data for the independent estimates.
2. A Research Lead consensus report using [consensus-report-template.md](references/consensus-report-template.md).

The report must include:

- Comparability checks and reviewer/model matrix.
- Work-item medians, ranges, divergence, and flagged items.
- Aggregate effort and duration comparison.
- Root cause and resolution path for each material disagreement.
- Scope gaps and assumptions requiring owner decisions.
- Confidence plus a recommended planning range or follow-up action, labeled as a synthesis decision rather than a fourth estimate.

## Document Artifact Mode

If `.agent/config.toml` exists, use its `[document_artifacts]` section. Only
when it does not exist should standalone dev-skills read
`.dev-skills/config.toml`. When enabled, write machine comparison JSON and the
Lead report to `docs/estimates/` or `document_artifacts.paths.delivery_estimates`
when configured. Suggested names:

- `docs/estimates/<packet-id>-comparison.json`
- `docs/estimates/<packet-id>-consensus.md`

Otherwise, return the concise report in chat and preserve comparison JSON when the user requests an artifact.

## Publish Layering (Multica / issue threads)

Keep comparison JSON / consensus report files as artifacts. The issue comment should be a short **Decision Card**, not a full work-item divergence dump.

```markdown
## Decision Card
- status: synthesized | synthesis_blocked | requires_packet_revision
- packet_id / packet_hash:
- reviewer_count / synthesis_eligible:
- planning range (total_expected min–max or median band):
- schedule range (P50/P80 band) if comparable:
- divergence nature: calibration skew | scope/assumption conflict | mixed
- waiting_on: none | third_reviewer | focused_rereview | human_decision | packet_revision
- choose: (explicit human options when blocked)
- artifacts: <comparison/consensus filenames>
```

Put per-item median/min/max/divergence tables in the comparison artifact. Mention only the material divergence drivers in the Decision Card.

If fewer than three sealed comparable estimates are available, say `synthesis_blocked` / not eligible, give a descriptive range only if useful, and do **not** invent consensus.

## Handoff Rules

- If material scope gaps exist, hand back to `requirement-deep-research` or the Requirement & Solution Analyst.
- If a risky unknown dominates the range, hand to `write-execution-plan` as a risk-first spike only after solution scope is settled.
- If the estimate is accepted, use it as a planning input for roadmap, staffing, or execution planning; do not rewrite requirements to fit the number.
- Preserve unresolved disagreement and confidence in downstream handoff.
