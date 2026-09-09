---
name: research
description: Turn rough ideas or formal requirements into research inputs before requirements analysis, technical design, or delivery estimation. `brief` (default) explores early ideas, industry practice, blind spots, and low-cost reversible decisions; `deep` freezes a decision-ready research packet with traceable evidence for formal estimation. Use for 调研、研究一下、摸底、找盲点、深度需求调研、需求调研包、估时输入.
---

# Research

Route the request to one mode, load only that mode's reference, and produce only that mode's canonical artifact.

## Mode Selection

| Mode | Use When | Do Not Use When | Reference |
|---|---|---|---|
| `brief` | Early idea, direction exploration, industry practice, blind spots, low-cost reversible decision, no frozen scope needed | The output must feed formal estimation or a frozen requirement packet | [references/brief.md](references/brief.md) |
| `deep` | Cross-business-workflow or cross-system requirement, integrations, unfamiliar domains, compliance, material delivery risk, or the output must feed formal estimation or PRD/TRD authoring | Quick background scan or low-cost reversible decision | [references/deep.md](references/deep.md) |

Decision rules:

- Default to `brief`. Escalate to `deep` only on the explicit signals in the table above; do not upgrade a lightweight question into formal research.
- If a `brief` run surfaces cross-system, compliance, or estimation-boundary evidence, say so and let the user confirm before escalating to `deep`.
- If a `deep` request turns out to be a raw idea with no identifiable decision or scope, drop to `brief` first.
- Never load both mode references in the same turn.

## Shared Rules (both modes)

- Separate confirmed facts, common practices, plausible inferences, and open questions.
- Verify volatile claims against current primary sources; cite what was used and mark unverified results as based on existing knowledge.
- Search for counter-evidence, not only supporting examples.
- Prefer mature internal components, managed services, official SDKs/libraries, and maintained open-source options before proposing custom development; raise an explicit decision instead of silently recommending a custom build.
- Keep depth proportional to decision cost.
- One canonical artifact per mode: `brief` produces a research brief in chat (or the configured document-artifact path); `deep` produces one Requirement Research Packet plus a short Decision Card. Do not emit duplicate summaries of the same facts.

## Delegated Research

When source material, extraction output, or verification logs are large enough to
threaten the coordinator's context, use `$subagent-orchestration` to delegate a
`researcher` or `evidence-auditor`. The child returns bounded claims, citations,
uncertainties, and artifact references; the coordinating research run remains
responsible for source reconciliation and the final brief/packet.

Use `fresh` context for independent research and audit. Prefer durable or
file-only output for large reports. Do not paste raw source dumps or complete
child transcripts into the canonical research artifact.

## Handoff Map

- `brief` → product scope is ready: `$write-prd`; technical options only: `$write-trd`; concrete change with unclear blast radius: `codebase-analysis` (impact).
- `brief` → broad/context-heavy evidence collection: `$subagent-orchestration` with `researcher` and, when claims matter, `evidence-auditor`.
- `brief` → formal multi-source investigation needed: escalate to `deep` mode in this skill.
- `deep` → product scope and acceptance intent ready: `$write-prd`; technical direction needed: `$write-trd`; frozen estimation-ready packet: `delivery-estimation` (review mode, one reviewer per run).
- `deep` → existing-system blast radius still unclear: `codebase-analysis` (orientation, then impact in a separate step).

When an external squad, managed-agent platform, or lead has already assigned the research scope, execute that scope directly and follow the orchestration boundary rules in the selected mode reference.
