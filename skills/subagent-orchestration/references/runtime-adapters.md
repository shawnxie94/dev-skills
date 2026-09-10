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
