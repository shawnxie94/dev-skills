# Skill Run Record

`dev-skills` does not collect prompts or task content automatically. For meaningful runs, an agent or operator may append a small local JSONL event:

```bash
python3 <dev-skills>/scripts/record_skill_run.py \
  --skill codebase-analysis \
  --status completed \
  --validation pass \
  --task-type orientation \
  --next-handoff write-trd \
  --friction codegraph-no-index
```

The default log is per runtime: `~/.pi/agent/dev-skills-runs.jsonl` for pi, `~/.codex/dev-skills-runs.jsonl` for Codex, `~/.zcode/dev-skills-runs.jsonl` for ZCode. Set `DEV_SKILLS_RUN_LOG` or pass `--path` to use another local file; `--dry-run` prints the record without writing. The record intentionally stores only outcome metadata, short friction tags, and optional short feedback; do not put the original prompt, source code, secrets, or sensitive business data in it.

Generate a retrospective summary:

```bash
python3 <dev-skills>/scripts/summarize_skill_runs.py \
  --all-runtimes \
  --since-days 30
```

This is opt-in and local. It is intended to establish a small evidence loop before introducing centralized telemetry.
