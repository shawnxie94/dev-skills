#!/usr/bin/env python3
"""Append a privacy-conscious, structured skill run record to a local JSONL log."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


SKILL_NAME = re.compile(r"^[a-z][a-z0-9-]*$")
STATUSES = ("completed", "blocked", "abandoned", "skipped")
VALIDATIONS = ("pass", "fail", "skipped", "not_applicable")

# The record log is per-runtime so a pi or ZCode session never writes into a
# Codex home it does not use. `summarize_skill_runs.py --all-runtimes`
# aggregates the set, and DEV_SKILLS_RUN_LOG still overrides everything.
RUNTIME_HOMES = {
    "pi": Path(".pi") / "agent",
    "codex": Path(".codex"),
    "zcode": Path(".zcode"),
}
LOG_NAME = "dev-skills-runs.jsonl"


def detect_runtime() -> str:
    """Best-effort host detection mirroring scripts/detect_runtime.sh."""

    forced = os.environ.get("DEV_SKILLS_FORCE_RUNTIME", "").strip().lower()
    if forced in RUNTIME_HOMES:
        return forced
    if os.environ.get("PI_CODING_AGENT") == "true" or os.environ.get("AI_AGENT") == "pi":
        return "pi"
    if os.environ.get("ZCODE_HOME"):
        return "zcode"
    if os.environ.get("CODEX_HOME"):
        return "codex"
    for runtime, relative in RUNTIME_HOMES.items():
        if (Path.home() / relative).is_dir():
            return runtime
    return "unknown"


def default_log_path() -> Path:
    configured = os.environ.get("DEV_SKILLS_RUN_LOG")
    if configured:
        return Path(configured).expanduser()
    runtime = detect_runtime()
    home = RUNTIME_HOMES.get(runtime)
    if home is None:
        return Path.home() / ".dev-skills" / LOG_NAME
    return Path.home() / home / LOG_NAME


def runtime_log_paths() -> list[Path]:
    return [Path.home() / relative / LOG_NAME for relative in RUNTIME_HOMES.values()]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Record one dev-skills run without storing the original prompt or task content."
    )
    result.add_argument("--skill", required=True, help="Skill name, for example codebase-analysis")
    result.add_argument("--status", choices=STATUSES, required=True)
    result.add_argument("--validation", choices=VALIDATIONS, default="not_applicable")
    result.add_argument("--task-type", default="", help="Short category such as bug-fix or planning")
    result.add_argument("--next-handoff", default="", help="Next skill or human decision, if any")
    result.add_argument("--friction", action="append", default=[], help="Short repeatable friction tag")
    result.add_argument("--feedback", default="", help="Short non-sensitive feedback, not the original prompt")
    result.add_argument("--duration-ms", type=int, default=None)
    result.add_argument("--project", default="", help="Optional non-sensitive project slug")
    result.add_argument("--run-id", default=str(uuid.uuid4()))
    result.add_argument("--path", type=Path, default=default_log_path(), help="JSONL log path")
    result.add_argument("--dry-run", action="store_true", help="print the record without writing it")
    return result


def main() -> int:
    args = parser().parse_args()
    if not SKILL_NAME.fullmatch(args.skill):
        print(f"invalid skill name: {args.skill}", file=sys.stderr)
        return 2
    if args.duration_ms is not None and args.duration_ms < 0:
        print("--duration-ms must be non-negative", file=sys.stderr)
        return 2

    event = {
        "schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "run_id": args.run_id,
        "skill": args.skill,
        "status": args.status,
        "validation": args.validation,
        "task_type": args.task_type,
        "next_handoff": args.next_handoff,
        "friction": args.friction,
        "feedback": args.feedback,
        "project": args.project,
    }
    if args.duration_ms is not None:
        event["duration_ms"] = args.duration_ms

    path = args.path.expanduser()
    if args.dry_run:
        print(json.dumps({"would_write": str(path), **event}, ensure_ascii=False, sort_keys=True))
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    print(f"Recorded {args.skill} run ({args.status}) -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
