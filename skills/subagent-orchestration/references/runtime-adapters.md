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

## Pi + Nico

- Resolve agents through Nico's discovered builtin, user, and project profiles.
- Inspect capabilities before launch when the role, tools, model, or child
  extension matters.
- Use `async: false` only when the coordinator must block and consume the result
  immediately. Use background execution for long research, builds, reviews, or
  monitoring, then record the exact run identity and use status/wait.
- Use `fresh` for independent read-only roles. Use `fork` only when inherited
  parent history is necessary. Use retained `resume` only when status reports a
  resumable persisted child.
- Prefer `outputMode: "file-only"`, bounded output, structured output, and
  explicit artifact paths for large results.
- `researcher` and `evidence-auditor` require the child's web tools to be
  registered when external web evidence is needed.
- A provider failure after tool side effects is a failed/paused lane, not an
  automatic replay. Capture the diff before a new bounded repair or resume.

## Codex

- Use the native multi-agent spawn/wait/send tools exposed by the current
  session. Do not call Pi/Nico tools through a bridge unless the execution
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
