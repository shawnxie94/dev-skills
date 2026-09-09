# Research Brief (brief mode)

Mode reference for the `$research` skill. Read this file only after the router selects `brief` mode: early ideas, direction exploration, industry practice, blind spots, and low-cost reversible decisions.

The goal is not to produce a final implementation plan; the goal is to expand the problem space and create high-quality inputs for later requirements analysis, technical design, or execution planning.

## Core Principles

- Reframe before answering. Clarify what problem the idea is trying to solve and which assumptions are currently unverified.
- Expand the user's thinking. Add relevant technologies, industry patterns, alternatives, risks, constraints, and failure modes the user may not have named.
- Separate evidence from inference. Clearly distinguish confirmed facts, common practices, plausible inferences, and open questions.
- Prefer decision-useful synthesis over source dumping. Convert research into options, tradeoffs, evaluation criteria, and next experiments.
- Apply the reuse-first rule from the router when comparing options.
- Keep the depth proportional. Use a light pass for simple questions and a deeper pass for cross-domain, high-cost, or high-risk decisions.

## Verification Rules

Research often depends on current information. Browse or otherwise verify with current sources when the answer involves recent technology, APIs, model capabilities, pricing, standards, regulations, vendor products, security posture, open-source project status, or industry adoption.

When verifying:

- Prefer primary sources: official documentation, standards, research papers, reputable project repositories, release notes, and vendor docs.
- Use secondary sources only to discover leads or collect practitioner experience, not as the sole basis for important claims.
- Cite the sources used.
- Avoid presenting unverified memory or assumptions as current fact.

If current verification is not available or not performed, say so and mark the result as based on existing knowledge.

## Research Workflow

1. Reframe the idea.
   - Restate the user's rough idea as a clearer research question.
   - Identify the likely goal, users, context, constraints, and implicit assumptions.

2. Generate research questions.
   - Create 5-10 targeted questions that would reduce uncertainty.
   - Cover technology, product fit, data, security, operations, cost, integration, and maturity when relevant.

3. Gather evidence.
   - Decide whether current-source verification is required.
   - Search or inspect sources according to the verification rules.
   - Track which claims are confirmed and which are inferred.

4. Synthesize patterns and alternatives.
   - Identify common industry practices and mature implementation patterns.
   - Compare viable options, including build-vs-buy, API-vs-self-hosted, open-source-vs-proprietary, or manual-vs-automated paths when relevant.
   - Explain where each option fits and where it fails.

5. Surface blind spots.
   - Look for missing requirements, edge cases, hidden costs, operational burden, compliance issues, data dependencies, scaling limits, evaluation gaps, and failure modes.

6. Produce design inputs.
   - Turn the research into decision criteria, recommended next steps, PoC ideas, and questions to confirm before design or implementation.

## Blind Spot Checklist

Use the relevant parts of this checklist:

- Problem fit: real user need, frequency, severity, existing workaround, success metric.
- Users and workflow: roles, permissions, handoffs, failure handling, review/approval needs.
- Data: availability, quality, ownership, freshness, privacy, retention, lineage.
- Technical path: architecture, integration points, APIs, SDKs, open-source options, hosting model.
- Security and compliance: auth, secrets, PII, audit trail, policy, legal or regulatory constraints.
- Reliability and operations: monitoring, alerting, rollback, retries, rate limits, degradation.
- Cost and maintainability: build cost, runtime cost, vendor lock-in, team skills, upgrade path.
- Evaluation: benchmarks, acceptance criteria, ground truth, test data, human review.
- Edge cases: abuse, adversarial input, empty states, partial failure, concurrency, migration.

## Handoff Rules

- If the question becomes a formal, multi-source requirement investigation with business flows, system boundaries, evidence traceability, or estimation inputs, escalate to this skill's `deep` mode using the escalation signals in the router.
- If the idea is ready to become product requirements, hand off to `write-prd`.
- If the user only needs technical options or architecture inputs, hand off to `write-trd`.
- If the research exposes a concrete change with unclear blast radius, hand off to `codebase-analysis` (impact mode).

## Delegated Research And Context Offload

If an external squad, managed-agent platform, issue workflow, or lead has already assigned the research scope, execute that scope directly. Do not recursively create subagents or redistribute work unless the assignment explicitly grants orchestration responsibility. When you run as the main agent on a direct user request, use `$subagent-orchestration` when delegation is useful; the restriction above applies when you are already an assigned executor.

Delegate broad or context-heavy research when it involves many sources, long
pages/PDFs, repeated extraction, web validation, or independent evidence review.
Use the logical `researcher` role for collection and first synthesis, then
`evidence-auditor` for important claims. Keep prompts minimal and do not reveal
an expected answer.

Common splits:

- Technology paths and architecture options.
- Industry practices, mature products, and open-source examples.
- Risks, blind spots, and evaluation criteria.
- Source collection versus claim/citation verification.

Require bounded claims, citations, uncertainty, and artifact references. Prefer
file-only or structured child output when the report is large. The main agent
must synthesize results, resolve conflicts, cite evidence, and avoid copying raw
subagent output blindly.

## Output Format

Answer in the user's language unless they request otherwise. Use this structure when practical:

```markdown
## Idea Reframe

<Clear restatement of the idea and the problem it may solve>

## Key Assumptions

<Implicit assumptions and what needs confirmation>

## Research Questions

1. <Question>
2. <Question>
3. <Question>

## Relevant Practices and Technologies

<Current or established practices, with sources when verified>

## Blind Spots

<Important risks, missing requirements, edge cases, and hidden costs>

## Options

| Option | Fits When | Advantages | Risks |
|---|---|---|---|
| <Option> | <Context> | <Pros> | <Risks> |

## Design Inputs

<Constraints, criteria, and context that should feed later requirements or technical design>

## Next Steps

<PoC, further research, requirements analysis, technical design, or decision points>
```

For small requests, keep the same logic but compress the output.
