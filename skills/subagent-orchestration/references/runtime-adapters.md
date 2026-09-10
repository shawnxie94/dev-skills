# Runtime Adapters

The logical role contract is shared; invocation and lifecycle semantics are
runtime-specific.

## Shared Model-Selection Rule

Before the first delegated run in a conversation, obtain and record the user's
explicit `provider/model` choice unless the current request already supplied
one. Reuse it for every subsequent new child dispatch in that conversation;
do not ask again unless the user explicitly changes it. Preserve the choice
exactly. If the selected model is unavailable, unsupported by the adapter,
unauthenticated, or out of quota, report a visible blocker and ask the user for
another choice; never silently substitute a model or provider.

A retained resume may be pinned to its original model. After an explicit model
change, do not resume that child under the old choice; start a new bounded
dispatch when continuation is needed.

Codex's native subagent schema has a model and reasoning-effort override but no
separate provider field. For `codex_subagent`, record the provider as
`host_inherited` when it is not explicitly selectable, preserve any explicit
model and thinking choice, and report a blocker if the user requires a provider
that the adapter cannot represent. Do not claim that a provider was forwarded
when the native tool cannot carry it.

## Pi official SDK

- Use the local SDK-backed `subagent` extension, which creates a persistent
  `AgentSession` with the selected built-in coding tools.
- Use `spawn` for a new child, `status`/`stop` with its `session_id`, and
  `resume` with its persisted `session_file`.
- The extension currently returns bounded inline text and session metadata; it
  does not provide web tools, workflow fan-out, or background wait semantics.
- Use `fresh` for independent read-only roles. Use `fork` only when inherited
  parent history is necessary. Use retained `resume` only when status reports a
  resumable persisted child.
- Keep child prompts and returned output bounded; persist large results in the
  child session rather than copying them into the parent context.
- External web evidence is not available through the minimal Pi child
  extension; use an explicitly configured web-capable runtime when required.
- A provider failure after tool side effects is a failed/paused lane, not an
  automatic replay. Capture the diff before a new bounded repair or resume.

## Codex

- Use the native multi-agent spawn/wait/send tools exposed by the current
  session. Do not call Pi tools through a bridge unless the execution
  contract explicitly selects that bridge.
- Preserve the user-selected model/provider/runtime exactly.
- Send one complete goal or assigned plan node. The child is a leaf unless the
  approved contract explicitly grants orchestration capability.
- `multi_agent_v1__spawn_agent` returns an `agent_id`; use that identity with
  `multi_agent_v1__wait_agent` and `multi_agent_v1__send_input`. The Codex App
  `mcp__codex_app__wait_threads` surface operates on `threadId` and is not a
  substitute for native subagent waiting.
- Native `wait_agent` is an event/mailbox wait: `timeout_ms` bounds this wait
  call, but is not a child ETA, execution deadline, or terminal-state claim.
  If it expires without a terminal result, keep the child `running` and wait
  again with backoff using the same `agent_id`.
- Use `join_policy=required` by default for a batch goal, a dependent node, or
  when the coordinator has no declared disjoint work. After spawn, the next
  action is one bounded `wait_agent` call. If it times out, wait again with
  backoff on the same `agent_id`; do not busy-poll, start unrelated work, or
  finalize while the required child remains non-terminal.
- Use `join_policy=opportunistic` only when the packet explicitly names
  independent work. Complete that work, then join before any dependent step or
  coordinator acceptance.
- When the host exposes a `SubagentStop` lifecycle hook, it can persist or
  inspect the child's terminal message and enforce a child-side stop decision.
  It is an observability/quality-gate callback, not a parent-resume webhook;
  the coordinator still joins through native `wait_agent`. The current native
  adapter does not expose a separate parent callback channel.
- Normalize the final result into the runtime-neutral result shape; native
  message IDs and wait semantics stay in the adapter.

## ZCode

- Use the native `Agent` interface and its background/output controls.
- Keep shared contracts, schemas, generated files, and lockfiles serial.
- Do not spawn Codex or Pi children from a ZCode session as a substitute for the
  native adapter.
- Preserve the selected runtime and model; unavailable capabilities are visible
  blockers.

## Adapter resolution

Resolve the adapter from the live harness, not from the task text:

- Pi native `subagent` tool -> `pi_subagent`;
- Codex native multi-agent tools -> `codex_subagent`;
- ZCode native `Agent` tool -> `zcode_subagent`;
- Codex driving ZCode through an exposed MCP bridge -> `zcode_mcp`.

If the required tool is not present, stop with a blocker. Do not silently use a
shell command, another provider, or another runtime.
