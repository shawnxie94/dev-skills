#!/usr/bin/env python3
"""Validate the repository-level contracts shared by dev-skills."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
README = ROOT / "README.md"
EXTERNAL_SKILLS = {"skill-installer"}

# Descriptions are the only part of a skill that is always loaded, so they must
# stay a trigger surface (purpose + modes + trigger phrases), not a summary of
# the body. The mode tables and rules in SKILL.md are the single source of truth.
MAX_DESCRIPTION_CHARS = 320


def frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def main() -> int:
    errors: list[str] = []
    skill_dirs = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())
    skill_names = {path.name for path in skill_dirs}

    if not skill_dirs:
        errors.append("skills/: no skill directories found")

    for skill_dir in skill_dirs:
        name = skill_dir.name
        skill_file = skill_dir / "SKILL.md"
        agent_file = skill_dir / "agents" / "openai.yaml"

        if not skill_file.is_file():
            errors.append(f"{name}: missing SKILL.md")
            continue
        metadata = frontmatter(skill_file)
        if metadata.get("name") != name:
            errors.append(
                f"{name}: frontmatter name is {metadata.get('name')!r}, expected {name!r}"
            )
        description = metadata.get("description", "")
        if not description:
            errors.append(f"{name}: frontmatter description is missing")
        elif len(description) > MAX_DESCRIPTION_CHARS:
            errors.append(
                f"{name}: frontmatter description is {len(description)} chars, "
                f"over the {MAX_DESCRIPTION_CHARS}-char cap; keep triggers, drop "
                "content already covered by SKILL.md"
            )

        if not agent_file.is_file():
            errors.append(f"{name}: missing agents/openai.yaml")
        else:
            agent_text = agent_file.read_text(encoding="utf-8")
            for field in ("display_name", "short_description", "default_prompt"):
                if not re.search(rf"^\s*{field}:\s*.+$", agent_text, re.MULTILINE):
                    errors.append(f"{name}: agents/openai.yaml missing {field}")
            if f"${name}" not in agent_text:
                errors.append(f"{name}: default_prompt does not reference ${name}")

        references = set(re.findall(r"\$([a-z][a-z0-9-]*)", skill_file.read_text(encoding="utf-8")))
        unknown = sorted(references - skill_names - EXTERNAL_SKILLS)
        for reference in unknown:
            errors.append(f"{name}: unknown skill reference ${reference}")

        # Reference files are loaded on demand, so a stale $skill or a dangling
        # relative link there is invisible until an agent follows it mid-task.
        for doc in sorted(skill_dir.rglob("*.md")):
            text = doc.read_text(encoding="utf-8")
            rel = doc.relative_to(skill_dir)
            for reference in sorted(set(re.findall(r"\$([a-z][a-z0-9-]*)", text))):
                if reference not in skill_names and reference not in EXTERNAL_SKILLS:
                    errors.append(f"{name}/{rel}: unknown skill reference ${reference}")
            for link in re.findall(r"\]\(([^)#\s]+)", text):
                if "://" in link or link.startswith("mailto:"):
                    continue
                if "<" in link or ">" in link:
                    # Documentation placeholders such as <slug>.md are not links.
                    continue
                target = (doc.parent / link).resolve()
                if not target.exists():
                    errors.append(f"{name}/{rel}: dangling link {link}")

    readme_text = README.read_text(encoding="utf-8") if README.is_file() else ""
    readme_skills = {
        name for name in re.findall(r"`([a-z][a-z0-9-]+)`", readme_text) if name in skill_names
    }
    for missing in sorted(skill_names - readme_skills):
        errors.append(f"README.md: skill {missing} is not listed")

    if errors:
        print("Skill contract check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Skill contract check passed: {len(skill_names)} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
