# Skill Run Record

`dev-skills` does not collect prompts or task content automatically. For meaningful runs, an agent or operator may append a small local JSONL event:

```bash
python3 <dev-skills>/scripts/record_skill_run.py \
  --skill codebase-orientation \
  --status completed \
  --validation pass \
  --task-type orientation \
  --next-handoff write-trd \
  --friction graphify-no-api-key
```

The default log is `~/.codex/dev-skills-runs.jsonl`. Set `DEV_SKILLS_RUN_LOG` or pass `--path` to use another local file. The record intentionally stores only outcome metadata, short friction tags, and optional short feedback; do not put the original prompt, source code, secrets, or sensitive business data in it.

Generate a retrospective summary:

```bash
python3 <dev-skills>/scripts/summarize_skill_runs.py \
  --path ~/.codex/dev-skills-runs.jsonl \
  --since-days 30
```

This is opt-in and local. It is intended to establish a small evidence loop before introducing centralized telemetry.
