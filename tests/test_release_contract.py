from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/release-delivery/scripts/release_contract.py"
SPEC = importlib.util.spec_from_file_location("release_contract", SCRIPT)
assert SPEC and SPEC.loader
release_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_contract)


class ReleaseContractPathTests(unittest.TestCase):
    def test_inspect_and_plan_serialize_project_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            profile = Path(directory) / "brain-profile"
            project.mkdir()
            profile.mkdir()
            (project / ".agent").mkdir()
            (project / ".agent/project-profile").symlink_to(profile, target_is_directory=True)
            (profile / "release.yaml").write_text(
                """schema_version: 1
project: example
runbook: production-release-runbook.md
environments: [production]
approval:
  merge_main: human
  production: human
  rollback: preauthorized
required_evidence: [rollback_ready]
""",
                encoding="utf-8",
            )
            (profile / "production-release-runbook.md").write_text(
                "# Prerequisite\n# Deploy\n# Verify\n# Rollback\n",
                encoding="utf-8",
            )

            inspected = release_contract.load_manifest(project)
            logical_profile = release_contract.logical_profile_path(project, None)
            self.assertEqual(
                release_contract.display_path(project, logical_profile / "release.yaml"),
                ".agent/project-profile/release.yaml",
            )
            self.assertEqual(
                release_contract.display_path(
                    project, logical_profile / inspected[0]["runbook"]
                ),
                ".agent/project-profile/production-release-runbook.md",
            )
            plan = release_contract.build_plan(
                project=project,
                profile_dir=None,
                action="rollback",
                environment="production",
                candidate="a" * 40,
                artifact="",
                quality_gate=None,
                approval="approved",
                merge_approval="",
                backup_evidence="",
                rollback_evidence="ready",
                migration_evidence="",
            )
            self.assertEqual(plan["manifest"], ".agent/project-profile/release.yaml")
            self.assertEqual(
                plan["runbook"], ".agent/project-profile/production-release-runbook.md"
            )
            self.assertNotIn(str(directory), plan["manifest"])
            self.assertNotIn(str(directory), plan["runbook"])


if __name__ == "__main__":
    unittest.main()
