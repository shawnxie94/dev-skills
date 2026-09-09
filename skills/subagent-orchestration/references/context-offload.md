# Context Offload

The goal is not merely to use another model. The goal is to keep the
coordinator's active context small while preserving evidence and traceability.

## When to offload

Delegate when one or more apply:

- external sources, PDFs, browser pages, or repository files are numerous or
  individually large;
- search, extraction, or validation output is likely to consume a material
  portion of the coordinator context;
- the work is independently verifiable and can return a bounded artifact;
- an independent review or evidence pass would reduce anchoring risk;
- a long-running test, build, browser, or CI operation should not block the
  reasoning loop.

Keep the work in the coordinator when it is small, interactive, host-only, or
requires continuous decisions that cannot be expressed in a bounded packet.

## Research pattern

```text
coordinator: question, decision criteria, exclusions
  -> researcher: source collection and first synthesis
  -> evidence-auditor: independent claim/source verification
  -> coordinator: final research brief or requirement packet
```

Research children should return a claim/source index, uncertainty list, and
artifact references. Use `outputMode: file-only` or the runtime equivalent for
large reports. The coordinator reads only the relevant sections instead of
injecting complete source content.

For Pi/Nico's built-in web roles, verify that the child has the required web
access tools. A foreground child does not automatically receive ambient parent
extensions; use the configured child extension path or a background child when
that is the supported path.

## Codebase and verification pattern

```text
scout -> bounded file/line/risk handoff -> coordinator or worker
worker -> reviewer and/or verifier -> coordinator acceptance
```

Pass file paths, plan IDs, commands, and acceptance criteria rather than full
source dumps. For noisy commands, persist logs and return exit codes, tails,
artifact paths, and an explanation of what the command proves.

## Output budget

Prefer, in order:

1. structured output with bounded arrays and strings;
2. a concise inline decision card plus artifact path;
3. a file-only report that the coordinator reads selectively;
4. full inline prose only for small results.

Never use the parent context as a transcript archive. Run artifacts, source
files, and acceptance evidence are the durable record; the parent receives the
minimum projection required for the next decision.

## Context choice

- `fresh`: independent scout, researcher, auditor, reviewer, or verifier.
- `fork`: implementation only when parent history is materially required and
  the inherited context is within budget.
- `resume`: a validated new turn for a retained child; never claim same-request
  recovery.

A fresh child still needs explicit project instructions, allowed paths, plan
references, and output requirements. Fresh does not mean context-free from the
repository; it means it does not inherit the coordinator's conversation.
