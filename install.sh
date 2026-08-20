#!/usr/bin/env bash
# install.sh — symlink dev-skills/* into local Codex
#
# Usage:
#   ./install.sh                 install (idempotent, default)
#   ./install.sh --uninstall     remove dev-skills symlinks only
#   ./install.sh --dry-run       show what would change, change nothing
#   ./install.sh -h | --help     show this help
#
# Env:
#   CODEX_HOME   target Codex home (default: $HOME/.codex)
set -euo pipefail

# ---------- locate this script (works through symlinks) ----------
_src="${BASH_SOURCE[0]:-$0}"
while [ -L "$_src" ]; do
  _dir="$(cd -P "$(dirname "$_src")" && pwd)"
  _src="$(readlink "$_src")"
  [[ "$_src" != /* ]] && _src="$_dir/$_src"
done
SCRIPT_DIR="$(cd -P "$(dirname "$_src")" && pwd)"

REPO_DIR="$SCRIPT_DIR"
SKILLS_SRC="$REPO_DIR/skills"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SKILLS_DST="$CODEX_HOME/skills"

# ---------- options ----------
ACTION="install"
DRY_RUN=0
print_help() {
  cat <<'EOF'
install.sh — symlink dev-skills/* into local Codex

Usage:
  ./install.sh                 install (idempotent, default)
  ./install.sh --uninstall     remove dev-skills symlinks only
  ./install.sh --dry-run       show what would change, change nothing
  ./install.sh -h | --help     show this help

Env:
  CODEX_HOME   target Codex home (default: $HOME/.codex)
EOF
}
while [ $# -gt 0 ]; do
  case "$1" in
    -u|--uninstall) ACTION="uninstall"; shift ;;
    -n|--dry-run)   DRY_RUN=1; shift ;;
    -h|--help)      print_help; exit 0 ;;
    *) echo "install.sh: unknown option: $1" >&2; print_help >&2; exit 2 ;;
  esac
done

# ---------- pretty output ----------
if [ -t 1 ]; then
  C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_ERR=$'\033[31m'; C_DIM=$'\033[2m'; C_RST=$'\033[0m'
else
  C_OK=; C_WARN=; C_ERR=; C_DIM=; C_RST=
fi
info() { printf "%s==%s %s\n" "$C_DIM" "$C_RST" "$*"; }
ok()   { printf "%s✓%s %s\n" "$C_OK" "$C_RST" "$*"; }
warn() { printf "%s!%s %s\n" "$C_WARN" "$C_RST" "$*" >&2; }
err()  { printf "%s✗%s %s\n" "$C_ERR" "$C_RST" "$*" >&2; }
note() { printf "  %s=%s %s\n" "$C_DIM" "$C_RST" "$*"; }
run() {
  if [ "$DRY_RUN" = 1 ]; then
    printf "  %s(dry-run)%s" "$C_DIM" "$C_RST"
    printf " %q" "$@"
    printf "\n"
  else
    "$@"
  fi
}

# Resolve a symlink to an absolute path (empty on failure)
resolve_link() {
  local link="$1" raw
  raw="$(readlink "$link" 2>/dev/null || true)"
  [ -n "$raw" ] || return 1
  if [[ "$raw" = /* ]]; then
    printf "%s\n" "$raw"
  else
    (cd -P "$(dirname "$link")" 2>/dev/null && cd -P "$raw" 2>/dev/null && pwd) || true
  fi
}

CODEGRAPH_INSTALL_URL="https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh"
CODEGRAPH_BIN=""

find_codegraph() {
  if command -v codegraph >/dev/null 2>&1; then
    command -v codegraph
    return 0
  fi
  if [ -x "$HOME/.local/bin/codegraph" ]; then
    printf "%s\n" "$HOME/.local/bin/codegraph"
    return 0
  fi
  return 1
}

ensure_codegraph() {
  info "checking codegraph"
  CODEGRAPH_BIN="$(find_codegraph || true)"
  if [ -n "$CODEGRAPH_BIN" ]; then
    ok "codegraph found: $CODEGRAPH_BIN"
  else
    warn "codegraph not found; installing the official local binary"
    if command -v curl >/dev/null 2>&1; then
      local installer_file
      installer_file="$(mktemp "${TMPDIR:-/tmp}/codegraph-install.XXXXXX")"
      if [ "$DRY_RUN" = 1 ]; then
        run curl -fsSL "$CODEGRAPH_INSTALL_URL" -o "$installer_file"
        run sh "$installer_file"
        run rm -f "$installer_file"
      elif curl -fsSL "$CODEGRAPH_INSTALL_URL" -o "$installer_file" && sh "$installer_file"; then
        rm -f "$installer_file"
      else
        rm -f "$installer_file"
        warn "official CodeGraph installer failed; trying npm fallback"
      fi
    fi
    if [ "$DRY_RUN" = 1 ]; then
      return 0
    fi
    if [ -z "$(find_codegraph || true)" ] && command -v npm >/dev/null 2>&1; then
      run npm install -g @colbymchenry/codegraph
    elif [ -z "$(find_codegraph || true)" ]; then
      err "codegraph requires curl or npm to install"
      exit 1
    fi
    CODEGRAPH_BIN="$(find_codegraph || true)"
  fi

  if [ "$DRY_RUN" = 1 ]; then
    return 0
  fi
  if [ -z "$CODEGRAPH_BIN" ]; then
    err "codegraph installation could not be verified; open a new shell if ~/.local/bin is not on PATH"
    exit 1
  fi
  if ! "$CODEGRAPH_BIN" --version >/dev/null 2>&1; then
    err "codegraph was found but could not run: $CODEGRAPH_BIN"
    exit 1
  fi
  ok "codegraph ready: $($CODEGRAPH_BIN --version)"

  if [ "${CODEGRAPH_CONFIGURE_CODEX:-1}" = 1 ]; then
    info "configuring CodeGraph for Codex"
    run "$CODEGRAPH_BIN" install --target=codex --yes
  fi
}

# ---------- preflight ----------
[ -d "$SKILLS_SRC" ] || { err "skills source not found: $SKILLS_SRC"; exit 1; }

SKILLS=()
while IFS= read -r entry; do
  [ -d "$entry" ] || continue
  name="${entry##*/}"
  case "$name" in .*) continue ;; esac
  SKILLS+=("$name")
done < <(
  find "$SKILLS_SRC" -mindepth 1 -maxdepth 1 -type d ! -name '.*' 2>/dev/null | LC_ALL=C sort
)
if [ "${#SKILLS[@]}" -eq 0 ]; then
  err "no skills found in $SKILLS_SRC"
  exit 1
fi

info "repo:   $REPO_DIR"
info "source: $SKILLS_SRC"
info "target: $SKILLS_DST"
info "action: $ACTION"
[ "$DRY_RUN" = 1 ] && info "mode:   dry-run"
printf "\n"

# ---------- install ----------
do_install() {
  [ -d "$SKILLS_DST" ] || run mkdir -p "$SKILLS_DST"

  local linked=0 skipped=0 warned=0
  for name in "${SKILLS[@]}"; do
    local target="$SKILLS_SRC/$name"
    local link="$SKILLS_DST/$name"

    if [ -L "$link" ]; then
      local cur
      cur="$(resolve_link "$link")"
      if [ "$cur" = "$target" ]; then
        note "$name (already linked)"
        skipped=$((skipped+1))
        continue
      fi
      warn "$name: existing symlink -> ${cur:-<broken>}; skipping (remove manually to replace)"
      warned=$((warned+1))
      continue
    fi
    if [ -e "$link" ]; then
      warn "$name: exists and is not a symlink; skipping (remove manually to replace)"
      warned=$((warned+1))
      continue
    fi
    run ln -s "$target" "$link"
    ok "link $name -> $target"
    linked=$((linked+1))
  done

  printf "\n"
  printf "summary: linked=%d skipped=%d warnings=%d\n" "$linked" "$skipped" "$warned"
}

# ---------- uninstall ----------
do_uninstall() {
  local removed=0 skipped=0
  for name in "${SKILLS[@]}"; do
    local link="$SKILLS_DST/$name"

    if [ ! -L "$link" ]; then
      note "$name (not a symlink)"
      skipped=$((skipped+1))
      continue
    fi
    local cur
    cur="$(resolve_link "$link")"
    if [ -z "$cur" ] || [ "$cur" != "$SKILLS_SRC/$name" ]; then
      warn "$name: not a dev-skills link (-> ${cur:-<broken>}); skipping"
      skipped=$((skipped+1))
      continue
    fi
    run rm "$link"
    ok "removed $name (was -> $cur)"
    removed=$((removed+1))
  done

  printf "\n"
  printf "summary: removed=%d skipped=%d\n" "$removed" "$skipped"
}

case "$ACTION" in
  install)   ensure_codegraph; printf "\n"; do_install ;;
  uninstall) do_uninstall ;;
esac
