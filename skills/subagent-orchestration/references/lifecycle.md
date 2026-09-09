# Delegated Lifecycle

The coordinator must distinguish task state from model transport state. A child
may have completed tool side effects even when its final model turn failed.

## Before launch

1. Confirm the approved goal or bounded read-only question.
2. Resolve the logical role and actual runtime adapter.
3. Capture the current repository/worktree/branch state for mutation-capable
   work.
4. Set context, timeout, tool/usage budget, isolation, output, and acceptance
   policy explicitly when defaults could change behavior.
5. State what the child must not modify or assume.

## During execution

| Situation | Coordinator action |
|---|---|
| Foreground | Wait for the terminal result; do not start a sibling writer in the same checkout |
| Background | Record the exact run identity; use the runtime's status/wait surface |
| Need to redirect | Use runtime-native steering and retain its delivery receipt |
| Need to stop | Stop only the intended run/child; preserve the partial state |
| Near timeout | Ask a writer for a checkpoint after its current tool returns |
| Partial output | Accept only after checking the declared output and evidence contract |

## Terminal-state policy

- `completed`: coordinator still performs final acceptance.
- `blocked`: preserve the blocker and do not substitute an unapproved runtime,
  model, or role.
- `failed`: capture error, partial side effects, and the exact retry boundary.
- `paused`: resume only when the runtime confirms a persisted session and the
  task is safe to continue.
- `stopped`: treat as non-resumable unless the runtime explicitly documents a
  safe restart path.
- `timed_out`: do not assume no side effect; inspect the worktree and artifacts.

## Recovery policy

A provider/network failure is not automatically an in-flight resume. For a
read-only child, a fresh retry may be safe after recording the failure. For a
writer:

1. Capture `git diff --name-only`, `git diff --stat`, and relevant status/artifacts.
2. Determine whether the last tool could have produced a side effect.
3. Prefer a retained session resume when the runtime validates it and the task
   contract supports a new turn.
4. Otherwise issue one bounded repair packet describing the current state; do
   not replay the entire original task blindly.
5. After one failed repair attempt, return control to the user.

A retained resume starts a new model turn from stored context. It does not prove
that the original HTTP request, tool call, or process was resumed.

## Runtime-neutral result

The coordinator should normalize runtime results to:

```text
role:
runtime_adapter:
run_id:
state:
context_mode:
execution_mode:
changed_files:
tests_or_checks:
artifacts:
error_or_blocker:
retry_or_resume_decision:
residual_risk:
```

Do not infer success from a child prose sentence, process exit code alone, or
presence of changed files.
