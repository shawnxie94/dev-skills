---
name: delivery-estimation
description: Estimate delivery effort in person-months from a frozen requirement packet or settled scope. Two modes — `review` (default), one independent sealed PERT estimate（独立估时、人月估算、交付估时、交叉估时）; `synthesis`, consolidate 3+ sealed estimates into a consensus report（综合估时、估时评审、估时汇总、离散度分析）.
---

# Delivery Estimation

Route the request to one mode, load only that mode's reference, and produce only that mode's artifact.

## Mode Selection

| Mode | Use When | Do Not Use When | Reference |
|---|---|---|---|
| `review` | One reviewer estimates one frozen packet; independent cross-model estimates are wanted | Any other reviewer's estimate or a target budget is visible; results are being compared | [references/review.md](references/review.md) |
| `synthesis` | Three or more sealed review-mode estimates exist for the same packet and a Lead must compare them | Fewer than three sealed comparable estimates exist; someone still needs a first-pass estimate | [references/synthesis.md](references/synthesis.md) |

Decision rules:

- Default to `review`. A reviewer must never open `references/synthesis.md`; the experimental variable is the reviewer model or runtime, not the standard.
- Enter `synthesis` only after every reviewer has finished a sealed first pass. If fewer than three comparable estimates exist, report `synthesis_blocked` instead of inventing consensus.
- Never run both modes for the same role in one turn.

## Shared Rules (both modes)

- Estimate or compare only against the same frozen packet: identical `packet_id`, `packet_hash` (`sha256:<hex>`), `rubric_version: 2.0`, `unit: person_months`, and `working_days_per_person_month` (default 20).
- Preserve frozen work item IDs and each item's `delivery_strategy` (`reuse`, `extend`, `custom`, `not_applicable`); never rename, add, split, or re-strategize them inside this skill.
- Reuse first: `custom` is valid only with an explicit self-development requirement or an approved custom-build decision; include the integration, verification, upgrade, and operating cost of reused components in the estimate.
- Scope gaps are reported, not absorbed: missing or unfreezable work goes to `scope_gaps` and back to `$research` (deep mode) for a packet revision, never into a padded pessimistic value.

## Artifact Rules

- `review` → one machine-validatable estimate JSON validated by `scripts/validate_estimate.py`, plus a short Decision Card on managed platforms. Do not paste full per-item tables into chat.
- `synthesis` → one comparison JSON from `scripts/aggregate_estimates.py` plus one consensus report from [references/consensus-report-template.md](references/consensus-report-template.md), plus a short Decision Card.
- One canonical artifact per mode; do not emit duplicate summaries of the same numbers.

Document artifact mode: check `.agent/config.toml`, falling back to `.dev-skills/config.toml` only when the former does not exist. When `[document_artifacts] enabled = true`, write artifacts to `docs/estimates/` (or `document_artifacts.paths.delivery_estimates`) with stable filenames and metadata frontmatter, and keep the chat reply to path plus summary; otherwise return artifacts in chat or as attachments.

## Handoff Map

- `review` → after all first passes are sealed, the Research Lead runs `$delivery-estimation` in `synthesis` mode.
- `synthesis` → material scope gaps: back to `$research` (deep mode) to revise and re-freeze the packet, then rerun all reviewers; a risky unknown dominates the range: execution-delivery (plan mode) as a risk-first spike after solution scope settles; accepted estimate: a planning input for roadmap, staffing, or execution planning.
- Packet hash, rubric version, or work-item set mismatch: reject the set and rerun every reviewer on one frozen packet; never average across versions.
