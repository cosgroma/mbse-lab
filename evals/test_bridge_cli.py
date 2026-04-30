from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mbse_lab import cli  # noqa: E402


class CliTests(unittest.TestCase):
    def test_find_repo_root_from_project(self) -> None:
        self.assertEqual(cli.find_repo_root(ROOT), ROOT)

    def test_workspace_init_creates_private_workspace_layout(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "model-workspace"
            result = runner.invoke(cli.main, ["workspace", "init", str(workspace), "--no-git"])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertTrue((workspace / "README.md").exists())
            self.assertTrue((workspace / ".gitignore").exists())
            self.assertTrue((workspace / "exports" / "flexo").is_dir())
            self.assertTrue((workspace / "exports" / "sysml").is_dir())
            self.assertTrue((workspace / "evidence").is_dir())

    def test_workspace_check_uses_environment_default(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "model-workspace"
            for directory in cli.WORKSPACE_DIRS:
                (workspace / directory).mkdir(parents=True, exist_ok=True)
            with mock.patch.dict(os.environ, {"MBSE_MODEL_WORKSPACE": str(workspace)}):
                result = runner.invoke(cli.main, ["workspace", "check"])

            self.assertEqual(result.exit_code, 0, result.output)

    def test_workspace_env_prints_export_command(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(cli.main, ["workspace", "env", temp_dir])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("export MBSE_MODEL_WORKSPACE=", result.output)

    def test_fetch_status_treats_timeout_as_unreachable(self) -> None:
        with mock.patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
            self.assertIsNone(cli.fetch_status("http://localhost:1/"))


if __name__ == "__main__":
    unittest.main()
