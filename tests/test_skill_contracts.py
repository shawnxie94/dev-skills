"""Tests for the skill-contract gate itself.

The gate is the only automated protection against cross-file drift, so each
check is exercised against a temporary fixture that must fail. Without these,
a broken check would keep reporting "passed".
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_skill_contracts", ROOT / "scripts" / "check_skill_contracts.py"
)
assert SPEC and SPEC.loader
check_skill_contracts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_skill_contracts)


def build_root(
    tmp: str,
    *,
    description: str = "Trigger surface（触发词）",
    reference_text: str = "",
    readme: str = "| `foo` |",
) -> Path:
    root = Path(tmp) / "repo"
    skill = root / "skills" / "foo"
    (skill / "agents").mkdir(parents=True)
    (skill / "references").mkdir()
    (skill / "SKILL.md").write_text(
        f"---\nname: foo\ndescription: {description}\n---\n\n# Foo\n", encoding="utf-8"
    )
    (skill / "agents" / "openai.yaml").write_text(
        'interface:\n  display_name: "Foo"\n  short_description: "x"\n  default_prompt: "Use $foo"\n',
        encoding="utf-8",
    )
    if reference_text:
        (skill / "references" / "bar.md").write_text(reference_text, encoding="utf-8")
    (root / "README.md").write_text(readme, encoding="utf-8")
    return root


class SkillContractGateTests(unittest.TestCase):
    def test_real_repository_passes(self) -> None:
        self.assertEqual(check_skill_contracts.check(ROOT), [])

    def test_minimal_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(check_skill_contracts.check(build_root(tmp)), [])

    def test_unknown_reference_in_reference_file_is_caught(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(tmp, reference_text="Compose `$retired-skill` first.\n")
            errors = check_skill_contracts.check(root)
            self.assertTrue(
                any("unknown skill reference $retired-skill" in error for error in errors), errors
            )

    def test_dangling_link_is_caught(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(tmp, reference_text="See [plan](missing.md).\n")
            errors = check_skill_contracts.check(root)
            self.assertTrue(any("dangling link missing.md" in error for error in errors), errors)

    def test_placeholder_link_is_not_treated_as_dangling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(tmp, reference_text="Write `docs/reviews/<slug>.md`.\n")
            self.assertEqual(check_skill_contracts.check(root), [])

    def test_overlong_description_is_caught(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(tmp, description="x" * (check_skill_contracts.MAX_DESCRIPTION_CHARS + 1))
            errors = check_skill_contracts.check(root)
            self.assertTrue(any("over the" in error for error in errors), errors)

    def test_missing_readme_entry_is_caught(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(tmp, readme="no skill table here")
            errors = check_skill_contracts.check(root)
            self.assertTrue(any("is not listed" in error for error in errors), errors)

    def test_missing_agent_yaml_is_caught(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(tmp)
            (root / "skills" / "foo" / "agents" / "openai.yaml").unlink()
            errors = check_skill_contracts.check(root)
            self.assertTrue(any("missing agents/openai.yaml" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
