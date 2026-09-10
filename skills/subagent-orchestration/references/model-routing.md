# Model Routing Policy

Use model routing as a deployment policy, not as part of a logical role definition.
The logical model is the selection key; providers are ordered delivery routes.
The shared policy source, when installed and enabled, is:

```text
~/Developer/agents/subagent-policies.json
```

It may be inspected through `kb subagent list|show|check`. If its top-level
`recommendationEnabled` flag is `false`, ignore the policy entirely until the
user enables recommendations. Direct subagent delegation remains available.
The policy contains logical model references and runtime-specific mappings, so
skills must not hard-code provider or model IDs.

## Selection order

1. Preserve an explicit user-selected `provider/model` and thinking level.
2. If no explicit choice exists, recommend a profile and show its logical model,
   primary `provider/model`, and ordered same-model routes. Ask the user to
   confirm the exact primary `provider/model` and route policy; a profile is
   never an authorization to change the user's selection.
3. Resolve the logical model through the ordered provider routes for the actual
   runtime adapter (Pi, ZCode, Codex, or another adapter). A route configured
   only for another runtime is not a valid choice.
4. Apply the profile's thinking level and try the next provider only for an
   availability failure. Provider fallback must keep the same logical model;
   never silently change the model, task scope, or runtime.
5. State the logical model, selected route, thinking level, context policy,
   execution mode, concurrency, fallback order, and output contract in the
   delegation packet.

## Default routing heuristic

- `scout`, small lookups, and mechanical read-only work: `fast` / low.
- Ordinary implementation and focused review: `balanced` / medium; use high
  thinking only when the review contract justifies it.
- Architecture tradeoffs, root-cause analysis, and high-risk review: `deep` /
  high, with a small fanout or a single oracle.
- Product/UX ambiguity is an intent problem, not automatically a deep-code
  problem; use the configured intent-capable profile when one exists.

Complexity classification is advisory. Do not infer permission, write ownership,
acceptance, or release authority from a model tier.

## Limits

Keep persistent safety ceilings in the runtime config and use profile limits as
workflow defaults:

- `globalConcurrencyLimit`: simultaneous children in one run.
- `maxSubagentSpawnsPerSession`: cumulative child launches in one parent session.
- `maxSubagentSpawnsPerRun`: cumulative launches in one workflow tree.
- `maxActiveAsyncRunsPerSession`: simultaneous top-level async workflows.
- `usageBudget`: optional workflow-level reported token/cost budget; it blocks
  later launches after reconciliation but does not stop children already running
  and is not a provider billing cap.

Writers should not receive tight hard tool or usage budgets unless the task has
an explicit checkpoint and handoff path. Prefer a narrow task, one writer per
worktree, and an elapsed deadline with enough margin.

## Runtime projection

For Pi, the native settings/projection is:

- `~/.pi/agent/settings.json`: `subagents.defaultModel`,
  `subagents.defaultThinking`, and `agentOverrides`. A profile projection may
  emit provider/model route strings and same-model `fallbackModels`. Do not
  enable `modelScope` from a profile projection because it could reject an
  explicit user-selected model; users may configure model scope independently.
- `~/.pi/agent/extensions/subagent/config.json`:
  concurrency, spawn, async-run, and parallel limits. Pi native fallback only
  covers the retryable provider/model failures documented by the runtime (most
  reliably before tool activity); Codex's native global config remains a single
  active provider, so per-request fallback requires the upper orchestrator.

`kb subagent use <profile> --runtime pi` may generate this projection. After a
projection, `/reload` or a new Pi session is required. The generated runtime
files are local state and must not be added to the shared agents repository.
