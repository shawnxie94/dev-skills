#!/usr/bin/env python3
"""ZCode UserPromptSubmit adapter for `codegraph prompt-hook`.

`codegraph prompt-hook` emits plain-text context, which is the Claude Code
UserPromptSubmit contract. ZCode only injects hook stdout when it is valid
JSON carrying `hookSpecificOutput.additionalContext`; plain-text output is
silently discarded. This adapter forwards the hook payload to codegraph and
repacks non-empty output into the ZCode-accepted JSON envelope.

Fail-open by design: a missing index, missing binary, or timeout yields empty
output and exit 0, so the hook never blocks a session.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

DEFAULT_TIMEOUT_SECONDS = 25.0


def build_response(context: str) -> dict[str, object]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codegraph-bin", default="codegraph")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)

    try:
        payload = sys.stdin.read()
    except OSError:
        return 0

    try:
        result = subprocess.run(
            [args.codegraph_bin, "prompt-hook"],
            input=payload,
            capture_output=True,
            text=True,
            timeout=args.timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return 0

    context = result.stdout.strip()
    if not context:
        return 0

    json.dump(build_response(context), sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
