#!/usr/bin/env python3
"""Summarize structured dev-skills run records for a lightweight retrospective."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


def parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def read_events(path: Path, since_days: int | None) -> tuple[list[dict], int]:
    cutoff = None
    if since_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    events: list[dict] = []
    malformed = 0
    if not path.is_file():
        return events, malformed
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        recorded_at = parse_time(event.get("recorded_at"))
        if cutoff and (recorded_at is None or recorded_at < cutoff):
            continue
        events.append(event)
    return events, malformed


def markdown(events: list[dict], path: Path, malformed: int) -> str:
    by_skill: dict[str, list[dict]] = defaultdict(list)
    friction = Counter()
    for event in events:
        by_skill[str(event.get("skill", "unknown"))].append(event)
        friction.update(str(tag) for tag in event.get("friction", []) if tag)

    lines = [
        "# dev-skills Run Summary",
        "",
        f"Source: `{path}`",
        f"Recorded runs: {len(events)}",
    ]
    if malformed:
        lines.append(f"Malformed lines skipped: {malformed}")
    lines.extend(["", "| Skill | Runs | Completed | Blocked | Validation pass | Validation fail |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for skill in sorted(by_skill):
        records = by_skill[skill]
        statuses = Counter(record.get("status") for record in records)
        validations = Counter(record.get("validation") for record in records)
        lines.append(
            f"| `{skill}` | {len(records)} | {statuses['completed']} | {statuses['blocked']} | "
            f"{validations['pass']} | {validations['fail']} |"
        )
    if friction:
        lines.extend(["", "## Friction Tags", "", "| Tag | Count |", "| --- | ---: |"])
        lines.extend(f"| `{tag}` | {count} |" for tag, count in friction.most_common())
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize dev-skills JSONL run records.")
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--since-days", type=int, default=30)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.since_days < 0:
        parser.error("--since-days must be non-negative")

    events, malformed = read_events(args.path.expanduser(), args.since_days)
    output = markdown(events, args.path.expanduser(), malformed)
    if args.output:
        args.output.expanduser().write_text(output, encoding="utf-8")
        print(f"Wrote summary -> {args.output.expanduser()}")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
