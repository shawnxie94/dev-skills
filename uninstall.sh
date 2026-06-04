#!/usr/bin/env bash
# uninstall.sh — remove dev-skills symlinks from local Codex
# Thin shim over install.sh; see ./install.sh --help
exec "$(cd "$(dirname "$0")" && pwd)/install.sh" --uninstall "$@"
