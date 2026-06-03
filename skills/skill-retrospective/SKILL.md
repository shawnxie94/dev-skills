---
name: skill-retrospective
description: Improve existing skills based on real task feedback. Use when the user asks to review how a skill performed, update a skill from usage feedback, refine skill triggers, adjust handoff rules, fix an over-heavy or under-specified workflow, incorporate lessons from a real task, or evolve this repository's skills after using them. Focus on identifying concrete skill gaps, making minimal targeted edits, preserving lightweight scope, validating changed skills, and preparing the change for commit.
---

# Skill Retrospective

Use this skill after a real task exposes a problem or improvement opportunity in one or more skills. The goal is to evolve skills from evidence, not to redesign them speculatively.

## Core Principles

- Use real task feedback as the source of truth.
- Make the smallest useful skill change.
- Separate skill problems from ordinary task difficulty.
- Prefer trigger, workflow, handoff, output, or validation fixes over broad rewrites.
- Keep skills lightweight and focused on one reusable workflow.
- Validate every changed skill with `quick_validate.py`.

## What To Inspect

Use the user's feedback, recent conversation, changed files, skill bodies, README, validation output, and task artifacts when available.

Classify the feedback:

- Trigger issue: the right skill did not activate, or the wrong skill activated.
- Workflow issue: the steps were missing, too heavy, too vague, or in the wrong order.
- Handoff issue: the skill should have routed to another skill but did not.
- Output issue: the format was not useful for the next step.
- Validation issue: the skill did not require the right checks.
- Scope issue: the skill mixed unrelated responsibilities or missed an important boundary.
- Naming issue: the skill name was confusing or overlapped another skill.

## Retrospective Workflow

1. Identify the real feedback.
   - State what happened in the task.
   - Identify which skill was used or should have been used.
   - Separate confirmed skill gaps from preferences or one-off task noise.

2. Locate the affected skill content.
   - Inspect frontmatter `description` for trigger issues.
   - Inspect workflow, handoff, output, and validation sections for execution issues.
   - Inspect README only when the skill list or repo-level explanation is stale.

3. Propose the minimal change.
   - Make the smallest targeted edit that would have improved the real task.
   - Avoid adding broad theory, duplicated content, or extra documentation files.
   - Do not expand a skill into another skill's responsibility.

4. Apply the edit.
   - Update `SKILL.md` and `agents/openai.yaml` only when needed.
   - Update README when adding, renaming, or materially changing a skill.
   - Preserve existing naming and style conventions.

5. Validate.
   - Run `quick_validate.py` on every changed skill.
   - Search for stale skill names or old handoff references after renames.
   - Report validation results and remaining risk.

6. Prepare follow-up.
   - If the user asked to commit, hand off to `prepare-commit`.
   - Otherwise summarize changed files and recommend commit scope.

## Output Format

Answer in the user's language unless they request otherwise. Use this structure when practical:

```markdown
## Feedback

<Real task feedback that motivated the change>

## Affected Skills

- <Skill and why it is affected>

## Change Type

<Trigger / workflow / handoff / output / validation / scope / naming>

## Changes Made

- <Concrete edit>

## Validation

- `<quick_validate.py ...>`: <result>

## Remaining Risk

<Any uncertainty or "None">

## Next Step

<prepare-commit, further test, or use the updated skill on another real task>
```

For small edits, compress the output but keep feedback, affected skills, changes, and validation.
