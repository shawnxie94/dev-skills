#!/usr/bin/env python3
"""Validate a delivery-estimation-standard JSON result."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


CONFIDENCE = {"low", "medium", "high"}
DELIVERY_STRATEGIES = {"reuse", "extend", "custom", "not_applicable"}
HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
TOP_LEVEL_FIELDS = {
    "estimate_id",
    "packet_id",
    "packet_hash",
    "rubric_version",
    "reviewer_id",
    "model",
    "generated_at",
    "unit",
    "working_days_per_person_month",
    "work_items",
    "role_totals",
    "total_expected",
    "duration_p50_months",
    "duration_p80_months",
    "critical_path",
    "recommended_team",
    "assumptions",
    "excluded_work",
    "scope_gaps",
    "uncertainty_drivers",
    "confidence",
}
WORK_ITEM_FIELDS = {
    "id",
    "name",
    "role",
    "optimistic",
    "most_likely",
    "pessimistic",
    "expected",
    "depends_on",
    "parallelizable_with",
    "delivery_strategy",
    "reused_components",
    "custom_build_justification",
    "confidence",
    "assumptions",
}


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def close(actual: float, expected: float, tolerance: float) -> bool:
    return math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance)


def require_nonempty_string(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path} must be a non-empty string")


def require_string_list(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{path} must be an array of strings")


def validate(data: Any, tolerance: float) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be a JSON object"]

    missing = sorted(TOP_LEVEL_FIELDS - data.keys())
    if missing:
        errors.append(f"missing top-level fields: {', '.join(missing)}")

    for field in ("estimate_id", "packet_id", "rubric_version", "reviewer_id", "model", "generated_at"):
        require_nonempty_string(data.get(field), field, errors)

    packet_hash = data.get("packet_hash")
    if not isinstance(packet_hash, str) or not HASH_PATTERN.fullmatch(packet_hash):
        errors.append("packet_hash must match sha256:<64 lowercase hex characters>")
    if data.get("rubric_version") != "2.0":
        errors.append("rubric_version must be '2.0'")
    if data.get("unit") != "person_months":
        errors.append("unit must be 'person_months'")
    working_days = data.get("working_days_per_person_month")
    if not is_number(working_days) or working_days <= 0:
        errors.append("working_days_per_person_month must be a finite positive number")
    if data.get("confidence") not in CONFIDENCE:
        errors.append("confidence must be low, medium, or high")

    for field in ("assumptions", "excluded_work", "scope_gaps", "uncertainty_drivers"):
        require_string_list(data.get(field), field, errors)

    work_items = data.get("work_items")
    if not isinstance(work_items, list) or not work_items:
        errors.append("work_items must be a non-empty array")
        work_items = []

    ids: list[str] = []
    role_sums: defaultdict[str, float] = defaultdict(float)
    total = 0.0
    references: list[tuple[str, str, str]] = []

    for index, item in enumerate(work_items):
        path = f"work_items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} must be an object")
            continue
        missing_item = sorted(WORK_ITEM_FIELDS - item.keys())
        if missing_item:
            errors.append(f"{path} missing fields: {', '.join(missing_item)}")

        for field in ("id", "name", "role"):
            require_nonempty_string(item.get(field), f"{path}.{field}", errors)
        item_id = item.get("id")
        if isinstance(item_id, str) and item_id:
            ids.append(item_id)

        values: dict[str, float] = {}
        for field in ("optimistic", "most_likely", "pessimistic", "expected"):
            value = item.get(field)
            if not is_number(value) or value < 0:
                errors.append(f"{path}.{field} must be a finite non-negative number")
            else:
                values[field] = float(value)

        if all(key in values for key in ("optimistic", "most_likely", "pessimistic")):
            o = values["optimistic"]
            m = values["most_likely"]
            p = values["pessimistic"]
            if not o <= m <= p:
                errors.append(f"{path} must satisfy optimistic <= most_likely <= pessimistic")
            pert = (o + 4 * m + p) / 6
            if "expected" in values and not close(values["expected"], pert, tolerance):
                errors.append(f"{path}.expected must equal PERT {pert:.4f}")

        role = item.get("role")
        if isinstance(role, str) and role and "expected" in values:
            role_sums[role] += values["expected"]
            total += values["expected"]

        if item.get("confidence") not in CONFIDENCE:
            errors.append(f"{path}.confidence must be low, medium, or high")
        strategy = item.get("delivery_strategy")
        if strategy not in DELIVERY_STRATEGIES:
            errors.append(
                f"{path}.delivery_strategy must be reuse, extend, custom, or not_applicable"
            )
        components = item.get("reused_components")
        require_string_list(components, f"{path}.reused_components", errors)
        if strategy in {"reuse", "extend"} and isinstance(components, list):
            if not components or any(not component.strip() for component in components):
                errors.append(
                    f"{path}.reused_components must identify a mature component for {strategy}"
                )
        justification = item.get("custom_build_justification")
        if not isinstance(justification, str):
            errors.append(f"{path}.custom_build_justification must be a string")
        elif strategy == "custom" and not justification.strip():
            errors.append(f"{path}.custom_build_justification is required for custom delivery")
        require_string_list(item.get("assumptions"), f"{path}.assumptions", errors)
        for field in ("depends_on", "parallelizable_with"):
            refs = item.get(field)
            require_string_list(refs, f"{path}.{field}", errors)
            if isinstance(refs, list):
                for ref in refs:
                    if isinstance(ref, str) and isinstance(item_id, str):
                        references.append((path, field, ref))
                        if ref == item_id:
                            errors.append(f"{path}.{field} cannot reference itself")

    duplicate_ids = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
    if duplicate_ids:
        errors.append(f"work item IDs must be unique: {', '.join(duplicate_ids)}")
    known_ids = set(ids)
    for path, field, ref in references:
        if ref not in known_ids:
            errors.append(f"{path}.{field} references unknown work item {ref}")

    role_totals = data.get("role_totals")
    if not isinstance(role_totals, dict):
        errors.append("role_totals must be an object")
    else:
        if set(role_totals) != set(role_sums):
            errors.append("role_totals keys must exactly match work item roles")
        for role, expected_sum in role_sums.items():
            value = role_totals.get(role)
            if not is_number(value) or value < 0:
                errors.append(f"role_totals.{role} must be a finite non-negative number")
            elif not close(float(value), expected_sum, tolerance):
                errors.append(f"role_totals.{role} must equal {expected_sum:.4f}")

    total_expected = data.get("total_expected")
    if not is_number(total_expected) or total_expected < 0:
        errors.append("total_expected must be a finite non-negative number")
    elif not close(float(total_expected), total, tolerance):
        errors.append(f"total_expected must equal {total:.4f}")

    durations: dict[str, float] = {}
    for field in ("duration_p50_months", "duration_p80_months"):
        value = data.get(field)
        if not is_number(value) or value < 0:
            errors.append(f"{field} must be a finite non-negative number")
        else:
            durations[field] = float(value)
    if all(field in durations for field in ("duration_p50_months", "duration_p80_months")):
        if durations["duration_p80_months"] < durations["duration_p50_months"]:
            errors.append(
                "duration_p80_months must be greater than or equal to duration_p50_months"
            )

    critical_path = data.get("critical_path")
    require_string_list(critical_path, "critical_path", errors)
    if isinstance(critical_path, list):
        for item_id in critical_path:
            if isinstance(item_id, str) and item_id not in known_ids:
                errors.append(f"critical_path references unknown work item {item_id}")

    team = data.get("recommended_team")
    if not isinstance(team, dict):
        errors.append("recommended_team must be an object")
    else:
        for role, count in team.items():
            if not isinstance(role, str) or not role:
                errors.append("recommended_team keys must be non-empty role names")
            if not is_number(count) or count < 0:
                errors.append(f"recommended_team.{role} must be a finite non-negative number")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("estimate", type=Path, help="Path to estimate JSON")
    parser.add_argument("--tolerance", type=float, default=1e-3, help="Numeric comparison tolerance")
    args = parser.parse_args()

    try:
        data = json.loads(args.estimate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read estimate: {exc}", file=sys.stderr)
        return 2

    errors = validate(data, args.tolerance)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"VALID: {args.estimate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
