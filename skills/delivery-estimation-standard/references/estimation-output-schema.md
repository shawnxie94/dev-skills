# Estimation Output Schema

Emit one JSON object. Use numbers, not strings, for effort and duration fields.

```json
{
  "estimate_id": "EST-001-model-a",
  "packet_id": "REQ-001",
  "packet_hash": "sha256:<64 lowercase hex characters>",
  "rubric_version": "2.0",
  "reviewer_id": "reviewer-model-a",
  "model": "<provider/model/runtime identifier>",
  "generated_at": "YYYY-MM-DD",
  "unit": "person_months",
  "working_days_per_person_month": 20,
  "work_items": [
    {
      "id": "W001",
      "name": "<frozen work item name>",
      "role": "backend",
      "optimistic": 0.1,
      "most_likely": 0.2,
      "pessimistic": 0.4,
      "expected": 0.2167,
      "depends_on": [],
      "parallelizable_with": [],
      "delivery_strategy": "reuse",
      "reused_components": ["<component and version or service tier>"],
      "custom_build_justification": "",
      "confidence": "medium",
      "assumptions": ["<specific assumption>"]
    }
  ],
  "role_totals": {
    "backend": 0.2167
  },
  "total_expected": 0.2167,
  "duration_p50_months": 0.25,
  "duration_p80_months": 0.4,
  "critical_path": ["W001"],
  "recommended_team": {
    "backend": 1
  },
  "assumptions": [],
  "excluded_work": [],
  "scope_gaps": [],
  "uncertainty_drivers": [],
  "confidence": "medium"
}
```

## Required Invariants

- `packet_hash` uses `sha256:<64 lowercase hex characters>` and identifies the exact frozen input.
- `rubric_version` is `2.0`; `reviewer_id` and `model` are non-empty.
- `unit` is `person_months`; `working_days_per_person_month` is a positive number and is identical across Reviewers.
- Work item IDs are unique and match the frozen packet exactly.
- `0 <= optimistic <= most_likely <= pessimistic`.
- `expected` equals `(optimistic + 4 * most_likely + pessimistic) / 6` within rounding tolerance.
- Every dependency, parallel item, and critical-path ID exists in `work_items`; an item cannot depend on or parallelize with itself.
- `delivery_strategy` is `reuse`, `extend`, `custom`, or `not_applicable` and matches the frozen packet.
- `reuse` and `extend` identify at least one mature component. `custom` has a non-empty justification citing an explicit self-development requirement or approved custom-build decision and the mature-option assessment.
- `role_totals` and `total_expected` equal their derived sums.
- `duration_p80_months >= duration_p50_months >= 0`.
- Confidence is one of `low`, `medium`, or `high`.
- `recommended_team` values are non-negative numbers.
- `scope_gaps` contains missing or unestimable scope and receives no effort value.

The deterministic validator checks structural and arithmetic consistency. It cannot determine whether the scope, assumptions, or estimates are substantively correct.
