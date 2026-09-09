"""Contract tests for scripts/detect_runtime.sh.

The detector feeds `execution_backend` in Task Packs, so its mapping is part of
the cross-repo contract rather than a convenience helper.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "detect_runtime.sh"


def run_detector(*args: str, env_overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    # Keep the probe hermetic: no forced runtime, no real home directories.
    for key in ("DEV_SKILLS_FORCE_RUNTIME", "PI_CODING_AGENT", "AI_AGENT"):
        env.pop(key, None)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [str(SCRIPT), *args], cwd=ROOT, text=True, capture_output=True, env=env
    )


class DetectRuntimeTests(unittest.TestCase):
    def test_forced_runtime_maps_to_its_backend(self) -> None:
        for runtime, backend in (
            ("pi", "pi_subagent"),
            ("codex", "codex_subagent"),
            ("zcode", "zcode_subagent"),
        ):
            with self.subTest(runtime=runtime):
                result = run_detector(env_overrides={"DEV_SKILLS_FORCE_RUNTIME": runtime})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), runtime)
                self.assertEqual(
                    run_detector(
                        "--backend", env_overrides={"DEV_SKILLS_FORCE_RUNTIME": runtime}
                    ).stdout.strip(),
                    backend,
                )

    def test_pi_env_marker_is_detected(self) -> None:
        result = run_detector(env_overrides={"AI_AGENT": "pi"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "pi")

    def test_json_output_shape(self) -> None:
        result = run_detector(
            "--json", env_overrides={"DEV_SKILLS_FORCE_RUNTIME": "pi"}
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["runtime"], "pi")
        self.assertEqual(payload["execution_backend"], "pi_subagent")
        self.assertEqual(payload["exit_code"], 0)

    def test_ambiguous_homes_are_reported_as_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "codex").mkdir()
            (root / "zcode").mkdir()
            result = run_detector(
                env_overrides={
                    "DEV_SKILLS_PI_HOME": str(root / "pi"),
                    "DEV_SKILLS_CODEX_HOME": str(root / "codex"),
                    "DEV_SKILLS_ZCODE_HOME": str(root / "zcode"),
                }
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout.strip(), "unknown")
            self.assertEqual(
                run_detector(
                    "--backend",
                    env_overrides={
                        "DEV_SKILLS_PI_HOME": str(root / "pi"),
                        "DEV_SKILLS_CODEX_HOME": str(root / "codex"),
                        "DEV_SKILLS_ZCODE_HOME": str(root / "zcode"),
                    },
                ).stdout.strip(),
                "current_session",
            )

    def test_pi_extension_hint_wins_over_generic_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extension = root / "pi" / "agent" / "extensions" / "subagent"
            extension.mkdir(parents=True)
            (extension / "index.ts").write_text("// stub\n", encoding="utf-8")
            (root / "codex").mkdir()
            result = run_detector(
                env_overrides={
                    "DEV_SKILLS_PI_HOME": str(root / "pi"),
                    "DEV_SKILLS_CODEX_HOME": str(root / "codex"),
                    "DEV_SKILLS_ZCODE_HOME": str(root / "zcode-missing"),
                }
            )
            self.assertEqual(result.stdout.strip(), "pi")

    def test_invalid_forced_runtime_is_a_usage_error(self) -> None:
        result = run_detector(env_overrides={"DEV_SKILLS_FORCE_RUNTIME": "not-a-runtime"})
        self.assertEqual(result.returncode, 2)
        self.assertIn("must be pi|codex|zcode", result.stderr)


if __name__ == "__main__":
    unittest.main()
