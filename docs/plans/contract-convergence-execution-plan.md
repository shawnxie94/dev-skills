---
id: contract-convergence-20260910
type: execution_plan
status: completed
created_at: 2026-09-10
updated_at: 2026-09-10
orchestration_mode: batch
sources:
  - README.md
  - skills/execution-delivery/SKILL.md
  - skills/implement-plan/SKILL.md
  - skills/delivery-readiness/SKILL.md
  - scripts/detect_runtime.sh
  - scripts/record_skill_run.py
  - scripts/check_skill_contracts.py
  - ../agent-brain/docs/plans/harness-consistency-convergence-execution-plan.md
---

# Execution Contract Convergence

## Goal

Make `dev-skills` the single textual owner of the execution contract that
agent-brain consumes, close the `execution_backend` drift that silently blocked
`pi_subagent`/`zcode_subagent`, and give the run-record feedback loop
runtime-aware defaults instead of a hard-coded Codex path.

Shared context and the cross-repo unit list live in
`agent-brain/docs/plans/harness-consistency-convergence-execution-plan.md`;
this plan owns only the dev-skills side.

## Scope

In scope:

- `skills/execution-delivery/SKILL.md` — declare the canonical
  `execution_backend` set and the shared linkage fields; agent-brain references
  this text instead of restating it.
- `skills/implement-plan/SKILL.md` — stop restating agent-brain's Task Pack,
  lane, and context-budget rules; reference the owner.
- `skills/delivery-readiness/SKILL.md` — one canonical report per gate stage;
  iteration history stays inside that file or a `history/` subdirectory.
- `skills/{research,write-prd,write-trd,delivery-estimation,delivery-readiness,codebase-analysis}/SKILL.md`
  — add the run-record section so the feedback loop is not skewed to four
  skills.
- `scripts/record_skill_run.py` — runtime-aware default log path.
- `scripts/summarize_skill_runs.py` — aggregate across runtimes.
- `scripts/check_skill_contracts.py` — validate `$skill` references inside
  `references/*.md`, not only `SKILL.md`.
- `tests/` — cover the new default-path logic and the reference scan.

Out of scope: renaming existing readiness iteration files in any project.

## Acceptance

```bash
python3 scripts/check_skill_contracts.py
python3 -m pytest tests -q
python3 -m compileall -q scripts
DEV_SKILLS_FORCE_RUNTIME=pi python3 scripts/record_skill_run.py --skill research --status completed --validation pass --task-type research --dry-run
```

## Rollback

`git restore` the touched paths. The run-record log format is unchanged, so no
historical record needs migration.
