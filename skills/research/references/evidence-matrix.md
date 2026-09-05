# Evidence Matrix

Use one row per material claim or decision input. Split a claim when different parts rely on different sources or confidence levels.

| Field | Required content |
| --- | --- |
| Evidence ID | Stable ID such as `E001`. |
| Question | Research question this evidence informs. |
| Claim | A precise factual statement; avoid combining fact and recommendation. |
| Source | Title and URL, file path, interview, query, log, or system observation. |
| Source type | `primary`, `secondary`, or `internal-observation`. |
| Publisher / owner | Organization, team, system, or person responsible for the source. |
| Published / observed | Date the source was published, updated, or observed. |
| Accessed | Date the evidence was checked. |
| Applicability | Product version, geography, user segment, scale, environment, or other boundary. |
| Supports / contradicts | Which hypothesis, requirement, or option it supports or contradicts. |
| Confidence | `high`, `medium`, or `low`. |
| Limitations | Missing context, bias, staleness, ambiguity, conflict, or validation gap. |

## Source Quality Rubric

Assess quality using these dimensions rather than source popularity:

- Authority: Is the source responsible for the product, standard, system, policy, or original research?
- Directness: Does it directly support the claim, or is the conclusion inferred?
- Recency: Is it current enough for the decision and named product version?
- Applicability: Does it match the target geography, scale, workflow, and environment?
- Independence: Is corroboration independent, or are multiple pages repeating the same origin?
- Reproducibility: Can the observation, calculation, or system behavior be checked again?

## Confidence Assignment

- `high`: the claim is direct, current, applicable, and reproducible, normally from primary evidence or multiple independent strong sources.
- `medium`: the claim is credible but indirect, only partly applicable, or dependent on explicit assumptions.
- `low`: evidence is incomplete, conflicting, stale, anecdotal, or mainly inferred.

Never raise confidence merely because several sources copy the same underlying claim.
