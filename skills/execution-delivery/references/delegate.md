# Execution Target and Delegation (delegate mode)

Mode reference for the `$execution-delivery` skill. Read this file only after
the router selects `delegate`: route an approved execution plan to the current
session or a subagent. A subagent target receives one whole-goal packet for a
`batch` plan, or bounded node packets for a `parallel_dag` plan. The target may
be a local child, remote Codex, managed-agent issue, squad child issue, GitHub
Issue, or workspace task file. This mode does not implement code.

## Core Principles

- Treat the handoff packet as the contract between planning and execution.
- Preserve traceability to PRD, TRD, execution plan, issues, decisions, and code context.
- Preserve the plan's `orchestration_mode`: do not create a DAG for a `batch` plan or a second DAG for a `parallel_dag` plan.
- Require an explicit execution target: `current_session` or `subagent`. Do not silently turn a routing request into remote execution.
- When the target is `subagent`, enforce the session model gate before creating a
  ready packet or dispatching: on the first subagent delegation in a
  conversation, obtain the user's explicit `provider/model` choice (unless
  already supplied), then reuse that exact choice for every subsequent new
  child in the conversation. Do not ask again unless the user explicitly
  changes it.
- Keep every subagent task bounded by scope, exclusions, write ownership, verification, and acceptance criteria.
- Preserve required capabilities and required skills from the source execution-plan node when the target platform supports them.
- Preserve the shared contract fields defined in the router: `plan_id`, `source_plan_sha256`, `base_commit`, `task_id`, `plan_unit_id`, `source_artifacts`, `source_hash`, `source_task_pack_sha256`, `acceptance_ids`, and `evidence_required`.
- Preserve `orchestration_mode`, `execution_target`, and `execution_backend` in
  the packet. `execution_backend` is required only when the target is
  `subagent`; it must be `zcode_subagent`, `codex_subagent`, `zcode_mcp`, or
  `pi_subagent`,
  resolved by the current harness (see the backend matrix), never picked by
  preference. Do not reuse agent-brain's `execution_mode` task lane for the
  plan shape or adapter.
- Split parallel tasks only when the approved `parallel_dag` has clear dependencies and write boundaries.
- Put only currently executable parallel tasks in `ready`; tasks with unmet dependencies must stay draft or blocked.
- For a delegated `batch`, create one ready task for the whole goal rather than unrelated serial tasks.
- Do not implement code or redesign the feature; if the plan is unclear, hand back to plan mode or `codebase-analysis` (impact mode).
- Preserve the session-selected subagent model/provider exactly in every new
  handoff and dispatch, regardless of role, lane, or runtime adapter. An
  unavailable, unsupported, unauthenticated, or out-of-quota choice is a
  user-visible blocker; never substitute another model or provider without
  explicit user approval. A retained resume that is pinned to its original
  model must not be used after the user explicitly changes the session choice.
- A subagent is a leaf executor and must not recursively call, spawn, or delegate to another subagent. Orchestration remains with the coordinating session; a child that discovers orchestration work must report the scope gap instead of creating another child.
- Do not mark a subagent task ready unless the user or source artifact clearly indicates approval and the execution target is explicit.
- A subagent handoff is one goal and one final return **per round**. Unless the
  packet declares disjoint coordinator work, it uses `join_policy=required`:
  set `acceptance_phase=locked` and make the coordinating agent's next action
  after dispatch the runtime-native bounded wait. It must not run acceptance or
  emit a final answer while the required child is non-terminal. The coordinator
  waits for a terminal `completed`, `blocked`, or `failed` result; only
  `completed` starts node acceptance, and integration acceptance additionally
  requires `all_required_children_terminal`. A failed or partial round
  enters the convergence loop: the coordinator records
  `progress_verdict: progress` or `no_progress`, issues one consolidated round
  packet (`repair` or `advance`), and re-dispatches. The loop runs at most
  `round_policy.max_rounds` rounds (default 3). Exceeding the budget, a
  `no_progress` verdict, or an unresolved blocker escalates to the user. The
  coordinator may fix mechanical compile/lint/test errors itself inside the
  task's allowed paths, recorded as `root_fix`; feature work and design changes
  always return to the child.

## Inputs to Look For

Use the execution plan, TRD, PRD, issue context, codebase analysis, implementation DAG, user approval, target repository, branch policy, test commands, and existing task files when available.

Extract:

- Source artifacts and their file paths.
- Approved scope and explicit non-goals.
- The plan's `orchestration_mode`, selected or pending `execution_target`, and whole-goal or node-level handoff inputs.
- For `parallel_dag`: DAG nodes, dependencies, critical path, risk-first nodes, shared-write nodes, and per-node handoff inputs.
- For `batch`: the single root unit, internal sequence, final acceptance scope, and complete-goal handoff inputs.
- Required capabilities and required skills for the whole actor or each execution-plan node.
- Task Pack linkage and canonical acceptance ids for the whole goal or each execution-plan node.
- Plan hash, Task Pack hash, Acceptance Pack path/hash, and baseline commit when available.
- Modules, files, APIs, schemas, migrations, generated artifacts, and config that each task may touch.
- Verification commands, manual checks, fixtures, logs, or PR review gates.
- Target repo, target branch, branch naming, PR expectations, and feedback format.

## Target Routing

The delegate mode has two execution targets:

- `current_session`: route the approved plan directly to `$implement-plan` in
  the current session. Do not create a remote task packet. If the plan is
  `batch`, the current session owns the whole implementation and final
  acceptance. If the user requested `parallel_dag` but no additional actors
  are available, report that true parallelism cannot occur and ask to downgrade
  to `batch` or choose `subagent`.
- `subagent`: create a task packet for a child actor. For `batch`, the packet
  covers the complete goal and has one final acceptance scope. For
  `parallel_dag`, create one packet per runnable node and preserve the source
  dependencies.

## Runtime Harness Detection

`execution_backend` is fixed by the *current* harness, not chosen by the
dispatcher. Before selecting a backend the skill must answer one question:
**which harness is hosting this session?** Use three detection layers in
order of reliability; stop at the first layer that yields a definite
answer.

### Detection Layers

**Layer 1 — Tool family (in-prompt, most reliable).** The model's own tool
list is the most direct signal because each harness exposes a different
native dispatch tool:

| Tool family visible | Implied harness | `execution_backend` |
|---|---|---|
| `subagent` tool present | Pi | `pi_subagent` |
| `Agent` tool present (no `subagent`) | ZCode native | `zcode_subagent` |
| `multi_agent_v1__spawn_agent` (and siblings) present | Codex native | `codex_subagent` |
| `mcp__zcode_codex__zcode_dispatch` present *and* no `multi_agent_v1` | Codex driving ZCode via MCP bridge | `zcode_mcp` |
| None of the above | current session only | `current_session` |

This layer is only available from inside an agent prompt, where the model
can inspect its own tool list directly.

**Layer 2 — Environment-variable marker (shell or in-prompt).** Useful for
hooks, scripts, child processes, or any context that cannot see the
parent's tool list. Documented markers:

| Variable | Value | Implied harness |
|---|---|---|
| `PI_CODING_AGENT` | `true` | Pi |
| `AI_AGENT` | `pi` | Pi (generic marker, also set by Pi) |

Codex and ZCode do **not** publish a public `AI_AGENT` / `*_CODING_AGENT`
process marker. If a layer-2 probe yields nothing, fall through to layer 3.

**Layer 3 — Filesystem hints (weakest, last resort).** Useful only when no
layer-1 or layer-2 signal is available; never override a higher-layer
result.

| Path | Implied harness |
|---|---|
| `$PI_HOME/agent/extensions/subagent/index.ts` exists | Pi (with subagent extension loaded) |
| `$CODEX_HOME` exists | Codex (likely) |
| `$ZCODE_HOME/cli/config.json` exists | ZCode (likely) |

Multiple homes may exist on the same machine (e.g. a developer keeps Codex
and Pi installed side-by-side). Layer 3 cannot disambiguate them; only
layer 1 or layer 2 can.

### Precedence and Ties

1. Always trust layer 1 when the tool list is visible.
2. Otherwise trust layer 2 (`PI_CODING_AGENT=true` / `AI_AGENT=pi`).
3. Otherwise use layer 3, treating Pi's subagent extension path as a strong
   positive signal and falling back to whichever of `$CODEX_HOME` /
   `$ZCODE_HOME` exists.
4. When two homes coexist and neither layer 1 nor layer 2 yields an
   answer, **report `unknown` rather than guessing** — the user must run
   the skill from the harness they intend, or pass
   `DEV_SKILLS_FORCE_RUNTIME=pi|codex|zcode` for an explicit override.
5. Never switch `execution_backend` away from what the host harness
   requires (e.g. do not use `pi_subagent` from a Codex session, even if
   `subagent` tools are visible through MCP). The host harness is the
   parent; cross-harness dispatch is a separate decision that belongs in
   `zcode_mcp`, not in this layer.

### Shell Helper

For pre-flight checks, hooks, or manual verification, run:

```bash
scripts/detect_runtime.sh                # prints pi | codex | zcode | unknown
scripts/detect_runtime.sh --backend      # prints execution_backend value
scripts/detect_runtime.sh --json         # structured output for tooling
scripts/detect_runtime.sh --verbose      # show every probe result on stderr
```

The helper walks layers 2 and 3 (layer 1 requires the in-prompt tool list
and is therefore not reachable from a shell). It exits `0` on a definite
detection and `1` on `unknown`; never exits `0` for a guess. Test all
three scenarios with `DEV_SKILLS_FORCE_RUNTIME=…` to exercise the helper
without switching harness.


## Subagent Backend Matrix And Runtime Adapters

`execution_backend` selects the runtime adapter after
`execution_target=subagent` has been chosen. The backend is decided by the
current harness, not by preference. Logical role selection, context policy,
output shaping, and lifecycle recovery are owned by `$subagent-orchestration`; this
reference preserves the plan packet and routing contract:

- ZCode session (native `Agent` tool present): `execution_backend=zcode_subagent`. Never spawn Codex children from ZCode (`codex_subagent` is unavailable here), and never wrap ZCode subagents in MCP calls (`zcode_mcp` is a cross-harness bridge, not in-session delegation).
- Codex session (`multi_agent_v1` tools present): `execution_backend=codex_subagent`, or `zcode_mcp` only when the ZCode MCP bridge tools are actually exposed in that session.
- Pi session with Pi SDK native `subagent` tool present: `execution_backend=pi_subagent`. Never dispatch from Pi to ZCode or Codex children; the Pi `subagent` tool is the in-session delegation mechanism. The Pi child is a leaf executor unless the approved workflow explicitly grants bounded fanout.
- Neither tool family is available: report a blocked handoff.

All adapters execute the packet; no adapter's success declaration is the final
acceptance. The coordinator waits for an explicit `completed` result before
running canonical acceptance. The protocols below describe supported
integrations; they do not imply that the current environment exposes every
named tool.

| Backend | Dispatch | Long wait / status | Next-round packet | Runtime boundary |
|---|---|---|---|---|
| `zcode_subagent` | Native `Agent` tool, one call per packet with a self-contained prompt | Foreground call blocks until the final message; `run_in_background` + `TaskOutput` (blocking) for long nodes; no polling | `SendMessage` to the same agent, one consolidated round packet per round | ZCode native child implementation and tests |
| `codex_subagent` | `multi_agent_v1__spawn_agent` with one complete goal or assigned DAG node | `multi_agent_v1__wait_agent`; bounded wait, no busy polling | `multi_agent_v1__send_input` to the same agent, one consolidated round packet per round | Codex child implementation and internal verification |
| `zcode_mcp` | `mcp__zcode_codex__zcode_dispatch` | `wait_ms` and terminal status; inspect with `zcode_status`, `zcode_messages`, or `zcode_diff` only when needed | `zcode_continue` on the same task, one consolidated round packet per round | ZCode code implementation and repository tests when explicitly available |
| `pi_subagent` | Official SDK-backed `subagent` tool with one complete goal or assigned DAG node | Foreground tool result plus returned `session_id`/`session_file` | `status`/`stop`, or `resume` with the persisted session file | Pi official SDK child session and repository tests |

### `zcode_subagent`

The default and only backend inside a ZCode session. ZCode subagents spawn
natively through the `Agent` tool; no MCP, no Codex.

- Call `Agent` once per packet with a self-contained prompt: the complete task
  packet or its file path plus a one-paragraph objective, the canonical plan
  path, and every command the child must run. A fresh subagent starts with no
  conversation context, so the prompt must not rely on session history or
  shorthand established earlier.
- Pick `subagent_type` by write ownership: `general-purpose` (or another type
  with write access) for nodes that write code or run state-changing commands;
  read-only types such as `Explore` only for analysis-only nodes.
- A foreground call blocks until the subagent returns its final message; that
  message is the terminal result. For concurrent `parallel_dag` dispatch,
  issue multiple `Agent` calls in one message so they run in parallel. For
  long-running nodes, set `run_in_background=true` and wait via `TaskOutput`
  (blocking); never busy-poll an unchanged agent.
- Require the final message to state `completed`, `blocked`, or `failed`,
  plus changed files, tests, deviations, blockers, and `attempt`. The
  subagent's final message is visible only to the coordinator, not to the
  user — relay the outcome after acceptance.
- Only after `completed`, run the coordinator's acceptance. If it fails or
  returns partial, send one complete consolidated round packet to the same
  agent via `SendMessage` (the agent resumes in the background with its prior
  context) and continue the loop until acceptance passes or the round budget /
  a blocker ends it. An unresolved blocker goes to the user.

### `codex_subagent`

Codex sessions only; unavailable from ZCode.

- Call `multi_agent_v1__spawn_agent` once for a `batch` whole-goal packet, or
  once per runnable `parallel_dag` node. The child receives one active goal and
  must not return after an internal step.
- `join_policy=required` is the default for a batch goal, a dependent node, or
  when no disjoint coordinator work is declared. Set `acceptance_phase=locked`
  and, after
  `multi_agent_v1__spawn_agent`, immediately call
  `multi_agent_v1__wait_agent` with the returned `agent_id`. A timeout is not a
  terminal result and `timeout_ms` is only the current wait window, not an ETA
  or child deadline; continue with a bounded wait using the same ID and
  backoff, without busy-polling, acceptance, or unrelated work.
- `join_policy=opportunistic` is allowed only when the packet names independent
  work. Finish that work, then wait before any dependent action or acceptance.
- Do not use `mcp__codex_app__wait_threads` for a native subagent: it accepts an
  App `threadId`, not the native `agent_id` returned by `spawn_agent`.
- Require the final child response to include `completed`, `blocked`, or
  `failed`, plus changed files, tests, deviations, blockers, and `attempt`.
- A configured Codex `SubagentStop` hook can persist or inspect the terminal
  child result, but it does not replace the parent `wait_agent` barrier or
  perform parent acceptance. This adapter has no separate parent webhook;
  completion delivered to `wait_agent` is the callback-like signal.
- Only after `completed`, run the coordinator's acceptance. If it fails or
  returns partial, send one complete consolidated round packet through
  `multi_agent_v1__send_input` to the same agent and continue the loop until
  acceptance passes or the round budget / a blocker ends it. An unresolved
  blocker goes to the user.

### `zcode_mcp`

A cross-harness bridge only: the coordinating session is Codex and the ZCode
MCP bridge tools (`zcode_dispatch` etc.) are exposed there. It is not how a
ZCode session delegates — inside ZCode use `zcode_subagent`.

- Call `mcp__zcode_codex__zcode_dispatch` with at least these mappings:
  `objective`, `implementation_paths`, `workspace_path`,
  `implementation_plan`, `acceptance`, `constraints`, `execution_mode`, and
  `workspace_mode`. Preserve the plan's `orchestration_mode`,
  `execution_target`, `execution_backend`, and linkage metadata in the
  implementation plan or constraints payload.
- Use `wait_ms` and the adapter's terminal status. Use `zcode_status`,
  `zcode_messages`, and `zcode_diff` only when a terminal result needs
  clarification or acceptance evidence is missing; do not turn these into
  periodic polling.
- Require a final `completed`, `blocked`, or `failed` response containing
  changed files, tests, deviations, blockers, and `attempt`. A successful
  ZCode response is still only an execution result, not coordinator acceptance.
- After a failed coordinator acceptance, call `zcode_continue` with one
  complete consolidated round packet and continue the loop until acceptance
  passes or the round budget / a blocker ends it. If ZCode requests permission
  or user input through `zcode_respond`, do not auto-approve; return a user
  blocker. Use `zcode_stop` only when the user or coordinator explicitly asks
  to stop.
- ZCode may implement code and run repository tests. Browser, desktop,
  visual, and other host-only acceptance capabilities remain with the
  coordinating session unless the adapter explicitly declares that capability
  and the approved plan authorizes it.

### Subagent Agent Resolution (Pi official SDK)

The minimal Pi adapter does not resolve named agent profiles. The coordinator
must encode the logical role, tools, write boundary, and output contract in the
child task packet. A role name alone is not proof of the effective tools, model,
context, or acceptance policy. If the requested capability is unavailable,
treat dispatch as `blocked`, not as permission to guess another role.

The packet should carry the logical role as a label plus the required tools,
context, write boundary, and output contract. The minimal adapter does not
resolve named profiles. An unavailable capability is a visible blocker; do not
silently substitute another role or backend.

### `pi_subagent`

Pi sessions only; unavailable from ZCode or Codex. The coordinating session
runs Pi with the official SDK-backed `subagent` extension.

- Dispatch through the `subagent` tool with `action: "spawn"` and a bounded
  `task`. The tool returns a `session_id` and persisted `session_file`.
- Use `action: "status"` or `action: "stop"` with `session_id`. Use
  `action: "resume"` with the persisted `session_file`; this starts a new
  model turn from stored context rather than resuming an HTTP request.
- The minimal adapter does not provide profiles, workflow fan-out, background
  wait, web access, or steering. Do not describe those capabilities as
  available in Pi unless another extension explicitly supplies them.
- The task must be self-contained and include the complete packet or its path,
  canonical plan, commands, exclusions, and final result contract. Preserve
  the selected provider/model in the child session configuration.
- Only after the child reports completion should the coordinator run final
  acceptance. If a child fails after tool side effects, inspect the worktree
  and artifacts before deciding whether to resume or issue a new bounded task.

The adapter contract is:

```text
round r = 1..max_rounds:
  dispatch -> bounded wait -> explicit terminal result -> coordinator acceptance
    pass            -> converged
    fail / partial  -> coordinator verdict
        progress    -> round packet -> round commit -> re-dispatch (r+1)
        no_progress -> escalate to user
    (r > max_rounds -> escalate to user)
```

Each round is recorded in agent-brain's run-state ledger, and each round's
task-owned changes are committed through agent-brain `round-commit` with an
explicit file list so partial work is preserved; push stays convergence-only.

Do not claim that `zcode_subagent`, `codex_subagent`, `zcode_mcp`, or
`pi_subagent` is available merely because the protocol supports it. If the
runtime tool required by the harness-mandated backend is unavailable, report a
blocked handoff and let the user choose another target/backend.

The target choice may be recorded in the plan when known, but `delegate` must
obtain it before creating a ready packet or starting current-session
implementation.

## Parallel DAG Task Groups

Use this section only when the approved plan has `orchestration_mode:
parallel_dag` and the target is `subagent`:

- Start from the source execution plan DAG. If the DAG is missing, stale, or
  ambiguous, hand back to plan mode instead of inventing a new one.
- Assign the same `parallel_group` and a stable `feature` value to all tasks.
- Assign a `phase` that reflects the DAG layer, such as `contract`, `backend`,
  `frontend`, `integration`, or `cleanup`.
- Preserve the execution plan unit IDs in each task packet with `plan_unit_id`.
- Put only root nodes with no unmet dependencies in `ready`.
- Put approved downstream nodes in `blocked` until their dependencies are
  accepted or merged.
- Add `unblocks` to each task when completing it can make downstream tasks
  runnable.
- Prefer a contract-first split when possible:

```text
contract/schema/API task
  -> backend task
  -> integration task

contract/schema/API task
  -> frontend task
  -> integration task
```

Do not use stacked branches by default. Prefer accepting the dependency task,
then creating or rebasing downstream task branches from the updated base
branch.

## Document Artifact Mode

Follow the shared document-artifact rules in the router SKILL.md. Subagent task
files use `tasks/draft/` by default, `tasks/ready/` only when explicitly
approved for subagent execution, and `tasks/blocked/` for approved but
dependency-blocked parallel tasks (or keep them in draft with `status:
blocked` when the blocked directory is not configured). A current-session
target does not need a task file. Use stable filenames such as
`tasks/draft/<feature-slug>-whole-goal.md` or
`tasks/draft/<feature-slug>-backend.md`.

## Handoff Workflow

1. Confirm readiness and target.
   - Identify whether the source plan is approved, draft, or ambiguous.
   - Read `orchestration_mode` and obtain `execution_target=current_session`
     or `execution_target=subagent`. If either decision is missing, return the
     decision needed and stop.
   - When the target is `subagent`, resolve `execution_backend` from the
     current harness: `zcode_subagent` in a ZCode session; `codex_subagent`,
     or `zcode_mcp` when its bridge is exposed, in a Codex session; `pi_subagent`
     when the native `subagent` tool is present in a Pi session. Do not
     offer a backend the current harness cannot serve.
   - Before creating a ready packet or dispatching the first subagent of this
     conversation, run the session model gate from `$subagent-orchestration`.
     Store `selected_subagent_model` in conversation state and in each task
     packet. If no model was explicitly supplied, stop and ask the user for the
     exact `provider/model`; do not infer it from profile defaults or tier
     recommendations. Later new child packets reuse it without another prompt.
     For `codex_subagent`, record `provider_resolution: host_inherited` because
     the native spawn schema has no provider parameter; preserve the confirmed
     model and thinking choice and report a blocker if the requested provider
     cannot be represented.
     A current-session handoff leaves `execution_backend` unset or empty; never
     infer a backend from the word subagent.
   - If approval is ambiguous, write draft tasks only; do not place tasks in `ready`.
   - If a `parallel_dag` task depends on another task that is not already done,
     accepted, merged, or explicitly satisfied, do not place it in `ready`;
     mark it `blocked` or keep it in draft.
   - If the implementation plan is missing or too vague, hand off to plan mode.

2. Route the target.
   - For `current_session`, hand the approved plan directly to `$implement-plan`
     and record that no subagent packet was created.
   - For `subagent` + `batch`, create exactly one whole-goal task packet.
   - For `subagent` + `parallel_dag`, select runnable nodes from the source
     DAG. Preserve DAG unit IDs and dependencies; group tightly coupled nodes
     only when the mapping does not change dependency semantics.
   - Dispatch each subagent packet through the selected backend adapter. If
     the adapter runtime is unavailable, leave the handoff blocked rather than
     claiming that dispatch occurred.
   - Keep shared contracts, schemas, migrations, generated artifacts, and
     cross-cutting config under a single writer.
   - If mapping would change the source DAG shape or acceptance semantics, hand
     back to plan mode.

3. Define dependency and parallelism rules.
   - For `batch`, record `Depends On: None`, `Can Run In Parallel With: None`,
     and the serial writer rule; do not invent node dependencies.
   - For `parallel_dag`, reuse the source DAG before writing task files.
   - List `Depends On`, `Unblocks`, and parallel-safe peers for every task.
   - List `Must Not Run In Parallel With` for shared files, public contracts,
     database migrations, generated artifacts, or unclear boundaries.
   - Assign a `parallel_group` and `mutex` values when multiple tasks belong to
     the same approved plan. Record the low-level `parallel_mode` for each
     task.

4. Define write ownership.
   - Specify allowed paths, modules, APIs, config, tests, and docs.
   - Specify forbidden writes for shared contracts, unrelated modules, migrations, lockfiles, generated artifacts, or files owned by another task.
   - If write ownership cannot be made clear, keep the task serial and mark the risk.

5. Define branch and worktree isolation after impact analysis.
   - A current-session target does not need a subagent branch or worktree.
   - Read-only parallel tasks do not need a branch or worktree.
   - Serial tasks with disjoint ownership may reuse the current checkout; the orchestrator must serialize writes.
   - Assign one branch and one git worktree per task only when tasks must write simultaneously, such as `task/<remote-task-id>` and `.worktrees/<remote-task-id>`.
   - Do not allow two write agents to run concurrently in the same working tree or on the same branch.
   - Shared contract, schema, migration, generated artifact, dependency manifest, and lockfile tasks should be serial unless the plan explicitly assigns single-writer ownership.

6. Write the subagent task packet when the target is `subagent`.
   - Include source artifacts, objective, whole-goal or node scope, exclusions,
     required context, implementation instructions, verification, acceptance
     criteria, blocking conditions, and feedback format.
   - Include branch and PR expectations when known.
   - When the target uses agent-brain, create or update its Task Pack from this packet; do not make the remote Markdown acceptance list a second source of truth.
   - Keep instructions concrete enough for `$implement-plan` to start without
     further discovery beyond reading the referenced files.
   - For a `batch` packet, require one active goal covering the complete plan;
     internal steps and checks must not trigger parent-agent interaction.

7. Define execution feedback and waiting.
   - Require the subagent to report changed files, tests run, result, deviations,
     blockers, attempt number, and PR or commit reference.
   - Require the subagent to return only after the whole `batch` goal or
     assigned DAG node has reached an explicit `completed`, `blocked`, or
     `failed` state, unless a human decision is required.
   - The coordinating agent must set `acceptance_phase=locked` and use the
     runtime's bounded wait mechanism when available. The wait window is only
     the duration of that observation call, not a child ETA or deadline. On a
     timeout, keep the same run identity and wait again with backoff; do not
     treat it as progress, completion, or permission to accept.
   - While a required child is active, avoid repeated polling, unchanged-context
     reads, acceptance commands, and unrelated work. Start node acceptance only
     after the assigned child explicitly returns `completed`; for integration,
     wait for all required children. `blocked` and `failed` are terminal reports
     for repair or escalation, not acceptance passes.
   - Require blockers to preserve current branch state and explain the missing
     decision or failing check.

8. Define the round budget.
   - Record `round_policy.max_rounds` (default 3) in the packet; the loop runs
     at most that many rounds.
   - After a failed or partial round, the coordinating agent judges `progress`
     or `no_progress` and creates one consolidated round packet containing all
     known findings, failed checks, expected corrections, and the same overall
     acceptance. Do not send piecemeal prompts.
   - Record each round through agent-brain `round-commit` (explicit file list,
     `Round:` / `Acceptance:` trailer) so partial work is preserved and
     traceable.
   - A `no_progress` verdict, an exhausted budget, or a remaining blocker
     stops automation and returns the evidence and choices to the user.

9. Finish with routing.
   - If tasks are draft, state what approval is needed before moving them to ready.
   - If tasks are blocked by dependencies, state which upstream task or merge must complete first.
   - If tasks are ready, state the recommended claim or execution order.
   - State the promotion rule for downstream tasks, for example "after `task/api-contract` is accepted, promote `task/backend` and `task/frontend` to ready."
   - State any mapping from execution plan units to remote tasks.
   - If `execution_target=current_session`, hand off to `$implement-plan`.
     Otherwise leave the subagent task ready for pickup.

## Task Packet Format

Use this structure unless the user provides a stricter format:

```markdown
---
id: <remote-task-id>
type: remote_task
status: draft
created_at: <date>
updated_at: <date>
orchestration_mode: batch | parallel_dag
execution_target: subagent
execution_backend: zcode_subagent | codex_subagent | zcode_mcp | pi_subagent
selected_subagent_model: <explicit provider/model chosen for this conversation>
provider_resolution: explicit | host_inherited | unavailable
logical_role: <required for a subagent; resolved by $subagent-orchestration>
subagent_scope: user | project | both  # Pi only; defaults to user
context_policy: fresh | fork | retained_resume
lifecycle_policy: <foreground/background, timeout, status/wait, stop/resume, failure handling>
join_policy: required | opportunistic
continue_while_child_active: none | declared_disjoint_only
acceptance_phase: preflight | locked | node | integration
acceptance_barrier: none | child_terminal | all_required_children_terminal
wait_semantics: event_driven_mailbox
wait_window_ms: <bounded wait call; not a child deadline>
timeout_action: rewait_same_identity | run_declared_disjoint | escalate_user
acceptance_scope: batch | node_and_batch
round_policy:
  max_rounds: 3
  converged_when: canonical_acceptance_pass
  progress_judgment: coordinator
  no_progress_action: escalate_user
  round_commit: explicit_file_list
sources:
  - <source artifact path or issue>
related:
  prd: <path>
  trd: <path>
  execution_plan: <path>
plan_unit_id: <root for batch, or execution-plan-unit-id for parallel_dag>
plan_id: <stable execution plan id>
source_plan_sha256: <sha256 of the canonical execution plan>
base_commit: <commit from which the task must start>
task_id: <outer Task Pack or issue id>
feature: <feature-id>
phase: <contract|backend|frontend|integration|cleanup>
depends_on: []
unblocks: []
parallel_group: <group-id>
required_capabilities:
  - <capability required by the source plan node>
required_skills:
  - <skill name required by the source plan node>
source_artifacts:
  - <PRD/TRD/execution plan/Task Pack path>
source_hash: <sha256 of the canonical source artifact or Task Pack>
source_task_pack_sha256: <sha256 of the canonical Task Pack, or "not applicable">
acceptance_ids:
  - <canonical acceptance id>
evidence_required:
  - <acceptance.json, test report, scope result, or manual acknowledgement>
mutex: []
parallel_mode: <read_only_parallel|serial_same_worktree|concurrent_write_worktree|serial_shared_writer>
branch: <required only for concurrent_write_worktree>
worktree: <required only for concurrent_write_worktree>
write_ownership:
  - <allowed path or module>
forbidden_writes:
  - <forbidden path or module>
---

# Subagent Task: <Title>

## Objective

<One concrete implementation outcome.>

## Scope

- <In-scope work>

## Exclusions

- <Out-of-scope work>

## Required Context

- <Files, docs, issues, or commands to inspect first>

## Required Capabilities And Skills

- Capabilities: <tool access, domain knowledge, or execution ability>
- Skills: <skill names or "None">

## Dependencies And Parallelism

- Orchestration mode: <batch|parallel_dag>
- Execution target: `subagent`
- Execution backend: `zcode_subagent` | `codex_subagent` | `zcode_mcp` | `pi_subagent`
- Subagent name: <required when backend=pi_subagent; must exist in `~/.pi/agent/agents/` or `.pi/agents/`>
- Subagent scope: `user` | `project` | `both` (Pi only; default `user`)
- Acceptance scope: <batch|node_and_batch>
- Plan unit: <root for batch, or execution-plan-unit-id for parallel_dag>
- Feature: <feature-id>
- Phase: <phase>
- Depends on: <tasks or "None">
- Unblocks: <tasks or "None">
- Can run in parallel with: <tasks or "None">
- Must not run in parallel with: <tasks or "None">
- Mutex: <shared resources or "None">

## Branch And Worktree

- Parallel mode: <read_only_parallel|serial_same_worktree|concurrent_write_worktree|serial_shared_writer>
- Branch: `<branch or None>`
- Worktree: `<worktree or None>`
- Concurrency rule: read-only tasks may share a checkout; serial-write tasks may reuse a checkout only under orchestration; simultaneous write tasks require separate branch/worktree.

## Write Ownership

- Allowed writes: <paths/modules>
- Forbidden writes: <paths/modules>

## Execution Steps

For `batch`, execute the complete approved plan in this one goal. Internal
steps may be sequential, but must not trigger parent-agent interaction.

1. <Step>
2. <Step>

## Verification

- `<command>`: <expected result>

## Acceptance Criteria

- <Observable pass/fail condition>

For `batch`, these are the complete-goal acceptance conditions. For
`parallel_dag`, these are the assigned node conditions; the coordinating actor
also performs final integration acceptance.

## Task Contract Bridge

- If agent-brain is used, the Task Pack is the outer contract and its `acceptance` list is canonical.
- Copy this packet's `orchestration_mode`, `execution_target`,
  `execution_backend`, `plan_id`, `source_plan_sha256`, `base_commit`, `task_id`,
  `source_artifacts`,
  `source_hash`, `source_task_pack_sha256`, `acceptance_ids`,
  `required_skills`, and `plan_unit_id` into the Task Pack linkage fields.
- Generate the compatibility Acceptance Pack from the Task Pack and retain its source hash; do not edit acceptance checks independently on the remote side.
- Evidence must identify a path, overall status, exit codes, git head, changed files, and source hashes; manual checks must record explicit acknowledgement.
- Done requires passing acceptance evidence plus a clean scope check. A text claim that tests passed is not evidence.

## Blocking Conditions

- <When the subagent should stop and report back>

## Delivery And Feedback

- Changed files:
- Tests run:
- Result: `completed` | `blocked` | `failed`
- Attempt: `1` | `2`
- Deviations:
- Blockers:
- PR/commit:
```

## Output Format

Answer in the user's language unless they request otherwise. Prefer:

```markdown
## Execution Handoff

- orchestration_mode: `batch` | `parallel_dag`
- execution_target: `current_session` | `subagent`
- execution_backend: `zcode_subagent` | `codex_subagent` | `zcode_mcp` | `pi_subagent`
- selected_subagent_model: `<session-selected provider/model; required when target=subagent>`
- provider_resolution: `explicit` | `host_inherited` | `unavailable`
- logical_role: `<resolved by $subagent-orchestration>`
- subagent_scope: `user` | `project` | `both` (Pi only)
- context_policy: `fresh` | `fork` | `retained_resume`
- lifecycle_policy: `<foreground/background, timeout, status/wait, stop/resume, failure handling>`
- join_policy: `required` | `opportunistic`
- continue_while_child_active: `none` | `declared_disjoint_only`
- acceptance_phase: `preflight` | `locked` | `node` | `integration`
- acceptance_barrier: `none` | `child_terminal` | `all_required_children_terminal`
- wait_semantics: `event_driven_mailbox`
- wait_window_ms: `<bounded wait call; not a child deadline>`
- timeout_action: `rewait_same_identity` | `run_declared_disjoint` | `escalate_user`
- approval: `<pending|approved>`

If `execution_target=current_session`, report the direct `$implement-plan`
handoff and do not create a remote task table. If `execution_target=subagent`,
use the table below.

## Prepared Subagent Tasks

| Task | Status | Path/Issue | Depends On | Parallel Group |
|---|---|---|---|---|
| <task> | <draft/ready> | <path or issue> | <deps> | <group> |

## Execution Order

<For batch: one whole-goal task. For parallel_dag: claim order, merge order,
and parallel-safe groups.>

## Approval Needed

<Execution target, plan approval, or downstream dependency confirmation; or
"None".>

## Notes

<Residual risks, shared-write warnings, or missing context.>
```

For a batch target, the table contains one whole-goal task and one final
acceptance scope. For a parallel DAG, state node dependencies, node acceptance,
and final integration acceptance. For one small task, compress the table but
still state status, path or issue, dependencies, and approval state.
