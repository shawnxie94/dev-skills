#!/usr/bin/env python3
"""Aggregate comparable delivery estimates without manufacturing consensus."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


METRICS = ("total_expected", "duration_p50_months", "duration_p80_months")


def load_estimate(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    data["_source_file"] = str(path)
    return data


def require_number(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def comparison(values_by_reviewer: dict[str, float], threshold: float) -> dict[str, Any]:
    values = list(values_by_reviewer.values())
    center = statistics.median(values)
    minimum = min(values)
    maximum = max(values)
    if center == 0:
        divergence = 0.0 if maximum == 0 else None
        requires_review = maximum != 0
    else:
        divergence = (maximum - minimum) / center * 100
        requires_review = divergence > threshold
    return {
        "values": values_by_reviewer,
        "median": round(center, 4),
        "min": round(minimum, 4),
        "max": round(maximum, 4),
        "divergence_pct": None if divergence is None else round(divergence, 2),
        "requires_review": requires_review,
    }


def ensure_same(estimates: list[dict[str, Any]], field: str) -> Any:
    values = [estimate.get(field) for estimate in estimates]
    if any(value in (None, "") for value in values):
        raise ValueError(f"all estimates must contain {field}")
    if len(set(values)) != 1:
        raise ValueError(f"estimates have different {field} values: {values}")
    return values[0]


def index_work_items(estimate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = estimate.get("work_items")
    source = estimate["_source_file"]
    if not isinstance(items, list) or not items:
        raise ValueError(f"{source}: work_items must be a non-empty array")
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ValueError(f"{source}: every work item must have a non-empty string ID")
        if item["id"] in indexed:
            raise ValueError(f"{source}: duplicate work item ID {item['id']}")
        indexed[item["id"]] = item
    return indexed


def aggregate(estimates: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    if len(estimates) < 3:
        raise ValueError("at least three independent estimates are required")

    packet_id = ensure_same(estimates, "packet_id")
    packet_hash = ensure_same(estimates, "packet_hash")
    rubric_version = ensure_same(estimates, "rubric_version")
    unit = ensure_same(estimates, "unit")
    working_days_per_person_month = ensure_same(estimates, "working_days_per_person_month")

    reviewer_ids = [estimate.get("reviewer_id") for estimate in estimates]
    if any(not isinstance(value, str) or not value for value in reviewer_ids):
        raise ValueError("every estimate must contain a non-empty reviewer_id")
    if len(set(reviewer_ids)) != len(reviewer_ids):
        raise ValueError(f"reviewer_id values must be unique: {reviewer_ids}")

    indexed = [index_work_items(estimate) for estimate in estimates]
    expected_ids = set(indexed[0])
    for estimate, items in zip(estimates[1:], indexed[1:]):
        if set(items) != expected_ids:
            missing = sorted(expected_ids - set(items))
            extra = sorted(set(items) - expected_ids)
            raise ValueError(
                f"{estimate['_source_file']}: work item set differs; missing={missing}, extra={extra}"
            )

    work_item_results = []
    for item_id in sorted(expected_ids):
        baseline = indexed[0][item_id]
        for estimate, items in zip(estimates[1:], indexed[1:]):
            candidate = items[item_id]
            for field in (
                "name",
                "role",
                "depends_on",
                "delivery_strategy",
                "reused_components",
                "custom_build_justification",
            ):
                if candidate.get(field) != baseline.get(field):
                    raise ValueError(
                        f"{estimate['_source_file']}: {item_id}.{field} differs from frozen baseline"
                    )
        values = {
            reviewer_id: require_number(items[item_id].get("expected"), f"{item_id}.expected")
            for reviewer_id, items in zip(reviewer_ids, indexed)
        }
        result = comparison(values, threshold)
        result.update(
            {
                "id": item_id,
                "name": baseline.get("name"),
                "role": baseline.get("role"),
                "delivery_strategy": baseline.get("delivery_strategy"),
                "reused_components": baseline.get("reused_components"),
            }
        )
        work_item_results.append(result)

    metric_results: dict[str, Any] = {}
    for metric in METRICS:
        values = {
            reviewer_id: require_number(estimate.get(metric), f"{estimate['_source_file']}:{metric}")
            for reviewer_id, estimate in zip(reviewer_ids, estimates)
        }
        metric_results[metric] = comparison(values, threshold)

    return {
        "packet_id": packet_id,
        "packet_hash": packet_hash,
        "rubric_version": rubric_version,
        "unit": unit,
        "working_days_per_person_month": working_days_per_person_month,
        "reviewer_count": len(estimates),
        "threshold_pct": threshold,
        "reviewers": [
            {
                "reviewer_id": reviewer_id,
                "estimate_id": estimate.get("estimate_id"),
                "model": estimate.get("model"),
                "source_file": estimate["_source_file"],
            }
            for reviewer_id, estimate in zip(reviewer_ids, estimates)
        ],
        "work_items": work_item_results,
        "metrics": metric_results,
        "flagged_work_items": [item["id"] for item in work_item_results if item["requires_review"]],
        "flagged_metrics": [name for name, value in metric_results.items() if value["requires_review"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("estimates", nargs="+", type=Path, help="Three or more estimate JSON files")
    parser.add_argument("--threshold", type=float, default=30.0, help="Divergence review threshold in percent")
    parser.add_argument("--output", type=Path, help="Write JSON to this path instead of stdout")
    args = parser.parse_args()

    if args.threshold < 0 or not math.isfinite(args.threshold):
        print("ERROR: threshold must be a finite non-negative number", file=sys.stderr)
        return 2

    try:
        result = aggregate([load_estimate(path) for path in args.estimates], args.threshold)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        try:
            args.output.write_text(payload, encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: cannot write {args.output}: {exc}", file=sys.stderr)
            return 2
        print(f"WROTE: {args.output}")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
