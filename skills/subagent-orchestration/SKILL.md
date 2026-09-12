---
name: subagent-orchestration
description: Choose, dispatch, observe, and recover delegated work across Pi, Codex, ZCode, and other runtimes（子代理编排、角色选择、运行时适配、上下文卸载、恢复策略）. Owns roles, context-offload, runtime adapters, and handoff contracts; does not implement the task itself.
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
   not infer Pi semantics from a generic word such as "subagent".
3. **Context policy**: `fresh`, `fork`, or an approved retained `resume`.
4. **Execution mode**: foreground/blocking or background/async, with explicit
   wait and observation behavior.
5. **Isolation and ownership**: read-only shared checkout, serial shared writer,
   or isolated worktree; never concurrent writes to one checkout.
6. **Output contract**: bounded inline result, structured result, or durable
   artifact reference. Large raw material must stay out of the parent context.
7. **Failure policy**: terminal state, partial side effects, retry/resume rule,
   and the handoff required before another attempt.

8. **Session model choice**: before the first delegated run in a conversation,
   obtain an explicit user-selected `provider/model` (unless the user already
   supplied one). Record it as a conversation-scoped choice, forward it
   explicitly to every subsequent new child run, and do not ask again until
   the user explicitly changes it.

The runtime may use different names, APIs, lifecycle states, and persistence
models. A role is a capability contract, not a required provider, model, or
agent filename. If a runtime cannot provide an equivalent capability, report a
visible blocker or explicitly labelled degraded fallback; never silently switch
runtime, model, or role.

## Join Barrier

After dispatch, resolve a `join_policy` before doing more coordinator work:

- `required` is the default for a `batch`, a dependent DAG node, a shared-writer
  task, or any dispatch with no explicitly declared independent coordinator work.
- `opportunistic` is allowed only when the packet names disjoint work that can
  proceed without the child result. The coordinator may do only that work, then
  must wait before any dependent action or acceptance.
- With `required`, the next coordinator action is the runtime's native bounded
  wait. Do not run unrelated commands, emit progress as a substitute for
  waiting, start acceptance, or send a final answer while the required child is
  non-terminal.
- A wait timeout is an observation, not a terminal result. Continue with a
  bounded wait using the same run identity; do not treat timeout as success or
  replay the original task. Only `completed`, `blocked`, `failed`, or an
  explicitly documented stop state releases the barrier.

The dispatch identity must stay within its runtime adapter. A Codex native
`agent_id` is not a Codex App `threadId`; do not substitute App task wait tools
for native subagent wait tools.

## Acceptance Lock

Treat dispatch and acceptance as separate phases:

- Before dispatch, use `acceptance_phase=preflight`. Once a required child has
  started, set `acceptance_phase=locked` and
  `acceptance_barrier=child_terminal` for a batch or single dependent node.
- While the required child is non-terminal, the coordinator must not run
  acceptance commands, inspect the result as if it were complete, or emit a
  final answer. A timeout, progress message, or callback notification does not
  release the lock.
- After the target child returns `completed`, the coordinator may perform node
  acceptance. For a parallel DAG, set
  `acceptance_barrier=all_required_children_terminal` before integration
  acceptance; completed individual nodes do not by themselves release the
  integration lock.
- A runtime callback or stop hook may record the child's terminal payload or
  apply a child-side quality gate. It only releases the coordinator's wait
  barrier when the runtime reports a terminal state; it never replaces
  coordinator acceptance.

## Child-Result Evidence Gate

A terminal child state is not a verified result. Classify what came back before
accepting:

- `evidence`: names the changed files and the checks it ran (commands plus
  exit/count outcomes), or an explicit `blocked`/`failed` with a concrete reason.
- `no_evidence`: a completion claim with no report, no changed file, or no check
  result.

`no_evidence` is neither acceptance nor a finished round, and the coordinator
must never absorb that work silently: presenting absorbed work as delegated
output misreports authorship and hides a failing runtime. Re-dispatch once with a
consolidated packet stating the required result fields and the concrete
deliverable; if that replacement is also `no_evidence`, stop and escalate to the
user with the round ledger instead of spending the remaining rounds or finishing
the work itself.

Every dispatch consumes a round, including an unproductive one. Report the
counter from the run state instead of asserting the budget is exhausted, and
report which parts were child-produced versus coordinator self-fix. Remaining
work that needs a scope change — a new file, a new dependency, bootstrap or
test-harness wiring — is user-facing scope, not a coordinator self-fix; escalate
it rather than widening the child's allowed paths yourself.

## Slot Reclaim

Task completion and runtime resource reclamation are separate transitions:

- `wait` observes a child result; it does not release the child runtime slot.
- For runtimes where completed children remain open, the coordinator must call
  the runtime-native close operation after acceptance, or after recording a
  terminal blocker when no resume is planned. The default is
  `reclaim_policy=close_after_acceptance_or_terminal_escalation`.
- For a `completed` child, acceptance must pass before closure. If acceptance
  fails and repair is possible, keep the child open for the repair round; do
  not release the slot early.
- Keep a terminal child open only when the next convergence round will reuse
  that exact run identity. Send the consolidated repair packet, wait again,
  accept, then close it. Do not spawn a replacement before deciding whether the
  old identity is resumable or must be closed.
- Record the final result and evidence before closing. Never close an active
  child as routine cleanup; stopping an active child requires an explicit
  cancellation or escalation decision.

## Session Model Gate

Model selection is a user decision, not an orchestration default:

- Before the first subagent dispatch in the current conversation, stop and ask
  the user to choose the exact `provider/model` (and, if relevant, the
  thinking level), for example: “请确认本次子代理使用哪个
  `provider/model`？” If the current user message already names the model,
  treat that as the explicit choice and do not ask a redundant question.
- Keep the choice in conversation state as `selected_subagent_model`. Apply it
  to every subsequent **new** subagent dispatch, regardless of logical role,
  runtime adapter, workflow stage, or parallel lane. Pass it explicitly rather
  than relying on profile defaults, parent inheritance, tier recommendations,
  or fallback models.
- For `codex_subagent`, the native dispatch schema has no provider parameter.
  Preserve the confirmed model and thinking choice, record
  `provider_resolution=host_inherited`, and do not claim that a provider was
  forwarded. If the user requires a provider that the adapter cannot express,
  report a blocker instead of silently changing the route.
- Do not ask again for another child in the same conversation. If the user
  explicitly requests a model change, replace the session choice before the
  next dispatch; if the user asks to change it without naming a model, ask for
  the exact choice.
- If the selected model is unavailable, unsupported by the adapter,
  unauthenticated, or out of quota, stop with a visible blocker and ask the
  user to select another model. Never silently substitute a model or provider.
- A retained resume may be pinned by the runtime to its original model. After
  an explicit model change, do not resume that child under the old choice;
  start a new bounded dispatch when continuation is needed.

## Model Routing Policy

Resolve model and thinking settings separately from the logical role. When the
shared `~/Developer/agents/subagent-policies.json` is available and its
`recommendationEnabled` flag is true, use its `fast`/`balanced`/`deep` profile
as a recommendation and validate the logical-model route mapping for the
actual runtime adapter. When recommendations are disabled, ignore the policy
and use normal user/native model selection; direct subagent delegation remains
available. Do not hard-code deployment model IDs in this skill. An explicit
user-selected `provider/model` and thinking level always win; when only a
logical model is confirmed, provider fallback may try the ordered routes for
that same model. Never silently switch model, runtime, or task scope. Keep
persistent runtime ceilings separate from task-level `usageBudget`. See
`references/model-routing.md` for the routing heuristic, Pi projection, and
limit semantics.

## Side-Effect Preflight

Classify the objective before choosing a role:

- **Observe/verify**: inspect state or validate a claim without changing it.
  Use `scout`, `reviewer`, `evidence-auditor`, or `verifier` as appropriate.
- **Mutate/execute**: install, uninstall, configure, authenticate, launch,
  migrate, edit, or otherwise change the system, repository, dependencies, or
  external state. Route directly to a write-capable `worker` (or the
  domain-specific release operator), with explicit allowed paths and rollback
  boundaries.

A task containing both phases does **not** automatically require two
delegations. If the command, source, scope, and rollback are already known and the
mutation is bounded, route the whole task directly to `worker`, including its
own preflight and verification. Add a separate `researcher` or
`evidence-auditor` only when the command/source is uncertain, alternatives need
independent comparison, the mutation is high-risk or irreversible, or the
acceptance contract explicitly requires independent evidence. In that case,
the coordinator freezes the auditor's findings before handing the action to
`worker`. Never assign an installation or configuration objective to
`evidence-auditor`, `reviewer`, `scout`, or `oracle` merely because source
research is useful. A read-only profile may recommend an action, but it does
not own the action.

## Efficiency Rule

Roles are a capability menu, not a mandatory pipeline. Optimize for the fewest
actors and tool calls that preserve safety, evidence quality, and clear
ownership. A single `worker` may research a known bounded task, perform its own
preflight, execute the mutation, and verify the result when its tools and
acceptance contract cover the whole objective. Do not insert a researcher,
auditor, reviewer, or second handoff merely to satisfy a checklist. Split work
only when the independent pass materially reduces risk, resolves uncertainty,
protects context, or improves acceptance confidence.

## Role Selection

Read `references/roles.md` before inventing a new role. The initial registry is:

- `scout`: local read-only reconnaissance and compressed context handoff.
- `researcher`: external/document research with source traceability.
- `oracle`: independent decision challenge and blind-spot analysis.
- `worker`: approved implementation and internal verification. Its result counts
  only when it names changed files and the checks it ran; a completion claim
  with no report or no changed file is `no_evidence`, not a finished round.
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

- Pi uses the official SDK-backed `subagent` extension. It creates persistent
  child sessions and supports explicit `status`, `stop`, and `resume` actions.
- Forward the session-selected model explicitly at each new dispatch when the
  adapter supports model selection; an adapter that cannot honor it is a
  visible blocker, not a reason to fall back silently.
- Codex and ZCode use their native actor APIs and their own wait/continue
  semantics.
- A Pi resume is a new child turn from a persisted SDK session, not a
  guarantee that the original model HTTP request continues.
- Provider failure after mutation is not permission to replay the whole task.
  Capture the partial diff, inspect terminal state, then choose a safe resume or
  a new bounded round packet.

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

- session-scoped `selected_subagent_model` and whether it was explicitly
  supplied by the user or obtained through the first-dispatch model gate;
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
