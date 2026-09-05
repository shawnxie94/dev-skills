from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts" / "codegraph-zcode-prompt-hook.py"

_SPEC = importlib.util.spec_from_file_location(
    "codegraph_zcode_config", ROOT / "scripts" / "codegraph_zcode_config.py"
)
assert _SPEC and _SPEC.loader
codegraph_zcode_config = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(codegraph_zcode_config)


def run_adapter(codegraph_bin: str, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(ADAPTER), "--codegraph-bin", codegraph_bin],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
    )


class CodegraphZcodeAdapterTests(unittest.TestCase):
    def fake_codegraph(self, directory: Path, stdout: str, exit_code: int = 0) -> str:
        path = directory / "codegraph"
        script = (
            "#!/bin/sh\n"
            "cat >/dev/null\n"
            f"printf '%s\\n' {json.dumps(stdout)}\n"
            f"exit {exit_code}\n"
        )
        path.write_text(script, encoding="utf-8")
        path.chmod(0o755)
        return str(path)

    def payload(self) -> dict[str, object]:
        return {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "how does the index work?",
            "cwd": "/some/project",
        }

    def test_repacks_context_into_zcode_json_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            codegraph = self.fake_codegraph(Path(temporary), "<codegraph_context>expl</codegraph_context>")
            result = run_adapter(codegraph, self.payload())
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(
            value,
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": "<codegraph_context>expl</codegraph_context>",
                }
            },
        )

    def test_silent_for_unindexed_project_and_missing_binary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            silent = self.fake_codegraph(Path(temporary), "")
            result = run_adapter(silent, self.payload())
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
        result = run_adapter(str(Path(temporary) / "missing-codegraph"), self.payload())
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_forwards_prompt_and_cwd_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            received = Path(temporary) / "received.json"
            bin_path = Path(temporary) / "codegraph"
            bin_path.write_text(
                f"#!/bin/sh\ncat > {received}\nprintf 'ctx'\n",
                encoding="utf-8",
            )
            bin_path.chmod(0o755)
            result = run_adapter(str(bin_path), self.payload())
            self.assertEqual(result.returncode, 0)
            forwarded = json.loads(received.read_text(encoding="utf-8"))
            self.assertEqual(forwarded["prompt"], "how does the index work?")
            self.assertEqual(forwarded["cwd"], "/some/project")


class CodegraphZcodeConfigTests(unittest.TestCase):
    def write_config(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "model": "test-model",
                    "provider": {"name": "keep-me"},
                    "hooks": {
                        "enabled": False,
                        "events": {
                            "PreToolUse": [
                                {"matcher": "^Bash$", "hooks": [{"type": "command", "command": "keep-bash"}]}
                            ]
                        },
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def managed_commands(self, config: dict) -> list[str]:
        groups = config.get("hooks", {}).get("events", {}).get("UserPromptSubmit", [])
        return [
            handler["command"]
            for group in groups
            for handler in group["hooks"]
            if "codegraph-zcode-prompt-hook.py" in handler["command"]
        ]

    def test_install_preserves_config_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_file = root / "cli" / "config.json"
            self.write_config(config_file)
            hook_script = root / "hooks" / "codegraph-zcode-prompt-hook.py"
            codegraph_bin = root / "bin" / "codegraph"

            first = codegraph_zcode_config.install_config(config_file, hook_script, codegraph_bin)
            second = codegraph_zcode_config.install_config(config_file, hook_script, codegraph_bin)
            self.assertIn("added", first)
            self.assertIn("updated", second)

            value = json.loads(config_file.read_text(encoding="utf-8"))
            self.assertEqual(value["model"], "test-model")
            self.assertEqual(value["provider"]["name"], "keep-me")
            self.assertTrue(value["hooks"]["enabled"])
            self.assertEqual(
                value["hooks"]["events"]["PreToolUse"][0]["hooks"][0]["command"], "keep-bash"
            )
            managed = self.managed_commands(value)
            self.assertEqual(len(managed), 1)
            self.assertIn("--codegraph-bin", managed[0])

    def test_uninstall_removes_only_managed_handler(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_file = root / "cli" / "config.json"
            self.write_config(config_file)
            hook_script = root / "hooks" / "codegraph-zcode-prompt-hook.py"
            codegraph_bin = root / "bin" / "codegraph"

            codegraph_zcode_config.install_config(config_file, hook_script, codegraph_bin)
            removed = codegraph_zcode_config.uninstall_config(config_file, hook_script)
            self.assertIn("removed", removed)

            value = json.loads(config_file.read_text(encoding="utf-8"))
            self.assertEqual(value["model"], "test-model")
            self.assertEqual(self.managed_commands(value), [])
            self.assertIn("PreToolUse", value["hooks"]["events"])

            again = codegraph_zcode_config.uninstall_config(config_file, hook_script)
            self.assertIn("no codegraph hook", again)


if __name__ == "__main__":
    unittest.main()
