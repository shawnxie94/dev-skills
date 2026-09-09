#!/usr/bin/env bash
# detect_runtime.sh — identify which agent harness is hosting this shell
#
# Walks two of the three detection layers (see
# skills/execution-delivery/references/delegate.md, "Runtime Harness
# Detection"). Layer 1 (tool family) is in-prompt only and cannot be probed
# from a shell; this helper covers layers 2 (env var) and 3 (filesystem)
# and stops at the first definite answer.
#
# Usage:
#   scripts/detect_runtime.sh                # prints pi | codex | zcode | unknown
#   scripts/detect_runtime.sh --backend      # prints execution_backend value
#   scripts/detect_runtime.sh --json         # structured JSON on stdout
#   scripts/detect_runtime.sh --verbose      # also prints probe detail on stderr
#   scripts/detect_runtime.sh -h | --help
#
# Exit codes:
#   0  one of pi | codex | zcode detected (definite)
#   1  unknown — caller should fall back to current_session
#   2  invalid usage
#
# Environment overrides (testing only):
#   DEV_SKILLS_FORCE_RUNTIME=pi|codex|zcode  bypass every probe
#   DEV_SKILLS_PI_HOME                       default $HOME/.pi
#   DEV_SKILLS_CODEX_HOME                    default $HOME/.codex
#   DEV_SKILLS_ZCODE_HOME                    default $HOME/.zcode
set -euo pipefail

# ---------- arg parsing ----------
OUTPUT_MODE="plain"
VERBOSE=0

print_help() {
  sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --backend)  OUTPUT_MODE="backend"; shift ;;
    --json)     OUTPUT_MODE="json"; shift ;;
    --verbose|-v) VERBOSE=1; shift ;;
    -h|--help)  print_help; exit 0 ;;
    *) echo "detect_runtime.sh: unknown option: $1" >&2; exit 2 ;;
  esac
done

# ---------- paths ----------
PI_HOME="${DEV_SKILLS_PI_HOME:-$HOME/.pi}"
CODEX_HOME_DIR="${DEV_SKILLS_CODEX_HOME:-$HOME/.codex}"
ZCODE_HOME_DIR="${DEV_SKILLS_ZCODE_HOME:-$HOME/.zcode}"

# ---------- helpers ----------
log_layer() {
  # log_layer <layer> <message>
  if [ "$VERBOSE" = 1 ]; then
    printf "  [layer-%s] %s\n" "$1" "$2" >&2
  fi
  return 0
}

# ---------- forced override (testing) ----------
RUNTIME=""
REASON=""
if [ -n "${DEV_SKILLS_FORCE_RUNTIME:-}" ]; then
  case "$DEV_SKILLS_FORCE_RUNTIME" in
    pi|codex|zcode)
      RUNTIME="$DEV_SKILLS_FORCE_RUNTIME"
      REASON="forced via DEV_SKILLS_FORCE_RUNTIME=$DEV_SKILLS_FORCE_RUNTIME"
      log_layer 0 "$REASON"
      ;;
    *)
      echo "detect_runtime.sh: DEV_SKILLS_FORCE_RUNTIME must be pi|codex|zcode (got '$DEV_SKILLS_FORCE_RUNTIME')" >&2
      exit 2
      ;;
  esac
fi

# ---------- layer 2: env var markers ----------
if [ -z "$RUNTIME" ]; then
  pi_marker=""
  [ "${PI_CODING_AGENT:-}" = "true" ] && pi_marker="PI_CODING_AGENT=true"
  [ "${AI_AGENT:-}" = "pi" ] && pi_marker="${pi_marker:+$pi_marker }AI_AGENT=pi"

  if [ -n "$pi_marker" ]; then
    RUNTIME="pi"
    REASON="env marker: $pi_marker"
    log_layer 2 "$REASON"
  else
    log_layer 2 "no PI_CODING_AGENT / AI_AGENT=pi marker set"
  fi
fi

# ---------- layer 3: filesystem hints ----------
if [ -z "$RUNTIME" ]; then
  pi_ext="$PI_HOME/agent/extensions/subagent/index.ts"
  has_pi=0
  has_codex=0
  has_zcode=0
  [ -e "$pi_ext" ] && has_pi=1
  [ -d "$CODEX_HOME_DIR" ] && has_codex=1
  [ -d "$ZCODE_HOME_DIR" ] && has_zcode=1

  log_layer 3 "pi_subagent_ext=$has_pi codex_home=$has_codex zcode_home=$has_zcode"

  # Pi subagent extension is a strong positive signal — prefer it over the
  # generic home-directory hint, because the extension is what makes the
  # `subagent` tool actually dispatchable.
  if [ "$has_pi" = 1 ]; then
    RUNTIME="pi"
    REASON="filesystem: $pi_ext present"
  elif [ "$has_codex" = 1 ] && [ "$has_zcode" = 1 ]; then
    # Both homes present and no env marker; refuse to guess. The caller
    # either is in a shell context (not an agent prompt) or has multiple
    # runtimes installed for testing; either way, surface the ambiguity.
    REASON="ambiguous: $CODEX_HOME_DIR and $ZCODE_HOME_DIR both exist; cannot disambiguate without in-prompt tool-family probe"
    log_layer 3 "$REASON"
  elif [ "$has_codex" = 1 ]; then
    RUNTIME="codex"
    REASON="filesystem: $CODEX_HOME_DIR exists"
  elif [ "$has_zcode" = 1 ]; then
    RUNTIME="zcode"
    REASON="filesystem: $ZCODE_HOME_DIR exists"
  else
    log_layer 3 "no harness home directories found"
  fi
fi

# ---------- layer 1 reminder ----------
if [ "$VERBOSE" = 1 ] && [ "$OUTPUT_MODE" != "json" ]; then
  printf "  [layer-1] tool-family probe is only available from inside an agent prompt\n" >&2
  printf "             (Agent tool -> zcode, multi_agent_v1__* -> codex, subagent tool -> pi)\n" >&2
fi

# ---------- derive execution_backend ----------
backend_for() {
  case "$1" in
    pi)     printf 'pi_subagent\n' ;;
    codex)  printf 'codex_subagent\n' ;;
    zcode)  printf 'zcode_subagent\n' ;;
    *)      printf 'current_session\n' ;;
  esac
}

# ---------- emit ----------
BACKEND="$(backend_for "${RUNTIME:-unknown}")"

if [ "$OUTPUT_MODE" = "json" ]; then
  # Minimal portable JSON (no jq dependency): escape backslash and double
  # quote, replace newlines/tabs with space-like forms. Good enough for
  # structured consumption from other bash scripts and most log parsers.
  reason_json="${REASON:-no harness detected}"
  reason_json="${reason_json//\\/\\\\}"
  reason_json="${reason_json//\"/\\\"}"
  reason_json="${reason_json//	/ }"
  reason_json="${reason_json//$'\n'/ }"
  if [ -n "$RUNTIME" ]; then exit_code=0; else exit_code=1; fi
  printf '{"runtime":"%s","execution_backend":"%s","reason":"%s","exit_code":%d}\n' \
    "${RUNTIME:-unknown}" "$BACKEND" "$reason_json" "$exit_code"
else
  case "$OUTPUT_MODE" in
    backend) printf '%s\n' "$BACKEND" ;;
    *)       printf '%s\n' "${RUNTIME:-unknown}" ;;
  esac
fi

if [ -n "$RUNTIME" ]; then
  exit 0
else
  [ "$VERBOSE" = 1 ] && printf "no harness detected (tried env var + filesystem probes)\n" >&2
  exit 1
fi
