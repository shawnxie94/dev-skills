---
id: subagent-orchestration-migration-v1
type: execution_plan
status: completed
created_at: 2026-09-09
updated_at: 2026-09-09
sources:
  - README.md
  - skills/execution-delivery/SKILL.md
  - skills/execution-delivery/references/delegate.md
  - skills/research/SKILL.md
  - skills/implement-plan/SKILL.md
related: []
base_commit: 95ccfcb125b3232c8e8c17c3951a1c410193d984
orchestration_mode: batch
execution_target: current_session
execution_backend:
---

# Subagent orchestration migration

## Implementation Goal

Replace the Pi official example subagent extension with `nicobailon/pi-subagents`, add a runtime-neutral `subagent-orchestration` skill that defines logical roles and delegation policy, and migrate the existing dev-skills delegation/research/implementation guidance to use that contract without duplicating Nico-specific behavior across unrelated skills.

Done means:

- Nico is installed and the old official Pi subagent extension is no longer active;
- Pi 0.85.1 smoke checks cover discovery, foreground/background execution, failure state, and retained resume semantics;
- `subagent-orchestration` defines the initial roles `scout`, `researcher`, `oracle`, `worker`, `reviewer`, and `evidence-auditor`, with `verifier` explicitly reserved as a follow-up role unless implementation evidence requires it;
- the role contract is runtime-neutral and maps to Pi/Nico, Codex, and ZCode adapters without assuming shared tool names or lifecycle semantics;
- `execution-delivery`, `research`, and `implement-plan` defer to the new orchestration contract instead of maintaining conflicting subagent rules;
- README skill chains and contract checks document the new skill;
- all changed repository checks pass, and local Pi changes are reported separately from git-tracked changes.

## Execution Decision

- orchestration_mode: `batch`
- execution_target: `current_session`
- execution_backend: none
- user_approval: `approved` — user selected `batch` after the parallelism assessment.

## Batch Plan

- plan_unit_id: `root`
- actor: current session
- acceptance_scope: complete migration
- parallel_mode: `serial_shared_writer`
- write_ownership:
  - `dev-skills` repository: new skill, references, README, execution/research/implementation guidance, tests/checks, and this plan
  - Pi user configuration: package installation and old-extension activation state only
- forbidden_writes:
  - unrelated repositories or worktrees
  - existing user agent prompts unless required for Nico compatibility and explicitly recorded
  - Pi credentials, auth tokens, model provider definitions, or unrelated extensions
  - source code belonging to user projects

## Internal Sequence

1. Record baseline state and validate the current Pi/runtime installation surface.
2. Install `pi-subagents` and the optional web-research provider only if the Nico research roles require it; move the official extension out of the active extension path without deleting the source, preserving a rollback path.
3. Run a minimal Nico smoke suite before changing dev-skills guidance: agent discovery, one foreground read-only child, one background child with status/wait, failure reporting, and a controlled retained resume/follow-up test.
4. Add `skills/subagent-orchestration/SKILL.md` and concise references for roles, lifecycle, context offload, and runtime adapters.
5. Update `README.md`, `execution-delivery`, `research`, and `implement-plan` so the new skill owns role selection, runtime mapping, lifecycle semantics, and context-budget rules; preserve plan/acceptance/leaf-executor ownership in the existing skills.
6. Add contract checks or fixtures where needed, run repository validation, and review the final diff and local Pi state separately.

## Role Contract

The new skill defines logical roles, not provider/model names or runtime tool syntax:

- `scout`: local read-only codebase reconnaissance and compressed handoff.
- `researcher`: external or document research with source traceability and bounded artifact output.
- `oracle`: independent decision challenge and blind-spot analysis; no writes.
- `worker`: approved implementation and internal verification; sole writer for its scope.
- `reviewer`: independent code/plan review; read-only by default.
- `evidence-auditor`: independent verification of research claims and citations; no writes.
- `verifier`: follow-up role for command-heavy acceptance evidence, not required in the first role registry unless current validation gaps justify it.

Every role contract must state objective, capabilities, write permissions, context policy, output schema, lifecycle defaults, and failure handoff.

## Runtime Adapter Contract

- Pi + Nico resolves logical roles through Nico/user/project agent discovery and must inspect actual capabilities before launch. Nico-specific actions such as `status`, `steer`, `stop`, `resume`, `workflowScript`, `outputMode`, and `bg_wait` remain in the Pi adapter reference.
- Codex maps roles to the available `multi_agent_v1` actor type and preserves its wait/send semantics.
- ZCode maps roles to native `Agent` calls and preserves its background/output semantics.
- Missing role equivalence or runtime capability is a visible blocker or explicitly labelled degraded fallback; it must not silently switch runtime, model, or role.
- `foreground/background`, `fresh/fork/resume`, worktree choice, model tier, timeout, and output mode are execution policy, not separate roles.

## Context-Offload Contract

For context-heavy research, codebase exploration, logs, browser snapshots, and evidence collection:

- delegate raw acquisition and first-pass compression to a read-only child;
- prefer `fresh` context for independent research and audit;
- use bounded summaries, structured output, or `outputMode: file-only` for large results;
- return artifact paths and claim/source indexes rather than raw source dumps;
- let the coordinating agent perform final synthesis and acceptance;
- preserve only selected source excerpts when a final conclusion needs direct proof.

For mutation-capable children, inspect the partial diff before retrying after timeout, network failure, stop, or provider exhaustion. Do not automatically replay a task that may already have produced side effects.

## Verification Plan

### Pi/local smoke

- `pi --version` reports the supported Pi version.
- The old official extension is inactive and only one `subagent` provider is registered.
- Nico agent discovery exposes the expected builtin/user roles.
- A foreground read-only run completes with bounded output.
- A background run produces a status identity, can be waited on, and leaves inspectable artifacts.
- A failed or paused run is reported with structured state; a stopped run is not revived.
- A retained child can be resumed as a new turn when Nico reports it resumable; this must not be described as same-request HTTP recovery.
- Builtin web research is either smoke-tested with `pi-web-access` or explicitly recorded as unavailable.

### Repository checks

- `python3 scripts/check_skill_contracts.py`
- `git diff --check`
- targeted internal-reference and README coverage checks
- `git status --short` and final diff review

## Acceptance Criteria

- AC-01: Pi uses Nico as the active `subagent` implementation with a documented rollback path.
- AC-02: The new skill has one canonical cross-runtime role/lifecycle/context contract and no conflicting duplicate contract in the migrated skills.
- AC-03: All six initial roles have explicit permissions, context, output, and failure semantics.
- AC-04: Pi/Nico, Codex, and ZCode differences are represented as adapters; unavailable capabilities fail closed or are visibly degraded.
- AC-05: Heavy research guidance keeps raw materials and verbose tool output out of the coordinating context by default.
- AC-06: Existing plan, acceptance, worktree, model immutability, and leaf-agent constraints remain intact.
- AC-07: Repository checks pass and no unrelated repository/config changes are included.

## Execution Record

- Repository contract check: `python3 scripts/check_skill_contracts.py` — passed (15 skills).
- Formatting check: `git diff --check` — passed.
- Pi: `0.85.1`; installed `pi-subagents@0.66.0` and `pi-web-access@0.28.0`; official extension inactive and backed up at `/tmp/pi-official-subagent-backup-20260909-193555`.
- Foreground smoke: builtin `oracle`, `context:fresh`, bounded read-only task — passed.
- Background smoke: `oracle`, `status` observed `running`, `bg_wait` observed completion, final output token — passed.
- Dispatch failure smoke: nonexistent agent — failed closed at resolution with an `isError` tool result and discovered-agent diagnostics; no child launched.
- Web smoke: foreground `evidence-auditor` correctly failed because ambient web tools are unavailable in foreground; background `evidence-auditor` with `pi-web-access` completed one search and returned `WEB_ACCESS_OK`.
- Retained resume smoke: same-session background child returned `RESUME_SEED_OK`; status advertised `Revive`; resume produced a new run and `RESUME_FOLLOWUP_OK`. This is a new child turn, not in-flight HTTP recovery.
- Explicit-model async smoke: exactly one builtin `oracle` child with `async:true`, `context:fresh`, and `openai-codex/gpt-5.6-luna:low` returned `BUILTIN_LUNA_BG_OK`; status, native completion notification, `bg_wait`, and final status were observed without retry or substitution.
- Interactive FleetView smoke: a native Pi TUI run showed the persistent async widget and `/subagents-fleet` overlay with live tool activity, `[fresh]` context, resolved `gpt-5.6-luna · thinking low`, completion state, and `FLEETVIEW_LUNA_OK`; no Orca observer was used.
- Orca installation: official Stably AI Orca `v1.4.198` Apple Silicon DMG installed and verified at `/Applications/Orca.app`; bundled `/opt/homebrew/bin/orca` reports `1.4.198` and supports `orca terminal create`. `orcaProgressTabs` remains disabled/unconfigured pending explicit activation.

## Final Handoff

- implementation status: `completed`;
- changed repository files and commit state: repository changes remain uncommitted; see `git status --short` and the final diff;
- Pi package/extension state and rollback path: see package/extension state above and the backup directory;
- smoke commands and results: recorded above; local Pi configuration is not part of the repository diff;
- residual risks: real Tauri/TCC/Keychain/model-provider boundaries remain unverified; foreground web roles require explicit child extension configuration or background execution; Codex/ZCode adapters are contract documentation, not live cross-runtime acceptance in this session.
