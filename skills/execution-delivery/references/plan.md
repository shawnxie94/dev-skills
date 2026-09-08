# Execution Plan (plan mode)

Mode reference for the `$execution-delivery` skill. First assess whether
parallel execution is worthwhile and let the user choose the coordination
shape. Then convert a clear TRD or technical direction into an executable
sequence, not a re-design or implementation.

## Core Principles

- Start from the whole implementation goal and assess parallelism before
  choosing the plan shape.
- Default to a whole-goal `batch` plan when the work is mostly serial or
  parallelism would not materially reduce delivery time.
- Generate a `parallel_dag` plan only after the user chooses parallel execution
  and independent actors, dependencies, and write boundaries are clear.
- A batch plan may contain one root implementation unit and one final
  acceptance scope. Do not manufacture a DAG merely to describe an internal
  serial checklist.
- A parallel-DAG plan contains node dependencies, actor contracts, node-level
  acceptance, and final integration acceptance.
- Put risky or unknown work early enough to validate assumptions before broad
  implementation.
- Keep write ownership clear. Prefer a single writer for shared files, public interfaces, schemas, migrations, and cross-cutting contracts.
- Give every delegated actor the capabilities, skills, scope, verification,
  evidence, and handoff conditions needed to execute without rediscovery.

## Implementation Handoff Ownership

This mode owns the canonical execution-plan artifact, its selected
`orchestration_mode`, sequencing, write ownership, and plan hash. It does not
implement code or silently choose whether the user wants parallel execution.

The two high-level planning values are:

- `batch`: one whole-goal plan, normally one actor and one final acceptance.
- `parallel_dag`: multiple independently executable units with node acceptance
  and final integration acceptance.

The execution target is chosen during `delegate` unless the user has already
specified it. It is recorded as `execution_target=current_session` or
`execution_target=subagent` in the handoff. A subagent target must also record
`execution_backend`, resolved at delegate time by the current harness
(`zcode_subagent` in a ZCode session; `codex_subagent`, or `zcode_mcp` when
its bridge is exposed, in a Codex session); a
current-session target leaves `execution_backend` unset or empty. Do not use
`execution_mode` for this choice: agent-brain reserves that field for
the `auto|trivial|bounded|full` task lane, while `parallel_mode` remains the
lower-level worktree taxonomy.

When the plan will be implemented through agent-brain or `$implement-plan`,
materialize it on disk with `status: approved`; chat-only prose is not a
handoff. `delivery-readiness` owns the cross-stage `plan_to_build` assessment;
agent-brain owns the outer Task Pack, allowed paths, acceptance lifecycle, and
Done gate.

`delivery-readiness` owns the cross-stage `plan_to_build` assessment and report. `agent-brain` owns the outer Task Pack, allowed paths, acceptance lifecycle, and Task Pack linkage. Emit the shared identity fields defined in the router and hand off to agent-brain for Task Pack creation; do not duplicate those contracts here.

The canonical artifact is normally `docs/plans/<feature-slug>-execution-plan.md` (or the configured execution-plan path) and includes frontmatter with at least:

```yaml
id: <stable plan id>
type: execution_plan
status: draft | approved
created_at: <date>
updated_at: <date>
sources: []
related: []
base_commit: <git commit used for planning>
orchestration_mode: batch | parallel_dag
execution_target: pending | current_session | subagent
execution_backend: pending | zcode_subagent | codex_subagent | zcode_mcp
```

`source_plan_sha256` is the SHA-256 of the complete canonical plan file and is
recorded in downstream Task Packs; do not put the file's own hash into its
frontmatter because that would create a circular hash. `plan_id`,
`base_commit`, source artifacts, and the root or node `plan_unit_id` values must
remain stable between planning and implementation.

Before handing off, report:

```bash
git rev-parse HEAD
shasum -a 256 docs/plans/<feature-slug>-execution-plan.md
```

After any plan edit, recompute the plan hash and hand the current artifact to
`delivery-readiness` and then agent-brain. If the user asked for implementation
immediately, the current-turn approval may authorize the handoff after the
execution shape and target are explicit; otherwise stop after writing the
approved plan.

## Inputs to Look For

Use the TRD, PRD, research brief, existing codebase, issue context, test layout, deployment constraints, and user constraints when available.

Extract:

- Modules, interfaces, data changes, migrations, integrations, and tests.
- Shared contracts: API shapes, schemas, config, permissions, events, generated types.
- Sequencing constraints: deploy order, migration order, feature flags, compatibility needs.
- Risk points: unknown APIs, data quality, concurrency, external services, performance, security, operational risk.
- Validation options: tests, smoke checks, manual flows, logs, metrics, local or staging verification.
- Existing outer contracts: agent-brain Task Pack id, source artifacts/hash, allowed paths, required skills, and canonical acceptance ids.
- Plan identity: stable plan id, plan hash, and base commit used for the planned change.

## Document Artifact Mode

Follow the shared document-artifact rules in the router SKILL.md; plans use `docs/plans/` (or `document_artifacts.paths.execution_plan`) with a stable filename and `id` / `type: execution_plan` / `status` / dates / `sources` / `related` frontmatter, linking source PRD/TRD paths in `related`.

When document artifact mode is disabled or the config is absent, keep normal chat-output behavior only for research-only or discussion-only plans. For implementation-bound plans, the Implementation Handoff Ownership section above still requires a canonical plan artifact.

Also include a `Remote Handoff Inputs` section identifying the selected
execution target and, for a subagent, the selected execution backend, plus the
whole-goal contract for `batch`, or the node context, exclusions, verification
commands, and acceptance criteria that `delegate` will need for
`parallel_dag`.

## Planning Workflow

1. Restate the implementation goal.
   - Connect the plan to the TRD and define what will be considered done.

2. Assess parallelism before generating the plan.
   - Inspect likely units, dependencies, write overlap, actor capabilities, and
     expected time savings.
   - Recommend `batch` or `parallel_dag` and explain independent work,
     expected benefit, coordination cost, and constraints.
   - If the user has not chosen a shape, return the assessment only. Do not
     write an approved plan, task packet, or DAG while the choice is pending.

3. Generate the selected plan shape.
   - For `batch`, use one root unit (for example `plan_unit_id: root`), an
     ordered internal sequence, one whole-goal actor contract, and one final
     acceptance scope. Internal steps are not parent-agent interaction points.
   - For `parallel_dag`, split only independently scoped, owned, and verified
     units. Include dependencies, critical path, risk-first nodes, node-level
     acceptance, and final integration acceptance.

4. Choose sequencing and actor assignment.
   - Put contract/schema decisions before dependent work and risky validation
     early enough to protect broad implementation.
   - For `batch`, prefer one actor for the whole goal.
   - For `parallel_dag`, choose among the local lead, local subagent, managed
     agent, remote worker, or unassigned actor for each node.

5. Define ownership and parallelism.
   - Avoid concurrent writes to shared files, public contracts, database
     schemas, generated artifacts, migrations, dependency manifests, or
     lockfiles.
   - Before approving parallel nodes, normalize pathspecs and reject
     overlapping write ownership or mutexes. Record `parallel_mode` after
     direct and indirect impact analysis.

6. Create execution contracts.
   - Each delegated actor contract must define objective, scope, inputs,
     required capabilities, required skills, write ownership, forbidden
     writes, steps, verification, expected output, acceptance criteria,
     evidence required, and handoff readiness.
   - A delegated `batch` contract covers the full goal and one final return.
     A delegated `parallel_dag` contract covers only its assigned node.

7. Define verification and handoff.
   - For `batch`, state that the coordinating actor waits for the explicit
     final result before running one final acceptance.
   - For `parallel_dag`, state what evidence accepts each node and unblocks
     downstream work, followed by final integration acceptance.
   - Write the plan and handoff inputs to the canonical file before the final
     response whenever the plan is implementation-bound.
   - Compute the canonical file hash only after all edits are complete;
     downstream Task Packs copy it into `source_plan_sha256`.

## Handoff Rules

- If the user has not chosen the execution shape, stop after the parallelism
  assessment; do not guess.
- If the approved plan uses `batch`, delegate the whole plan as one goal when
  `execution_target=subagent`, or route it to `$implement-plan` when
  `execution_target=current_session`.
- If the approved plan uses `parallel_dag`, hand it to `delegate` for the
  user's execution-target choice and node packet generation. True parallel
  execution requires multiple actors; do not simulate it with a fake DAG in a
  single current session.
- If the plan artifact, hash, approval, or Task Pack linkage is missing, stop and repair the planning handoff before implementation.
- If implementation units, dependencies, or shared-write boundaries are unclear, hand off to `codebase-analysis` (impact mode).
- If the plan is for a refactor, ensure `refactor-plan` has defined behavior protection first.

## Execution Actor Decision Rules

Recommend `batch` when:

- The task has one dominant implementation path.
- Modules are tightly coupled or share central contracts.
- A single writer can finish and verify the goal without coordination.
- The expected parallelism is low or would not materially shorten delivery.
- The output is easier to review as one complete result.

Recommend `parallel_dag` when:

- At least two actors can make meaningful progress independently.
- Each actor's output can be objectively verified.
- Write ownership, mutexes, dependencies, and worktree policy are explicit.
- Parallel execution reduces wall-clock time or improves analysis quality.
- The coordination and integration cost is justified.

Avoid `parallel_dag` when:

- The user has not chosen parallel execution.
- Requirements or technical boundaries are still unclear.
- All work touches one central module, public interface, schema, migration, or
  generated artifact.
- Tasks are tightly coupled or require continuous local debugging.
- The result cannot be objectively reviewed by the coordinating actor.

When in doubt, use `batch` and let the actor perform internal serial steps.

Do not delegate work that requires host-only runtime tooling unless the selected
adapter explicitly declares and the approved plan authorizes that capability.
Browser control, desktop control, and visual acceptance gates remain with the
coordinating session by default. Code implementation and repository tests may
be delegated to the harness-mandated subagent adapter (`zcode_subagent`,
`codex_subagent`, or `zcode_mcp`) when that adapter is actually
available; record unavailable runtime tools as a blocker.

## Output Format

When the user has not yet chosen a shape, return only:

```markdown
## Parallelism Assessment

- Recommended shape: batch | parallel_dag
- Candidate independent work: <items or None>
- Expected benefit: <time or quality benefit>
- Coordination cost: <merge, worktree, mutex, and communication cost>
- Risks and constraints: <shared writes, runtime tools, or None>
- User decision needed: batch | parallel_dag
```

After the user chooses and the plan is generated, use this structure as
appropriate:

```markdown
## Implementation Goal

<What will be implemented and what done means>

## Execution Decision

- orchestration_mode: batch | parallel_dag
- execution_target: pending | current_session | subagent
- execution_backend: pending | zcode_subagent | codex_subagent | zcode_mcp
- user_approval: <pending|approved>

## Plan Artifact

- path: `<canonical execution plan path>`
- plan_id: `<stable id>`
- status: `draft|approved`
- base_commit: `<git commit>`
- source_plan_sha256: `<sha256 of the complete plan file>`

## Batch Plan

- plan_unit_id: `root`
- actor: <actor>
- acceptance_scope: batch
- internal_sequence: <ordered implementation and verification steps>
- final_acceptance: <one complete acceptance scope>

## Parallel DAG Plan

| ID | Unit | Depends On | Actor | Risk | Acceptance |
|---|---|---|---|---|---|
| U1 | <Name> | <None or IDs> | <Actor> | Low/Med/High | <IDs> |

### Node Contract: U1

- Contract linkage: plan_id / source_plan_sha256 / base_commit / task_id / source_artifacts / source_hash / acceptance_ids / orchestration_mode / execution_target / execution_backend
- Required capabilities: <reasoning, repository access, browser, domain knowledge, or other needs>
- Required skills: <skill names or "None">
- Write ownership: <allowed paths, modules, contracts, or "Read only">
- Forbidden writes: <explicit exclusions>
- Verification: <command, check, or evidence>
- Evidence required: <machine-readable path, overall status, exit codes, git_head, changed files, source hashes, or manual acknowledgement>
- Handoff readiness: <observable conditions required before downstream actors can start>

Critical path: <U1 -> U2 -> U4, or None for batch>
Risk-first nodes: <U3, U5, or None>
Shared-write nodes: <U1, U2, or None>

## Execution Sequence

1. <Batch internal step, or DAG units covered and verification checkpoint>
2. <Batch internal step, or DAG units covered and verification checkpoint>
3. <Batch internal step, or DAG units covered and verification checkpoint>

## Per-Actor Execution Contracts

### Actor: <Name or managed-platform role>

Objective: <What this actor should achieve>

Scope: <Files, modules, docs, or questions in scope>

Inputs: <TRD sections, files, constraints, raw artifacts>

Exclusions: <What not to modify or assume>

Steps:
1. <Step>
2. <Step>

Expected output: <Structured artifact or summary>

Acceptance criteria: <How the coordinating actor will judge usefulness>

Handoff readiness: <What must be true before the result can be accepted or downstream work starts>

## Verification Plan

<Batch final acceptance, or node and final integration checks for a DAG>

## Open Questions and Risks

<Decisions or risks that must be resolved during execution>
```

For a small batch plan, omit the parallel-DAG section. For a parallel plan,
do not omit node acceptance or the final integration acceptance.
