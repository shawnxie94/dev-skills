#!/usr/bin/env bash
# uninstall.sh — remove dev-skills symlinks from a local agent runtime
# Thin shim over install.sh; see ./install.sh --help
exec "$(cd "$(dirname "$0")" && pwd)/install.sh" --uninstall "$@"
