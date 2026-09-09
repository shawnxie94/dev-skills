---
name: subagent-orchestration
description: Choose, dispatch, observe, and recover delegated work across Pi/Nico, Codex, ZCode, and other runtimes. Defines logical subagent roles, context-offload rules, lifecycle handling, runtime adapters, and bounded handoff contracts; does not implement the delegated task itself（子代理编排、角色选择、运行时适配、上下文卸载、恢复策略）.
---

# Subagent Orchestration

Use this skill when work may be delegated to a subagent, when the user asks about
subagent roles or runtime behavior, or when a task is large enough that raw
research, codebase exploration, logs, or verification output would pollute the
coordinating context.

This skill owns delegation policy. It does not become the product requirement,
technical design, execution plan, implementation, or final acceptance source of
truth. The coordinating session remains responsible for scope, synthesis,
acceptance, and user-visible decisions.

## Core Contract

Every delegation must make these decisions explicit:

1. **Logical role**: `scout`, `researcher`, `oracle`, `worker`, `reviewer`,
   `evidence-auditor`, or the later `verifier` role.
2. **Runtime adapter**: the current harness and its actual delegation tool. Do
   not infer Pi/Nico semantics from a generic word such as "subagent".
3. **Context policy**: `fresh`, `fork`, or an approved retained `resume`.
4. **Execution mode**: foreground/blocking or background/async, with explicit
   wait and observation behavior.
5. **Isolation and ownership**: read-only shared checkout, serial shared writer,
   or isolated worktree; never concurrent writes to one checkout.
6. **Output contract**: bounded inline result, structured result, or durable
   artifact reference. Large raw material must stay out of the parent context.
7. **Failure policy**: terminal state, partial side effects, retry/resume rule,
   and the handoff required before another attempt.

The runtime may use different names, APIs, lifecycle states, and persistence
models. A role is a capability contract, not a required provider, model, or
agent filename. If a runtime cannot provide an equivalent capability, report a
visible blocker or explicitly labelled degraded fallback; never silently switch
runtime, model, or role.

## Side-Effect Preflight

Classify the objective before choosing a role:

- **Observe/verify**: inspect state or validate a claim without changing it.
  Use `scout`, `reviewer`, `evidence-auditor`, or `verifier` as appropriate.
- **Mutate/execute**: install, uninstall, configure, authenticate, launch,
  migrate, edit, or otherwise change the system, repository, dependencies, or
  external state. Route directly to a write-capable `worker` (or the
  domain-specific release operator), with explicit allowed paths and rollback
  boundaries.

A task containing both phases must split at the boundary: an auditor or
researcher may identify and verify the command, then the coordinator hands the
frozen command and acceptance checks to `worker`. Never assign an installation
or configuration objective to `evidence-auditor`, `reviewer`, `scout`, or
`oracle` merely because source research is needed first. A read-only profile
may recommend an action, but it does not own the action.

## Role Selection

Read `references/roles.md` before inventing a new role. The initial registry is:

- `scout`: local read-only reconnaissance and compressed context handoff.
- `researcher`: external/document research with source traceability.
- `oracle`: independent decision challenge and blind-spot analysis.
- `worker`: approved implementation and internal verification.
- `reviewer`: independent code/plan review, read-only by default.
- `evidence-auditor`: independent claim/source/evidence verification.
- `verifier`: reserved for command-heavy acceptance evidence when `reviewer` is
  insufficient; add only with a demonstrated validation gap.

Do not create roles for execution modes (`background-worker`, `fresh-scout`),
retry phases (`fix-worker`), or orchestration responsibilities (`delegate`,
`integrator`). Express those as runtime policy or coordinator behavior.

## Context-Offload Policy

Use a child when the work is broad, independently verifiable, or likely to
consume a material share of the coordinator's context. Common triggers include
large external research, many source documents, long tool/test output, broad
codebase reconnaissance, independent review, and evidence collection.

The parent should send a small task packet and receive a bounded handoff:

- facts/findings and uncertainty;
- exact source/file/line references or artifact paths;
- structured claims and evidence when applicable;
- commands and exit codes for verification work;
- changed files, deviations, blockers, and residual risks for writers.

Prefer `fresh` context for independent research, audits, reviews, and scouts.
Use `fork` only when the child genuinely needs parent history. Use `file-only`
or equivalent durable output for large results, then read the artifact
selectively. Never concatenate raw web pages, complete transcripts, or verbose
logs into the parent prompt when an index or summary is sufficient.

See `references/context-offload.md` for the research, implementation, and
verification patterns.

## Runtime and Lifecycle

Resolve runtime behavior before dispatch:

- Pi with Nico uses the `subagent` tool, Nico agent discovery, background run
  artifacts, `status`/`bg_wait`, steering, and guarded retained `resume`.
- Codex and ZCode use their native actor APIs and their own wait/continue
  semantics.
- A Pi retained resume is a new child turn from a persisted session, not a
  guarantee that the original model HTTP request continues.
- Provider failure after mutation is not permission to replay the whole task.
  Capture the partial diff, inspect terminal state, then choose a safe resume or
  a new bounded repair packet.

See `references/lifecycle.md` and `references/runtime-adapters.md` before
writing runtime-specific instructions into another skill.

## Handoff Boundaries

- `$execution-delivery` owns the approved plan, execution target, write
  ownership, acceptance IDs, and plan linkage.
- `$implement-plan` owns implementation of the approved whole goal or assigned
  node; a worker is a leaf and must not recursively delegate.
- `$research` owns research framing, evidence quality, and final synthesis;
  this skill supplies the delegation and context-offload path.
- `$codebase-analysis` may use `scout` for broad read-only reconnaissance but
  remains responsible for the analysis artifact.
- The coordinator owns final acceptance and may not treat a child prose claim
  as acceptance evidence by itself.

Do not create a second plan, Task Pack, acceptance source of truth, or hidden
runtime fallback inside this skill.

## Output Contract

When dispatching, return or persist a packet containing:

- logical role and resolved runtime adapter;
- objective and bounded scope;
- required context and explicitly omitted context;
- allowed paths/tools and forbidden writes;
- context/execution/isolation/output policy;
- verification and acceptance evidence;
- retry/resume and terminal-state rules;
- expected final result shape.

When operating an existing run, report the exact run identity, current state,
control action, delivery receipt, partial side effects, and next safe action.

## Handoff Map

- Approved implementation plan needs routing → `$execution-delivery` (`delegate`).
- Delegated implementation needs execution → `$implement-plan`.
- Large or evidence-heavy research needs offload → `$research` with this skill's
  researcher/evidence-auditor contract.
- Unclear codebase impact → `$codebase-analysis` with a read-only scout first.
- A runtime or child failure needs reproduction → `$bug-reproduction`.
