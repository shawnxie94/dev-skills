---
name: requirement-deep-research
description: Conduct formal, multi-source requirement research and produce a decision-ready Requirement Research Packet before PRD, solution design, or delivery estimation. Use when a requirement spans business workflows, system boundaries, integrations, unfamiliar domains, technical options, compliance, or material delivery risk and a lightweight research brief is not enough. Focus on traceable evidence, mature-component reuse before custom development, source quality, counter-evidence, confidence, functional scope, process flows, system decomposition, technical options, risks, and a frozen estimation input without producing effort numbers.
---

# Requirement Deep Research

Use this skill for decision-grade requirement research. The output is a traceable Requirement Research Packet that a Requirement & Solution Analyst, PRD/TRD author, or independent estimation reviewers can consume without repeating discovery.

Do not use this skill for a quick background scan or a low-cost reversible decision; use `research-brief` instead. Do not turn the packet into a PRD, final architecture, implementation plan, or delivery estimate.

## Core Rules

- Reframe the decision before collecting sources.
- Separate stakeholder statements, verified facts, informed inference, and recommendations.
- Prefer current primary sources and record source dates, scope, and limitations.
- Search for counter-evidence and failure cases, not only supporting examples.
- Trace each material conclusion to evidence and assign explicit confidence.
- Define functional scope, workflows, system boundaries, integrations, non-functional concerns, and unresolved questions.
- Prefer mature internal components, managed services, official SDKs/libraries, and maintained open-source components before proposing custom development.
- Produce stable work item IDs for estimation; do not attach person-months, story points, or calendar dates.
- Record unknowns as research gaps or estimation uncertainty drivers instead of silently guessing.

## External Orchestration Boundary

When an external squad, managed-agent platform, issue workflow, or Research Lead has already assigned this research task:

- Execute only the assigned research scope and return the requested packet.
- Do not recursively create internal agents or redistribute the work unless the task explicitly grants orchestration responsibility.
- Preserve the external task's source links, output path, scope, exclusions, and acceptance criteria.
- Report evidence gaps and blocked questions to the orchestrator instead of expanding scope unilaterally.

When no external orchestration exists, parallel research passes are optional only for genuinely broad, separable domains. The lead agent remains responsible for source verification, conflict resolution, and the final packet.

## Required Inputs

Collect what exists; mark missing items explicitly:

- Requirement statement, business objective, target users, and triggering scenarios.
- Known scope, exclusions, constraints, deadline or budget constraints, and stakeholders.
- Existing systems, repositories, workflows, data, integrations, policies, and prior decisions.
- Geographic, regulatory, security, privacy, reliability, and operating constraints.
- The decision this research must enable: PRD, system option, feasibility gate, or estimation.

If the request is still a raw idea with no identifiable decision or scope, run `research-brief` first.

## Workflow

### 1. Frame the research contract

- State the decision to support and the intended consumer.
- Define in-scope and out-of-scope questions.
- List assumptions, unknowns, time sensitivity, and evidence freshness needs.
- Establish completion criteria and the research cutoff date.

### 2. Build the question map

Cover the relevant dimensions:

- Business objective, actors, permissions, value, and measurable outcome.
- Functional capabilities, rules, states, exceptions, approvals, and failure handling.
- Current and target workflows, handoffs, inputs, outputs, and operational ownership.
- System boundaries, integration points, data ownership, and source-of-truth decisions.
- Technical options, existing internal capabilities, mature reusable components, constraints, build-vs-buy, and migration implications.
- Security, privacy, compliance, reliability, observability, scalability, and cost.
- Dependencies, assumptions, risks, open decisions, and estimation uncertainty.

### 3. Plan and gather evidence

- Use primary sources first: stakeholder artifacts, current system evidence, official docs, standards, regulations, vendor docs, repositories, release notes, and original research.
- Use high-quality secondary sources to compare practice or find leads; do not use them as the sole support for high-impact claims.
- Verify volatile claims such as product capabilities, model support, pricing, legal requirements, and project status against current sources.
- Record every material source in the evidence matrix described in [evidence-matrix.md](references/evidence-matrix.md).
- Capture contradicting evidence, applicability limits, and unanswered questions.

### 4. Model the requirement

- Normalize actors, goals, triggers, preconditions, main flow, alternate flows, failures, and outputs.
- Identify capability groups and stable functional points.
- Draw or describe the current and target business flow when sequence matters.
- Propose a lightweight system decomposition: responsibilities, system boundaries, integrations, data ownership, and external dependencies.
- Compare viable technical options using common decision criteria; label recommendations as recommendations, not facts.
- Default to reuse or extension when a mature component meets functional, security, compliance, licensing, operational, performance, cost, and lock-in constraints.
- Recommend custom development only when the requirement explicitly demands it. If evidence shows all mature options fail, raise an open decision and require the decision owner to approve and record an explicit custom-build requirement before freezing the packet.

### 5. Build the frozen estimation input

- Convert the agreed scope into stable IDs such as `W001`, `W002`, and `W003`.
- For each work item, include name, outcome, responsible role or discipline, dependencies, acceptance signal, complexity drivers, known exclusions, and `delivery_strategy` as `reuse`, `extend`, `custom`, or `not_applicable`.
- For `reuse` or `extend`, freeze the component and relevant version/service tier. For `custom`, freeze the explicit requirement or approved decision record plus the evidence-backed rejection reasons for mature alternatives.
- Include discovery, UX, data, integration, migration, testing, security, observability, release, and operational readiness work when relevant.
- Do not add effort or duration values.
- If a material scope gap remains, mark the packet not ready for estimation.

### 6. Challenge and synthesize

- Test the preferred direction against counter-evidence, edge cases, hidden operating cost, vendor lock-in, and failure modes.
- Mark each conclusion `high`, `medium`, or `low` confidence using the evidence rubric.
- Separate blocking decisions from questions that can remain assumptions during estimation.
- State what new evidence would change the recommendation.

### 7. Publish the packet

Use [research-packet-template.md](references/research-packet-template.md). Before handoff:

- Give the packet a stable `packet_id` and version.
- Freeze `rubric_version: 2.0`, `unit: person_months`, and `working_days_per_person_month` for all reviewers; default to 20 working days per person-month unless the organization defines another standard.
- Freeze the exact file or input bundle sent to all estimation reviewers.
- Compute its SHA-256 over the raw frozen bytes and pass it as `packet_hash` in the form `sha256:<hex>`.
- Send every reviewer the same packet bytes, rubric version, instructions, and output schema.
- If the packet changes, create a new hash and rerun all reviewers; do not mix versions.

## Evidence Confidence

Use the detailed fields in [evidence-matrix.md](references/evidence-matrix.md). As a shorthand:

- `high`: directly supported by applicable primary evidence or multiple independent strong sources.
- `medium`: supported but indirect, partially applicable, or dependent on an explicit assumption.
- `low`: weak, conflicting, stale, or largely inferred evidence; further validation is required.

Confidence describes evidence strength, not how strongly the author prefers a conclusion.

## Document Artifact Mode

If `.dev-skills/config.toml` enables `[document_artifacts]`, write the packet to `docs/research/` or `document_artifacts.paths.research` when configured. Use a stable filename such as `docs/research/<requirement-slug>-research.md` and include frontmatter with `id`, `type: requirement_research`, `status`, `version`, `created_at`, `updated_at`, `sources`, and `related`.

Otherwise, return the packet in chat unless the user requests a file.

## Handoff Rules

- Hand a complete packet to `write-prd` when product scope and acceptance intent are ready.
- Hand technical direction and system constraints to `write-trd` when architecture decisions are needed.
- Hand a frozen, estimation-ready packet to independent reviewers using `delivery-estimation-standard`.
- If the research reveals an existing-system blast radius that is still unclear, run `codebase-orientation` and then `change-impact-analysis`.
- Do not call the packet estimation-ready while blocking scope decisions, missing work items, or unverified critical constraints remain.

## Completion Checklist

- The supported decision, scope, exclusions, and research cutoff are explicit.
- Material claims are traceable to sources and distinguish fact from inference.
- Counter-evidence, risks, unknowns, and confidence are visible.
- Actors, functional points, workflows, boundaries, integrations, and technical options are covered.
- Estimation work items have stable IDs and no effort numbers.
- Component-relevant work items have a frozen reuse/extend/custom decision; custom development has explicit justification.
- Packet readiness and remaining gaps are explicit.
