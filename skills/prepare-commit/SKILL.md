---
name: prepare-commit
description: Review and prepare pending code changes before commit, merge, or PR creation. Use when the user asks for "review", "review my changes", "pre-commit check", "check before commit", "/review", "整理提交", "提交代码", "帮我 commit", or when Codex is preparing to stage files, create a commit, or publish changes. Focus on scoped diff review, bugs, regressions, API breakage, missing tests, security, performance, maintainability, deployability, observability, commit hygiene, safe staging, concise commit messages, and final worktree state.
---

# Prepare Commit

Prepare pending changes for commit. Always review the diff first; only stage or commit when the user explicitly asks to create or organize a commit.

## Modes

- Review-only mode: use when the user asks to review, check, or inspect changes. Do not stage or commit.
- Commit-preparation mode: use when the user asks to prepare, organize, stage, or create a commit. Review first; if no blocking issues are found and the requested scope is clear, stage only relevant files and commit.

## Workflow

1. Determine scope.
   - Run `git status --short`, `git diff --name-only`, and `git diff --stat`.
   - If the user specifies files, staged-only review, or a commit range, review only that scope.
   - By default, review all pending changes. If both staged and unstaged changes exist, inspect both so staged-only or unstaged-only issues are not missed.
   - Create a review target snapshot before reading findings. Record the base (working copy, commit, or branch range), included staged/unstaged/untracked files, excluded files, file count, and changed-line count.
   - Preview the file set before detailed review. If the requested scope cannot be resolved exactly, state the ambiguity and treat the result as `partial` until it is resolved.
   - Distinguish the intended commit scope from the broader review scope. Do not silently review the whole worktree and present it as a staged-only review.

2. Select review strategy and coverage units.
   - Use the smallest strategy that can cover the target: direct review for small changes, risk-first review for medium changes, and unit-based review for large changes.
   - As a heuristic, treat a change as small when it is at most 5 files and 50 changed lines, medium when it is at most 15 files and 300 changed lines, and large beyond either threshold. These thresholds guide sequencing, not approval by themselves.
   - Always elevate a change to risk-first review when it touches public APIs, schemas/migrations, auth or permissions, data writes, concurrency, queues, caching, external dependencies, deployment configuration, or generated artifacts, regardless of size.
   - For medium or large changes, group related files into review units before inspecting them: route/API + service + schema, migration + model + query, UI + client + types, queue/job + retry/transaction code, or config + startup/deployment files.
   - A review is complete only when every included file and every relevant unit has been inspected. If a file is skipped because of size, tooling, context, or an execution error, report the skipped path and mark the review `partial` or `error`.
   - Extract a short business context from the task, PR, commit message, branch, or surrounding docs: intended behavior, behavior that must remain unchanged, and affected users/APIs/data/deployments. Use it to focus the review; do not invent missing requirements.

3. Read the diff.
   - Use `git diff` for unstaged changes and `git diff --cached` for staged changes.
   - Read surrounding code when needed with `sed`, `rg`, or direct file inspection.
   - Do not review unrelated pre-existing issues unless the diff makes them newly reachable or worse.
   - Follow the selected review units. For large diffs, prioritize high-risk units first, then cover ordinary units; do not stop after the high-risk pass and claim full coverage.
   - Resolve review rules in this order: explicit task/user constraints, project `AGENTS.md` and project profile, project tests/lint/typecheck/deploy configuration, then this skill's generic checklist. A more specific rule supplements or overrides a generic rule only when the source clearly says so.
   - Apply path-triggered checks when the relevant paths are present: migrations/schema → existing-deployment upgrade and idempotency; auth/permissions → authentication, authorization, and sensitive logging; API/routes/SDK → contract and compatibility; payments/orders/data writes → duplicate side effects and retry safety; queues/jobs/workers → delivery, retry, concurrency, and cleanup; deployment/config → env, ordering, and rollback; generated artifacts → source-of-truth and regeneration.

4. Review with the checklist below.
   - Flag only actionable issues introduced by the current changes.
   - Do not report issues that a linter, type checker, compiler, or formatter would reliably catch unless they indicate a behavioral risk, API misuse, migration gap, or CI coverage gap.
   - Prefer fewer, higher-confidence findings over broad speculation.
   - Every finding must include: severity (`blocking` or `advisory`), confidence (`high`, `medium`, or `low`), file and line/section, the concrete problem, evidence from the code or contract, impact, a suggested fix, and a verification step.
   - A finding without a precise line location may use a file and named section, but must say that positioning is approximate. Do not mark an imprecisely positioned or weakly evidenced concern as blocking.
   - Treat likely false positives, style preferences, and concerns without a concrete failure mode as advisory or omit them. Do not inflate severity to compensate for uncertainty.

5. Verify when appropriate.
   - Run the smallest focused tests or static checks that directly cover the changed behavior when they are cheap to run.
   - Infer likely test commands from project configuration when the command is obvious.
   - Do not turn a review into a long full-suite CI investigation unless the user asked for it or the risk justifies it.
   - If checks are not run, say so and explain the residual risk.
   - Keep review coverage and verification status separate: a complete diff review does not mean tests passed, and passing tests does not mean the diff was fully reviewed.
   - Classify the final state explicitly:
     - `complete`: every intended file/unit was reviewed; verification may still be `passed`, `not run`, or `failed`.
     - `partial`: one or more intended files/units were not reviewed, with paths and reasons listed.
     - `error`: the review could not be performed or its result could not be trusted.
   - Never report `complete` or `no issues` when the review process itself stopped early, returned incomplete output, or failed to inspect the intended scope.

6. Prepare the commit when requested.
   - Decide whether the diff should be one commit or multiple commits.
   - Stage only files that belong to the requested commit scope.
   - Never stage unrelated changes. If unrelated changes exist, leave them unstaged and mention them.
   - If the final diff touches public contracts, schemas, config, permissions, caching, migrations, generated artifacts, or shared modules, run `change-impact-analysis` before staging.
   - Create a concise commit message that describes the completed change.
   - After committing, report the commit hash and final worktree state.
7. Record the run for the feedback loop.
   - Append a short outcome event after a material review (skip only for trivial look-ups the user did not want tracked):

   ```bash
   python3 <dev-skills>/scripts/record_skill_run.py \
     --skill prepare-commit \
     --status completed \
     --validation pass \
     --task-type commit-review \
     --friction <short-tag> \
     --feedback <short non-sensitive note>
   ```

   - Record `blocked` or `abandoned` outcomes too; they are the most useful signals for future retrospectives.

## Checklist

Always check:

- Bugs: null or undefined access, off-by-one errors, inverted conditions, wrong operators, missing `await`, swallowed exceptions, race conditions, and copy-paste mistakes.
- API and data compatibility: changed public signatures, exported types, route methods or response shapes, config keys, env vars, CLI flags, serialization fields, and database schema compatibility.
- Tests: missing regression tests, new public behavior without coverage, weak assertions, and untested integration or e2e paths.
- Security: unsanitized input, hardcoded or logged secrets, missing authz/authn, sensitive data in logs or responses, and injection paths.
- Performance: N+1 queries, missing indexes for new query patterns, unbounded memory growth, blocking I/O on hot paths, and avoidable large loads.
- Maintainability: unclear names, excessive nesting, magic values, conflicting local patterns, overly long functions, and unnecessary complexity.
- Scope hygiene: unrelated changes, dead code, commented-out blocks, duplicated logic, and leftover debug output.
- Deployability: required migrations, env vars, infrastructure, external services, feature flags, deploy order, dev/prod differences, and app-owned default config (for example prompt templates or system settings) that existing deployments must pick up.
- Observability: useful logs, correct log levels, trace or correlation identifiers where relevant, metrics for critical paths, and log volume.
- Error handling and user experience: actionable user-facing errors, correct status codes, graceful degradation, retry semantics, and failure isolation.

Apply these only when triggered by the diff:

- Data model or persistence schema changes: check the upgrade path for existing deployments, not only fresh setup. Find the project's migration, bootstrap, entrypoint, installer, seed, or backfill mechanism and verify it applies new columns/tables/indexes/constraints idempotently to an already-created database or data store. Require a focused legacy/upgrade test or an explicit manual upgrade command when the change cannot be made automatic.
- App-owned default config or prompt template changes: check how existing deployments pick up new defaults, not just fresh setups. Require an idempotent upgrade, seed, or backfill when old instances keep stale values, and confirm a fresh-environment smoke check shows the new default takes effect.
- Idempotency and retry safety: for POST, PUT, PATCH, DELETE, INSERT, UPDATE, payments, orders, notifications, and message sends, check idempotency keys, deduplication, unique constraints, UPSERTs, and duplicate side effects.
- Resource cleanup: for file I/O, database connections, HTTP clients, pools, timers, intervals, streams, iterators, or native handles, check cleanup on success, error, early return, and cancellation paths.
- Dependency changes: for dependency manifests or lockfiles, check maintenance status, license fit, footprint, breaking changes, deprecated API removal, and known vulnerabilities.

## Output Format

Use this format exactly:

```markdown
## 审查范围

- target: <working copy / commit / branch range>
- included: <files or count, including staged/unstaged/untracked distinction>
- excluded: <files or "无">
- review strategy: <direct / risk-first / unit-based>
- coverage: <complete / partial / error>
- skipped or unresolved: <paths and reasons, or "无">

## 🔴 必须修改

<Blocking issues. Each item must include severity, confidence, file:line or approximate section, problem, evidence, impact, fix suggestion, and verification. If none, write "无">

## 🟡 建议修改

<Non-blocking issues. Each item must include confidence, file:line or approximate section, problem, evidence, impact, fix suggestion, and verification. If none, write "无">

## 测试建议

<Specific tests or checks to add/run. If adequate, write "现有测试已覆盖主要路径">

## 总体评价

<2-4 sentences summarizing code quality, risk level, and whether the reviewer would approve>

## 可合并判断

✅ 可以合并 / ⚠️ 修复必须项后可合并 / ❌ 不建议合并
<One sentence explaining the judgment. A `partial` or `error` coverage state cannot receive ✅ without explicit user acceptance of the residual risk.>
```

The `审查范围` block is mandatory even when there are no findings. `coverage` describes whether the diff was inspected, while the test section describes whether behavior was verified; do not use one as a substitute for the other.

If there are no changes in scope, report that there is nothing to review and stop.

## Commit Preparation Output

When a commit is created, append:

```markdown
## Commit

<commit hash> <commit message>

## Worktree State

<clean, or list remaining unstaged/untracked changes and why they were left out>
```

## Handoff Rules

- If review finds blocking implementation defects, hand off to `implement-plan`.
- If review finds broad impact concerns, hand off to `change-impact-analysis`.
- If commit succeeds and the worktree is clean, no next skill is required by default.
