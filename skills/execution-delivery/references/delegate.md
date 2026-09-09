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
- Do not mark a subagent task ready unless the user or source artifact clearly indicates approval and the execution target is explicit.
- A subagent handoff is one goal and one final return by default. The coordinating agent waits for a terminal `completed`, `blocked`, or `failed` result; only `completed` starts acceptance. If acceptance fails, it may issue one consolidated repair packet; a second failed attempt or unresolved blocker escalates to the user.

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
current harness, not by preference:

- ZCode session (native `Agent` tool present): `execution_backend=zcode_subagent`. Never spawn Codex children from ZCode (`codex_subagent` is unavailable here), and never wrap ZCode subagents in MCP calls (`zcode_mcp` is a cross-harness bridge, not in-session delegation).
- Codex session (`multi_agent_v1` tools present): `execution_backend=codex_subagent`, or `zcode_mcp` only when the ZCode MCP bridge tools are actually exposed in that session.
- Pi session (native `subagent` tool present, spawned by the `pi-coding-agent` `subagent/` extension): `execution_backend=pi_subagent`. Never dispatch from Pi to ZCode or Codex children; the Pi `subagent` tool is the in-session delegation mechanism.
- Neither tool family is available: report a blocked handoff.

All adapters execute the packet; no adapter's success declaration is the final
acceptance. The coordinator waits for an explicit `completed` result before
running canonical acceptance. The protocols below describe supported
integrations; they do not imply that the current environment exposes every
named tool.

| Backend | Dispatch | Long wait / status | One consolidated repair | Runtime boundary |
|---|---|---|---|---|
| `zcode_subagent` | Native `Agent` tool, one call per packet with a self-contained prompt | Foreground call blocks until the final message; `run_in_background` + `TaskOutput` (blocking) for long nodes; no polling | `SendMessage` to the same agent, once, with the complete repair packet | ZCode native child implementation and tests |
| `codex_subagent` | `multi_agent_v1__spawn_agent` with one complete goal or assigned DAG node | `multi_agent_v1__wait_agent`; bounded wait, no busy polling | `multi_agent_v1__send_input` to the same agent, once, with the complete repair packet | Codex child implementation and internal verification |
| `zcode_mcp` | `mcp__zcode_codex__zcode_dispatch` | `wait_ms` and terminal status; inspect with `zcode_status`, `zcode_messages`, or `zcode_diff` only when needed | `zcode_continue` once on the same task with the complete repair packet | ZCode code implementation and repository tests when explicitly available |
| `pi_subagent` | `subagent` tool (single mode) with one complete goal or assigned DAG node; each call spawns an isolated `pi` process | Tool call blocks until the child process exits with its final message; no polling | Re-spawn a new `subagent` single-mode call with the complete repair packet, the source packet, and `attempt: 2` | Pi child implementation and repository tests |

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
- Only after `completed`, run the coordinator's acceptance. If it fails, send
  one complete consolidated repair packet to the same agent via `SendMessage`
  (the agent resumes in the background with its prior context). A second
  failure or unresolved blocker goes to the user.

### `codex_subagent`

Codex sessions only; unavailable from ZCode.

- Call `multi_agent_v1__spawn_agent` once for a `batch` whole-goal packet, or
  once per runnable `parallel_dag` node. The child receives one active goal and
  must not return after an internal step.
- Wait with `multi_agent_v1__wait_agent` for a bounded interval. Do not use
  repeated status retrieval or busy polling while the agent is unchanged.
- Require the final child response to include `completed`, `blocked`, or
  `failed`, plus changed files, tests, deviations, blockers, and `attempt`.
- Only after `completed`, run the coordinator's acceptance. If it fails, send
  one complete consolidated repair through `multi_agent_v1__send_input` to the
  same agent. A second failure or unresolved blocker goes to the user.

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
- After a failed coordinator acceptance, call `zcode_continue` at most once
  with one complete consolidated repair packet. If ZCode requests permission
  or user input through `zcode_respond`, do not auto-approve; return a user
  blocker. Use `zcode_stop` only when the user or coordinator explicitly asks
  to stop.
- ZCode may implement code and run repository tests. Browser, desktop,
  visual, and other host-only acceptance capabilities remain with the
  coordinating session unless the adapter explicitly declares that capability
  and the approved plan authorizes it.

### Subagent Agent Resolution (Pi)

The Pi `subagent` tool resolves the `agent` parameter by **name** from the
user-level agent registry (`~/.pi/agent/agents/*.md`) and, when invoked with
`agentScope: both` or `project`, the nearest project-level registry
(`.pi/agents/*.md`). Each registry entry is a Markdown file with YAML
frontmatter declaring `name`, `description`, optional `tools`, and optional
`model`; the body becomes the subagent's appended system prompt. If the
requested name does not appear in the resolved registry, the tool returns
exit code `1` with stderr starting with `Unknown agent: "<name>"` — a hard
dispatch failure, not a soft warning.

Because the registry is user-owned and may include custom agents (e.g.
`luna-audit`, `code-review`, `release-bot`), the skill must not hardcode
agent names. Resolve at dispatch time by following this sequence:

1. Read the packet's `subagent_name` (required when
   `execution_backend=pi_subagent`). If absent, stop and report a missing
   field — do not silently pick a default that may not exist on this
   machine.
2. Confirm the named agent exists in the registry. Prefer a one-line
   pre-dispatch probe (list `~/.pi/agent/agents/*.md` and, when the packet
   sets `subagent_scope: both|project`, also `.pi/agents/*.md`); match on
   the `name` frontmatter field. If the probe is skipped, accept that
   dispatch may fail and treat an `Unknown agent` result as `blocked`.
3. Set `agentScope` from the packet's `subagent_scope` (`user` is the Pi
   default and matches the bundled `subagent/` example; `both` is required
   only when the named agent lives in `.pi/agents/`).
4. Forward `subagent_name` and `subagent_scope` into the `subagent` tool
   call alongside `task` and `cwd`. Do not invent additional arguments;
   the tool ignores unknown fields and other options (model, thinking,
   tools) come from the agent's own frontmatter, not the call site.

Conventional mapping from packet contract to a known Pi agent name. These
are the bundled `subagent/` example agents; treat them as the **suggested**
mapping and let users override per packet:

| Packet contract | Conventional Pi agent | Why |
|---|---|---|
| `parallel_mode: read_only_parallel`, no writes | `scout` | Read-only recon, fast model, returns compressed context |
| `parallel_mode: read_only_parallel`, planning only | `planner` | Read-only plan synthesis; must not edit |
| Whole-goal `batch` implementation | `worker` | Full default tool set, isolated context, write-enabled |
| `batch` followed by review | `reviewer` (then `worker` for repair) | Read-only review, then re-dispatch worker |
| Audit-style bounded conclusion document | a user-defined `*-audit` agent | e.g. `luna-audit`: read-only, narrow write |

User-defined agents override these conventions when they exist. Always
re-verify the name against the live registry; an agent file deleted from
`~/.pi/agent/agents/` must not be silently substituted.

**Unknown-agent handling.** If dispatch returns `Unknown agent: "<name>"`,
treat the task as `blocked`, not `failed`. The blocker message must list the
discovered agent names from the registry so the user can either install the
missing agent, pick an existing one, or switch `execution_target` to
`current_session`. Do not retry with a guessed name and do not downgrade
`pi_subagent` to another backend without user approval.

### `pi_subagent`

Pi sessions only; unavailable from ZCode or Codex. The coordinating session
runs the `pi-coding-agent` with the `subagent/` extension loaded, exposing the
native `subagent` tool.

- Dispatch through the `subagent` tool in single mode:
  `{ agent, task, cwd, agentScope }`. The `agent` field must come from the
  packet's `subagent_name` (see "Subagent Agent Resolution (Pi)"); never
  guess. The `agentScope` field follows the packet's `subagent_scope`
  (default `user`). The `task` must be a self-contained prompt carrying the
  complete task packet (or its file path plus a one-paragraph objective),
  the canonical plan path, and every command the child must run. A fresh
  `pi` subagent starts with no conversation context, so the prompt must not
  rely on session history or shorthand established earlier.
- Choose the agent by the packet's `required_capabilities`,
  `write_ownership`, and `parallel_mode`, not by ad-hoc preference. See the
  conventional mapping table in "Subagent Agent Resolution (Pi)"; the
  registry on the host machine is the source of truth, not the
  convention.
- The tool call blocks until the child `pi` process exits and returns its
  final message; that message is the terminal result. For concurrent
  `parallel_dag` dispatch, issue multiple `subagent` calls in one message so
  they run in parallel, or use the tool's `tasks` array (max 8 tasks, 4
  concurrent). Do not busy-poll.
- Require the final message to state `completed`, `blocked`, or `failed`,
  plus changed files, tests, deviations, blockers, and `attempt`. The child's
  final message is visible only to the coordinator, not to the user — relay
  the outcome after acceptance.
- Only after `completed`, run the coordinator's acceptance. If it fails,
  re-spawn a new single-mode `subagent` call with the complete consolidated
  repair packet, the source packet, and `attempt: 2`. Unlike ZCode/Codex
  adapters, a Pi subagent is an isolated process with no resumed context, so
  the repair re-dispatch must be fully self-contained: all findings, failed
  checks, expected corrections, and the same overall acceptance. A second
  failure or unresolved blocker goes to the user; never send piecemeal repair
  prompts.
- Pi subagents inherit the dispatching session's active model and thinking
  level unless the agent definition sets `model`; account for this when
  selecting agents with specific cost or capability requirements.

The adapter contract is:

```text
dispatch once → bounded wait → explicit terminal result → coordinator acceptance
                         ↘ one consolidated repair → bounded wait → acceptance
```

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
   - The coordinating agent must use the runtime's bounded wait mechanism when
     available, avoid repeated polling or unchanged-context reads, and not
     start acceptance until the subagent explicitly returns `completed`.
     `blocked` and `failed` are terminal reports for repair or escalation, not
     acceptance passes.
   - Require blockers to preserve current branch state and explain the missing
     decision or failing check.

8. Define the repair limit.
   - If final batch acceptance or DAG integration acceptance fails, the
     coordinating agent creates one repair packet containing all known findings,
     failed checks, expected corrections, and the same overall acceptance.
   - Retry the same goal at most once. Do not send piecemeal repair prompts.
   - If the second attempt fails or remains blocked, stop automation and return
     the evidence and choices to the user.

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
subagent_name: <required when execution_backend=pi_subagent; agent registry name>
subagent_scope: user | project | both  # required when execution_backend=pi_subagent; defaults to user
acceptance_scope: batch | node_and_batch
attempt_policy:
  max_attempts: 2
  repair: consolidated_repair_packet
  escalate_after_exhaustion: user_decision
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
- subagent_name: `<agent registry name, required when backend=pi_subagent>`
- subagent_scope: `user` | `project` | `both` (Pi only)
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
