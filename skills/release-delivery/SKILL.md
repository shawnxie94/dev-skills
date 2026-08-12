---
name: release-delivery
description: Safely plan, execute, verify, observe, and roll back project releases through a deterministic project-profile release manifest and runbook. Use when the user asks to release, deploy, publish to staging or production, merge and release an accepted candidate, verify a deployment, or roll back, including Chinese requests such as 发布, 部署, 上线, 发版, 生产发布, 灰度, 回滚. Requires candidate identity, Quality Gate evidence, configured approvals, smoke checks, and rollback readiness; never guesses a runbook or embeds project credentials.
---

# Release Delivery

Use the generic release contract here; keep project hosts, paths, ports,
credential references, commands, and rollback details in the mounted project
profile.

## Resolve the release contract

From the target repository root, run:

```bash
python3 <skill-dir>/scripts/release_contract.py inspect --project .
```

Resolution is deterministic:

1. `<project>/.agent/project-profile/release.yaml`
2. An explicit `--profile-dir` supplied by the user or orchestration contract

Stop when the manifest or named runbook is missing, the environment is not
declared, or multiple sources conflict. Do not search arbitrary Markdown files
and choose one heuristically.

## Build the release plan

For deployment:

```bash
python3 <skill-dir>/scripts/release_contract.py plan \
  --project . \
  --action deploy \
  --environment <staging|production> \
  --candidate <commit-sha> \
  --artifact <tag-or-digest> \
  --quality-gate <quality-gate-result.yaml> \
  --merge-approval <main-merge-approval-evidence> \
  [--approval <environment-approval-evidence>] \
  [--backup-evidence <backup-readiness-evidence>] \
  [--rollback-evidence <rollback-readiness-evidence>] \
  [--migration-evidence <migration-readiness-evidence>]
```

For rollback:

```bash
python3 <skill-dir>/scripts/release_contract.py plan \
  --project . \
  --action rollback \
  --environment production \
  --candidate <commit-sha> \
  [--approval <approval-evidence>]
```

The planner is read-only. It validates the manifest, exact runbook path,
environment, candidate/QG identity, configured merge and environment approvals,
manifest-required readiness evidence, and whether the runbook exposes
preflight, deployment, verification, and rollback sections.

## Determine the release version

- If the target version is explicitly specified in the current request or the
  orchestration contract, use it and record it as confirmed; do not re-ask.
- Otherwise derive the next version from the release manifest's formal baseline
  and the declared versioning convention (for example
  `v<baseline>.<minor>-rc<n>`), not from the currently running tag. The running
  tag is evidence of what is live, not the version line.
- When the version was derived rather than explicitly specified, present the
  formal baseline, the running tag, and the derived version, and require the
  user to confirm it before any mutation (tagging, pushing, or deploying). A
  read-only plan may be produced before that confirmation.
- Never guess an increment (for example `-rc28` from `-rc27`) when the manifest
  declares a different baseline.

## Execute

1. Read the complete named runbook before any mutation.
2. Confirm branch, candidate commit, artifact/tag, Quality Gate evidence,
   migration/backup state, and rollback readiness.
3. Treat explicit user authorization in the current request or a recorded
   lifecycle approval as approval evidence. Do not infer approval from an old
   conversation or from `RELEASE_READY` alone.
4. Execute only the selected environment and action. Do not combine merge,
   tagging, staging, and production unless each is in scope.
5. Follow the runbook in order. After every material command, inspect its result
   before continuing.
6. Run the named smoke checks and observation window. A successful deploy
   command is not a successful release.
7. When a runbook rollback trigger matches, stop promotion and execute the
   pre-authorized rollback path. Never delete persistent data or volumes unless
   the runbook and current human approval explicitly require it.
8. Record hypothesis vs verified and preserve exact candidate/artifact identity.

## Release Result

Write a YAML result with:

```yaml
schema_version: 1
status: pass                # pass | failed | rolled_back | blocked
environment: production
candidate_commit_sha: ""
artifact_digest_or_tag: ""
quality_gate_evidence: ""
approval_evidence: ""
runbook: ""
deploy_steps: []
smoke_results: []
observation_result: ""
rollback_status: not_needed # not_needed | ready | executed | failed
residual_risks: []
next_action: ""
```

Validate it before reporting completion:

```bash
python3 <skill-dir>/scripts/release_contract.py validate-result <release-result.yaml>
```

For Multica, publish a short `## release result` comment pointing to the full
artifact. Do not paste credentials, production coordinates, or long logs into
the Issue.

## Record the Run

After the release outcome is confirmed, append a short feedback-loop event:

```bash
python3 <dev-skills>/scripts/record_skill_run.py \
  --skill release-delivery \
  --status completed \
  --validation pass \
  --task-type release \
  --friction <short-tag> \
  --feedback <short non-sensitive note>
```

Use the actual outcome status (`completed`, `blocked`, `failed`, `rolled_back`);
failed and blocked outcomes are the most useful signals for later retrospectives.

## Hard stops

- Quality Gate is not PASS or tested commit differs from candidate.
- Production or main-merge approval is required but absent.
- Candidate artifact/tag cannot be identified.
- The target version is not explicitly specified in the current request or
  contract and has not been confirmed by the user, or it cannot be derived from
  the manifest baseline and versioning convention.
- Migration or backup requirements are unresolved.
- Rollback instructions are missing or incompatible with the migration.
- Smoke checks fail or the observation window reports degradation.
- The requested action or environment is not declared in `release.yaml`.

Report `blocked`, `failed`, or `rolled_back` accurately; never convert them to
Done for workflow convenience.
