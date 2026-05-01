from __future__ import annotations

import json
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

    def test_doctor_json_outputs_structured_report(self) -> None:
        runner = CliRunner()
        doctor = {
            "status": "passed",
            "checks": {
                "repo_root": {"ok": True, "path": str(ROOT)},
                "markers": [],
            },
        }
        with mock.patch.object(cli, "doctor_report", return_value=doctor):
            result = runner.invoke(cli.main, ["--repo-root", str(ROOT), "doctor", "--json-output"])

        self.assertEqual(result.exit_code, 0, result.output)
        report = json.loads(result.output)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["checks"]["repo_root"]["ok"])
        self.assertIn("markers", report["checks"])

    def test_doctor_fix_creates_syson_env_and_workspace_layout(self) -> None:
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
                path.write_text("template\n", encoding="utf-8")

            with (
                mock.patch.dict(os.environ, {"MBSE_MODEL_WORKSPACE": str(workspace)}),
                mock.patch.object(cli, "command_exists", return_value=True),
                mock.patch.object(cli.subprocess, "run", return_value=mock.Mock(returncode=0)),
                mock.patch.object(cli, "tcp_connects", return_value=False),
                mock.patch.object(cli, "fetch_status", return_value=None),
            ):
                result = runner.invoke(cli.main, ["--repo-root", str(repo), "doctor", "--fix"])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertTrue((repo / "deploy/syson/.env").exists())
            self.assertTrue((workspace / "README.md").exists())
            self.assertTrue((workspace / "exports/flexo").is_dir())
            self.assertFalse((workspace / ".git").exists())
            self.assertIn("Applied fixes:", result.output)
            self.assertIn("python3 scripts/flexo_mms_env.py init --with-sysmlv2", result.output)
            self.assertIn("docker compose -f deploy/syson/docker-compose.yml up -d", result.output)

    def test_doctor_fix_rejects_json_output(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.main, ["--repo-root", str(ROOT), "doctor", "--fix", "--json-output"])

        self.assertNotEqual(result.exit_code, 0, result.output)
        self.assertIn("--fix cannot be combined with --json-output", result.output)

    def test_status_json_outputs_structured_report(self) -> None:
        runner = CliRunner()
        status = {
            "status": "passed",
            "containers": [
                {
                    "name": "demo",
                    "exists": True,
                    "running": True,
                    "status": "running",
                    "health": "none",
                    "ports": {},
                }
                for _ in (*cli.FLEXO_CONTAINERS, *cli.SYSON_CONTAINERS)
            ],
            "http": {"flexo_projects": {"status": 200}},
        }
        with mock.patch.object(cli, "service_report", return_value=status):
            result = runner.invoke(cli.main, ["--repo-root", str(ROOT), "status", "--json-output"])

        self.assertEqual(result.exit_code, 0, result.output)
        report = json.loads(result.output)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(len(report["containers"]), len(cli.FLEXO_CONTAINERS) + len(cli.SYSON_CONTAINERS))
        self.assertEqual(report["http"]["flexo_projects"]["status"], 200)

    def test_report_command_writes_markdown_html_and_json(self) -> None:
        runner = CliRunner()
        doctor = {"status": "passed", "checks": {}}
        status = {"status": "passed", "containers": [], "http": {}}
        report_data = {
            "generated_at": "2026-01-01T00:00:00+00:00",
            "repo_root": str(ROOT),
            "model_workspace": None,
            "service_urls": {},
            "doctor": doctor,
            "status": status,
            "share_issues": [],
            "diagnostics": {"latest_index": "diagnostics/latest/index.md", "latest_exists": False},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "report"
            with mock.patch.object(cli, "report_data", return_value=report_data):
                result = runner.invoke(
                    cli.main,
                    ["--repo-root", str(ROOT), "report", "--output-dir", str(output_dir)],
                )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertTrue((output_dir / "index.md").exists())
            self.assertTrue((output_dir / "index.html").exists())
            self.assertTrue((output_dir / "doctor.json").exists())
            self.assertTrue((output_dir / "status.json").exists())
            self.assertEqual(json.loads((output_dir / "doctor.json").read_text(encoding="utf-8")), doctor)
            self.assertIn("# MBSE Lab Report", (output_dir / "index.md").read_text(encoding="utf-8"))

    def test_cleanup_dry_run_keeps_generated_files(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            generated = repo / "reports" / "latest" / "index.md"
            generated.parent.mkdir(parents=True)
            generated.write_text("# Report\n", encoding="utf-8")

            result = runner.invoke(cli.main, ["--repo-root", str(repo), "cleanup", "--dry-run"])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("dry-run: remove reports", result.output)
            self.assertTrue(generated.exists())

    def test_cleanup_removes_safe_generated_paths_only(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            for relative in (
                "reports/latest/index.md",
                "diagnostics/latest/index.md",
                "runs/flexo-to-syson/run.json",
                "tmp/scratch.txt",
                "site/index.html",
                "exports/flexo/private.json",
            ):
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("generated\n", encoding="utf-8")

            result = runner.invoke(cli.main, ["--repo-root", str(repo), "cleanup"])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertFalse((repo / "reports").exists())
            self.assertFalse((repo / "diagnostics").exists())
            self.assertFalse((repo / "runs").exists())
            self.assertFalse((repo / "tmp").exists())
            self.assertTrue((repo / "site").exists())
            self.assertTrue((repo / "exports" / "flexo" / "private.json").exists())

            site_result = runner.invoke(cli.main, ["--repo-root", str(repo), "cleanup", "--include-site"])

            self.assertEqual(site_result.exit_code, 0, site_result.output)
            self.assertFalse((repo / "site").exists())

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

    def test_flexo_export_wrapper_builds_bridge_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            [
                "--repo-root",
                str(ROOT),
                "flexo",
                "export",
                "project-1",
                "--commit-id",
                "commit-1",
                "--output",
                "out.json",
                "--dry-run",
            ],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("dry-run: python3 scripts/flexo_syson_bridge.py flexo-export project-1", result.output)
        self.assertIn("--commit-id commit-1", result.output)
        self.assertIn("--output out.json", result.output)

    def test_syson_roots_wrapper_builds_bridge_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            ["--repo-root", str(ROOT), "syson", "roots", "syson-project-1", "--json-output", "--dry-run"],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("dry-run: python3 scripts/flexo_syson_bridge.py syson-roots syson-project-1", result.output)
        self.assertIn("--json", result.output)

    def test_bridge_run_wrapper_builds_bridge_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            [
                "--repo-root",
                str(ROOT),
                "bridge",
                "run",
                "flexo-project-1",
                "--syson-project-id",
                "syson-project-1",
                "--namespace-id",
                "namespace-1",
                "--output-dir",
                "exports",
                "--dry-run",
            ],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("dry-run: python3 scripts/flexo_syson_bridge.py flexo-to-syson flexo-project-1", result.output)
        self.assertIn("--syson-project-id syson-project-1", result.output)
        self.assertIn("--namespace-id namespace-1", result.output)
        self.assertIn("--output-dir exports", result.output)

    def test_share_check_passes_for_clean_git_repo(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            repo.mkdir()
            cli.run_capture(["git", "init", "-b", "main"], repo)
            cli.run_capture(["git", "config", "user.email", "test@example.invalid"], repo)
            cli.run_capture(["git", "config", "user.name", "Test User"], repo)
            (repo / "README.md").write_text("# Clean\n", encoding="utf-8")
            cli.run_capture(["git", "add", "README.md"], repo)
            cli.run_capture(["git", "commit", "-m", "init"], repo)

            result = runner.invoke(cli.main, ["--repo-root", str(repo), "share-check"])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("share-check passed", result.output)

    def test_share_check_flags_tracked_runtime_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            repo.mkdir()
            cli.run_capture(["git", "init", "-b", "main"], repo)
            cli.run_capture(["git", "config", "user.email", "test@example.invalid"], repo)
            cli.run_capture(["git", "config", "user.name", "Test User"], repo)
            env = repo / "deploy" / "syson" / ".env"
            env.parent.mkdir(parents=True)
            env.write_text("SYSON_POSTGRES_PASSWORD=pass" "word\n", encoding="utf-8")
            cli.run_capture(["git", "add", "-f", "deploy/syson/.env"], repo)

            issues = cli.scan_share_issues(repo)

            self.assertTrue(any("tracked publish-blocked path: deploy/syson/.env" in issue for issue in issues))
            self.assertTrue(any("tracked secret-like pattern" in issue for issue in issues))

    def test_share_check_flags_untracked_generated_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            repo.mkdir()
            cli.run_capture(["git", "init", "-b", "main"], repo)
            cli.run_capture(["git", "config", "user.email", "test@example.invalid"], repo)
            cli.run_capture(["git", "config", "user.name", "Test User"], repo)
            export = repo / "exports" / "flexo" / "private.json"
            export.parent.mkdir(parents=True)
            export.write_text("{}", encoding="utf-8")

            issues = cli.scan_share_issues(repo)

            self.assertIn("untracked generated export: exports/flexo/private.json", issues)


if __name__ == "__main__":
    unittest.main()
