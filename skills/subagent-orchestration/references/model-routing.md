# Model Routing Policy

Use model routing as a deployment policy, not as part of a logical role definition.
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
2. If no explicit choice exists, recommend a profile and ask the user to
   confirm the resolved model: `fast`, `balanced`, or `deep`; a profile is never
   an authorization to change the user's selection.
3. Resolve the selected role through the profile for the actual runtime adapter
   (Pi, ZCode, Codex, or another adapter). A model configured only for another
   runtime is not a valid choice.
4. Apply the profile's thinking level and fallback only after checking that the
   model supports them. Fallback is an availability recovery path, not a reason
   to change task scope or silently cross runtimes.
5. State the resolved model, thinking level, context policy, execution mode,
   concurrency, and output contract in the delegation packet.

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
  `subagents.defaultThinking`, and `agentOverrides`. Do not enable
  `modelScope` from a profile projection because it could reject an explicit
  user-selected model; users may configure model scope independently.
- `~/.pi/agent/extensions/subagent/config.json`:
  concurrency, spawn, async-run, and parallel limits.

`kb subagent use <profile> --runtime pi` may generate this projection. After a
projection, `/reload` or a new Pi session is required. The generated runtime
files are local state and must not be added to the shared agents repository.
