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

    def test_bootstrap_dry_run_prints_planned_setup_without_touching_workspace(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            workspace = Path(temp_dir) / "workspace"
            for path in (
                repo / "deploy/flexo-mms/docker-compose.yml",
                repo / "deploy/syson/docker-compose.yml",
                repo / "deploy/syson/.env.example",
                repo / "scripts/flexo_mms_env.py",
                repo / "scripts/flexo_syson_bridge.py",
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")

            result = runner.invoke(
                cli.main,
                [
                    "--repo-root",
                    str(repo),
                    "bootstrap",
                    "--dry-run",
                    "--model-workspace",
                    str(workspace),
                    "--skip-start",
                    "--skip-flexo-org",
                    "--skip-status",
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("dry-run: python3 scripts/flexo_mms_env.py init --with-sysmlv2", result.output)
            self.assertIn("dry-run: copy deploy/syson/.env.example to deploy/syson/.env", result.output)
            self.assertIn(f"dry-run: initialize model workspace {workspace}", result.output)
            self.assertFalse(workspace.exists())

    def test_first_model_dry_run_prints_planned_workflow(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            for path in (
                repo / "deploy/flexo-mms/docker-compose.yml",
                repo / "deploy/syson/docker-compose.yml",
                repo / "scripts/flexo_mms_env.py",
                repo / "scripts/flexo_syson_bridge.py",
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")

            result = runner.invoke(
                cli.main,
                [
                    "--repo-root",
                    str(repo),
                    "first-model",
                    "Demo Model",
                    "--dry-run",
                    "--output-dir",
                    str(Path(temp_dir) / "exports"),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("dry-run: create Flexo project `Demo Model`", result.output)
            self.assertIn("dry-run: commit Package `Demo Model`", result.output)
            self.assertIn("dry-run: create SysON project `Demo Model Review`", result.output)
            self.assertIn("dry-run: import package `Demo_Model`", result.output)


if __name__ == "__main__":
    unittest.main()
