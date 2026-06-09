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
   - State the reviewed scope before listing findings.

2. Read the diff.
   - Use `git diff` for unstaged changes and `git diff --cached` for staged changes.
   - Read surrounding code when needed with `sed`, `rg`, or direct file inspection.
   - Do not review unrelated pre-existing issues unless the diff makes them newly reachable or worse.
   - For large diffs, prioritize high-risk areas first: public APIs, data writes, migrations, auth and permissions, error handling, external dependencies, deploy configuration, and changed tests. Sample low-risk formatting or presentation-only changes after the risky paths are covered.

3. Review with the checklist below.
   - Flag only actionable issues introduced by the current changes.
   - Do not report issues that a linter, type checker, compiler, or formatter would reliably catch unless they indicate a behavioral risk, API misuse, migration gap, or CI coverage gap.
   - Prefer fewer, higher-confidence findings over broad speculation.

4. Verify when appropriate.
   - Run the smallest focused tests or static checks that directly cover the changed behavior when they are cheap to run.
   - Infer likely test commands from project configuration when the command is obvious.
   - Do not turn a review into a long full-suite CI investigation unless the user asked for it or the risk justifies it.
   - If checks are not run, say so and explain the residual risk.

5. Prepare the commit when requested.
   - Decide whether the diff should be one commit or multiple commits.
   - Stage only files that belong to the requested commit scope.
   - Never stage unrelated changes. If unrelated changes exist, leave them unstaged and mention them.
   - If the final diff touches public contracts, schemas, config, permissions, caching, migrations, generated artifacts, or shared modules, run `change-impact-analysis` before staging.
   - Create a concise commit message that describes the completed change.
   - After committing, report the commit hash and final worktree state.

## Checklist

Always check:

- Bugs: null or undefined access, off-by-one errors, inverted conditions, wrong operators, missing `await`, swallowed exceptions, race conditions, and copy-paste mistakes.
- API and data compatibility: changed public signatures, exported types, route methods or response shapes, config keys, env vars, CLI flags, serialization fields, and database schema compatibility.
- Tests: missing regression tests, new public behavior without coverage, weak assertions, and untested integration or e2e paths.
- Security: unsanitized input, hardcoded or logged secrets, missing authz/authn, sensitive data in logs or responses, and injection paths.
- Performance: N+1 queries, missing indexes for new query patterns, unbounded memory growth, blocking I/O on hot paths, and avoidable large loads.
- Maintainability: unclear names, excessive nesting, magic values, conflicting local patterns, overly long functions, and unnecessary complexity.
- Scope hygiene: unrelated changes, dead code, commented-out blocks, duplicated logic, and leftover debug output.
- Deployability: required migrations, env vars, infrastructure, external services, feature flags, deploy order, and dev/prod differences.
- Observability: useful logs, correct log levels, trace or correlation identifiers where relevant, metrics for critical paths, and log volume.
- Error handling and user experience: actionable user-facing errors, correct status codes, graceful degradation, retry semantics, and failure isolation.

Apply these only when triggered by the diff:

- Data model or persistence schema changes: check the upgrade path for existing deployments, not only fresh setup. Find the project's migration, bootstrap, entrypoint, installer, seed, or backfill mechanism and verify it applies new columns/tables/indexes/constraints idempotently to an already-created database or data store. Require a focused legacy/upgrade test or an explicit manual upgrade command when the change cannot be made automatic.
- Idempotency and retry safety: for POST, PUT, PATCH, DELETE, INSERT, UPDATE, payments, orders, notifications, and message sends, check idempotency keys, deduplication, unique constraints, UPSERTs, and duplicate side effects.
- Resource cleanup: for file I/O, database connections, HTTP clients, pools, timers, intervals, streams, iterators, or native handles, check cleanup on success, error, early return, and cancellation paths.
- Dependency changes: for dependency manifests or lockfiles, check maintenance status, license fit, footprint, breaking changes, deprecated API removal, and known vulnerabilities.

## Output Format

Use this format exactly:

```markdown
## 🔴 必须修改

<Blocking issues, each with file:line and fix suggestion. If none, write "无">

## 🟡 建议修改

<Non-blocking issues worth addressing, each with file:line and fix suggestion. If none, write "无">

## 测试建议

<Specific tests or checks to add/run. If adequate, write "现有测试已覆盖主要路径">

## 总体评价

<2-4 sentences summarizing code quality, risk level, and whether the reviewer would approve>

## 可合并判断

✅ 可以合并 / ⚠️ 修复必须项后可合并 / ❌ 不建议合并
<One sentence explaining the judgment>
```

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
