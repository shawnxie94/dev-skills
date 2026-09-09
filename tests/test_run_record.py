from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "record_skill_run.py"
SPEC = importlib.util.spec_from_file_location("record_skill_run", SCRIPT)
assert SPEC and SPEC.loader
record_skill_run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(record_skill_run)


class RuntimeLogPathTests(unittest.TestCase):
    def test_forced_runtime_selects_its_own_log(self) -> None:
        for runtime, relative in (
            ("pi", ".pi/agent"),
            ("codex", ".codex"),
            ("zcode", ".zcode"),
        ):
            with self.subTest(runtime=runtime), mock.patch.dict(
                os.environ, {"DEV_SKILLS_FORCE_RUNTIME": runtime}, clear=False
            ):
                self.assertEqual(record_skill_run.detect_runtime(), runtime)
                self.assertEqual(
                    record_skill_run.default_log_path(),
                    Path.home() / relative / "dev-skills-runs.jsonl",
                )

    def test_explicit_log_env_still_wins(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"DEV_SKILLS_RUN_LOG": "/tmp/dev-skills-test.jsonl", "DEV_SKILLS_FORCE_RUNTIME": "pi"},
            clear=False,
        ):
            self.assertEqual(
                record_skill_run.default_log_path(), Path("/tmp/dev-skills-test.jsonl")
            )

    def test_pi_env_marker_beats_codex_home(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"PI_CODING_AGENT": "true", "CODEX_HOME": str(Path.home() / ".codex")},
            clear=False,
        ):
            os.environ.pop("DEV_SKILLS_FORCE_RUNTIME", None)
            os.environ.pop("DEV_SKILLS_RUN_LOG", None)
            self.assertEqual(record_skill_run.detect_runtime(), "pi")

    def test_runtime_log_paths_covers_every_known_runtime(self) -> None:
        paths = record_skill_run.runtime_log_paths()
        self.assertEqual(len(paths), len(record_skill_run.RUNTIME_HOMES))
        self.assertTrue(all(path.name == "dev-skills-runs.jsonl" for path in paths))


if __name__ == "__main__":
    unittest.main()
