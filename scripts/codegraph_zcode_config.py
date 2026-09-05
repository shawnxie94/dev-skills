#!/usr/bin/env python3
"""Install or remove dev-skills' codegraph UserPromptSubmit hook in ZCode.

ZCode keeps hooks inside the main app config (`cli/config.json`) under
``hooks.events.<Event>`` and requires ``hooks.enabled: true`` for
configuration-file hooks. The writer is surgical: it only touches the
``hooks`` key and preserves every other top-level key (provider credentials,
model state, ...).
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

HOOK_EVENT = "UserPromptSubmit"


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError(f"ZCode config must contain a JSON object: {path}")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def build_handler(hook_script: Path, codegraph_bin: Path, python_bin: str = "python3") -> dict[str, str]:
    command = " ".join(
        [
            python_bin,
            str(hook_script),
            "--codegraph-bin",
            str(codegraph_bin),
        ]
    )
    return {
        "type": "command",
        "command": command,
        "timeout": 30,
    }


def is_managed_handler(handler: object, hook_script: Path) -> bool:
    return isinstance(handler, dict) and str(hook_script) in str(handler.get("command", ""))


def install_config(
    path: Path,
    hook_script: Path,
    codegraph_bin: Path,
    *,
    python_bin: str = "python3",
    dry_run: bool = False,
) -> str:
    config = load_config(path)
    hooks = config.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"hooks must be a JSON object: {path}")
    hooks["enabled"] = True
    events = hooks.setdefault("events", {})
    if not isinstance(events, dict):
        raise ValueError(f"hooks.events must be a JSON object: {path}")
    groups = events.setdefault(HOOK_EVENT, [])
    if not isinstance(groups, list):
        raise ValueError(f"{HOOK_EVENT} hooks must be a JSON array: {path}")

    handler = build_handler(hook_script, codegraph_bin, python_bin)
    kept_groups: list[dict[str, Any]] = []
    found = False
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
            kept_groups.append(group)
            continue
        retained = [item for item in group["hooks"] if not is_managed_handler(item, hook_script)]
        found = found or len(retained) != len(group["hooks"])
        if retained:
            updated = dict(group)
            updated["hooks"] = retained
            kept_groups.append(updated)
    kept_groups.append({"hooks": [handler]})
    events[HOOK_EVENT] = kept_groups

    if dry_run:
        return f"would {'update' if found else 'add'} codegraph hook in {path}"
    atomic_write(path, config)
    return f"{'updated' if found else 'added'} codegraph hook in {path}"


def uninstall_config(path: Path, hook_script: Path, *, dry_run: bool = False) -> str:
    config = load_config(path)
    hooks = config.get("hooks")
    if not isinstance(hooks, dict):
        return f"no codegraph hook in {path}"
    events = hooks.get("events")
    if not isinstance(events, dict):
        return f"no codegraph hook in {path}"
    groups = events.get(HOOK_EVENT)
    if not isinstance(groups, list):
        return f"no codegraph hook in {path}"

    kept_groups: list[dict[str, Any]] = []
    removed = False
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
            kept_groups.append(group)
            continue
        retained = [item for item in group["hooks"] if not is_managed_handler(item, hook_script)]
        removed = removed or len(retained) != len(group["hooks"])
        if retained:
            updated = dict(group)
            updated["hooks"] = retained
            kept_groups.append(updated)
    if not removed:
        return f"no codegraph hook in {path}"

    if kept_groups:
        events[HOOK_EVENT] = kept_groups
    else:
        events.pop(HOOK_EVENT, None)
    if not events:
        hooks.pop("events", None)

    if dry_run:
        return f"would remove codegraph hook from {path}"
    atomic_write(path, config)
    return f"removed codegraph hook from {path}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)

    install = subparsers.add_parser("install")
    install.add_argument("--config-file", type=Path, required=True)
    install.add_argument("--hook-script", type=Path, required=True)
    install.add_argument("--codegraph-bin", type=Path, required=True)
    install.add_argument("--python-bin", default="python3")
    install.add_argument("--dry-run", action="store_true")

    uninstall = subparsers.add_parser("uninstall")
    uninstall.add_argument("--config-file", type=Path, required=True)
    uninstall.add_argument("--hook-script", type=Path, required=True)
    uninstall.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    if args.action == "install":
        message = install_config(
            args.config_file,
            args.hook_script,
            args.codegraph_bin,
            python_bin=args.python_bin,
            dry_run=args.dry_run,
        )
    else:
        message = uninstall_config(args.config_file, args.hook_script, dry_run=args.dry_run)
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
