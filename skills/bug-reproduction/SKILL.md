---
name: bug-reproduction
description: Reproduce and characterize a bug before attempting a fix. Use when the user reports broken behavior, a failing page, API, command, test, CI job, local service, data refresh, cache issue, regression, flaky behavior, or asks why something is not working. Focus on expected vs actual behavior, real execution paths, minimal reproduction steps, evidence collection, logs, network/API traces, database or state checks, confirmed facts, hypotheses, and next debugging or fix direction before editing code.
---

# Bug Reproduction

Use this skill to avoid guessing fixes. The goal is to reproduce the problem, identify the real path involved, and collect enough evidence to guide a targeted fix.

## Core Principles

- Reproduce before changing code whenever feasible.
- Separate observed facts from hypotheses.
- Follow the real user or system path: page, API, CLI, job, worker, test, database, cache, or external service.
- Minimize the reproduction while preserving the failure.
- Capture evidence that another engineer could use to verify the issue.
- Do not over-debug unrelated code paths once the failing path is identified.

## What To Inspect

Use the relevant sources for the bug:

- User report: expected behavior, actual behavior, environment, timing, input, screenshots, logs.
- Codebase orientation: run commands, entry points, modules, tests, data flow.
- Runtime path: frontend route, API endpoint, CLI command, worker/job, event handler, test case.
- Evidence: logs, console output, network requests, response bodies, database rows, cache state, generated files, screenshots, traces.
- Recent changes: git diff, commits, dependency changes, migrations, config changes.

## Reproduction Workflow

1. Restate the bug.
   - State expected behavior, actual behavior, and the affected surface.
   - Identify missing details, but avoid blocking on questions when local reproduction is possible.

2. Locate the likely entry point.
   - Use codebase files and commands to find the page, API, command, job, or test involved.
   - If the repository is unfamiliar, run a quick `codebase-orientation` style pass first.

3. Build a minimal reproduction path.
   - Prefer an existing failing test or the shortest command/user flow that triggers the issue.
   - If a dev server is needed and practical, start it and verify the actual surface.
   - If external dependencies block reproduction, document the missing dependency and use the closest local substitute.

4. Collect evidence.
   - Capture commands run, inputs used, outputs observed, errors, logs, request/response details, state changes, and timestamps when useful.
   - For UI issues, use browser inspection or screenshots when available.
   - For data issues, inspect database/cache/state rather than relying only on the UI.

5. Narrow the failure.
   - Compare expected vs actual at each boundary.
   - Identify the first point where the observed behavior diverges.
   - Keep a clear list of confirmed facts and remaining hypotheses.

6. Decide next action.
   - If reproduced, summarize likely fix direction and the evidence supporting it.
   - If the reproduced bug suggests a broad contract, data-flow, cache, permission, or config issue, run `change-impact-analysis` before fixing.
   - If not reproduced, explain what was tried, what was ruled out, and what information is still needed.
   - Only proceed to code changes if the user asked for a fix or the task clearly includes fixing.

## Handoff Rules

- If the bug is reproduced and the fix is straightforward, hand off to `implement-plan`.
- If the fix requires structural change, hand off to `refactor-plan`.
- If the blast radius is unclear, hand off to `change-impact-analysis`.

## Output Format

Answer in the user's language unless they request otherwise. Use this structure when practical:

```markdown
## Bug Summary

Expected: <expected behavior>
Actual: <actual behavior>
Surface: <page/API/command/job/test/environment>

## Reproduction Steps

1. <Step>
2. <Step>
3. <Step>

## Evidence

- Command / input: `<command or input>`
- Observed output: <output, error, log, response, screenshot, state>
- Relevant files or paths: <files, routes, modules>

## Confirmed Facts

- <Fact>

## Hypotheses

- <Hypothesis and why it is plausible>

## Narrowed Failure Point

<First boundary where expected and actual behavior diverge>

## Next Debugging Or Fix Direction

<Targeted next step, likely fix area, or missing information>
```

For small bugs, compress the format while preserving reproduction steps, evidence, confirmed facts, and next direction.
