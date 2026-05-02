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

from mbse_lab import cli, health  # noqa: E402


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

    def test_completion_prints_bash_activation_snippet(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.main, ["completion", "bash"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output.strip(), 'eval "$(_MBSE_LAB_COMPLETE=bash_source mbse-lab)"')

    def test_completion_prints_zsh_activation_snippet(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.main, ["completion", "zsh"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output.strip(), "source <(_MBSE_LAB_COMPLETE=zsh_source mbse-lab)")

    def test_completion_prints_fish_activation_snippet(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.main, ["completion", "fish"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output.strip(), "_MBSE_LAB_COMPLETE=fish_source mbse-lab | source")

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

    def test_syson_database_credential_report_passes_when_configured_password_works(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "deploy/syson/data/postgres").mkdir(parents=True)
            (repo / "deploy/syson/data/postgres/PG_VERSION").write_text("15\n", encoding="utf-8")
            (repo / "deploy/syson/.env").write_text(
                "SYSON_POSTGRES_IMAGE=postgres:15\n"
                "SYSON_POSTGRES_DB=postgres\n"
                "SYSON_POSTGRES_USER=username\n"
                "SYSON_POSTGRES_PASSWORD=local-password\n",
                encoding="utf-8",
            )
            with (
                mock.patch.object(health, "docker_container_report", return_value={"running": True}),
                mock.patch.object(health, "run_capture_result", return_value=mock.Mock(returncode=0, stderr="")),
            ):
                report = health.syson_database_credential_report(repo)

        self.assertTrue(report["ok"])
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["data_exists"])

    def test_syson_database_credential_report_warns_on_password_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "deploy/syson/data/postgres").mkdir(parents=True)
            (repo / "deploy/syson/data/postgres/PG_VERSION").write_text("15\n", encoding="utf-8")
            (repo / "deploy/syson/.env").write_text(
                "SYSON_POSTGRES_PASSWORD=wrong-password\n",
                encoding="utf-8",
            )
            result = mock.Mock(returncode=2, stderr='FATAL: password authentication failed for user "username"')
            with (
                mock.patch.object(health, "docker_container_report", return_value={"running": True}),
                mock.patch.object(health, "run_capture_result", return_value=result),
            ):
                report = health.syson_database_credential_report(repo)

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "failed")
        self.assertIn("does not match", report["detail"])

    def test_syson_database_credential_report_treats_unreadable_data_dir_as_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            data_path = repo / "deploy/syson/data/postgres"
            data_path.mkdir(parents=True)
            (repo / "deploy/syson/.env").write_text(
                "SYSON_POSTGRES_PASSWORD=local-password\n",
                encoding="utf-8",
            )
            with (
                mock.patch.object(health, "has_persisted_data", return_value=True),
                mock.patch.object(health, "docker_container_report", return_value={"running": False}),
            ):
                report = health.syson_database_credential_report(repo)

        self.assertTrue(report["data_exists"])
        self.assertEqual(report["status"], "database-stopped")

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
            self.assertIn("mbse-lab init", result.output)
            self.assertIn("mbse-lab services up --syson --timeout 60", result.output)

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
            self.assertIn('mbse-lab first-model "My First Model"', result.output)
            self.assertFalse(workspace.exists())

    def test_init_dry_run_prepares_files_without_starting_services(self) -> None:
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
                    "init",
                    "--dry-run",
                    "--model-workspace",
                    str(workspace),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("dry-run: python3 scripts/flexo_mms_env.py init --with-sysmlv2", result.output)
            self.assertIn("dry-run: copy deploy/syson/.env.example to deploy/syson/.env", result.output)
            self.assertIn(f"dry-run: initialize model workspace {workspace}", result.output)
            self.assertIn("mbse-lab services up", result.output)
            self.assertNotIn("scripts/flexo_mms_env.py up", result.output)
            self.assertNotIn("init-flexo-org", result.output)
            self.assertFalse(workspace.exists())

    def test_flexo_env_init_renders_compose_with_docker_env_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_dir = Path(temp_dir) / "flexo"
            cluster = env_dir / "mount" / "cluster.trig"
            cluster.parent.mkdir(parents=True)
            cluster.write_text("# local fixture\n", encoding="utf-8")

            cli.run_capture(
                [
                    "python3",
                    "scripts/flexo_mms_env.py",
                    "--env-dir",
                    str(env_dir),
                    "init",
                    "--with-sysmlv2",
                ],
                ROOT,
            )

            compose = (env_dir / "docker-compose.yml").read_text(encoding="utf-8")
            self.assertIn("${FLEXO_MMS_LDAP_ADMIN_PASSWORD}", compose)
            self.assertIn("${FLEXO_MMS_SYSMLV2_HOST_PORT:-18083}:8080", compose)
            self.assertTrue((env_dir / "env" / "flexo-mms-jwt.env").exists())

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

    def test_first_model_dry_run_warns_when_workspace_unset(self) -> None:
        runner = CliRunner()
        with mock.patch.dict(os.environ, {"MBSE_MODEL_WORKSPACE": ""}):
            result = runner.invoke(cli.main, ["--repo-root", str(ROOT), "first-model", "Demo Model", "--dry-run"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("warning: MBSE_MODEL_WORKSPACE is unset", result.output)
        self.assertIn("repo-local `exports`", result.output)

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

    def test_services_up_dry_run_builds_start_commands(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.main, ["--repo-root", str(ROOT), "services", "up", "--timeout", "45", "--dry-run"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("dry-run: python3 scripts/flexo_mms_env.py up --wait --timeout 45", result.output)
        self.assertIn("dry-run: docker compose -f deploy/syson/docker-compose.yml up -d", result.output)

    def test_wait_for_readiness_succeeds_after_retry(self) -> None:
        probe = cli.ReadinessProbe("Demo API", "http://example.invalid/ready", "mbse-lab services up")
        with (
            mock.patch.object(cli, "fetch_status", side_effect=[None, 200]),
            mock.patch.object(cli.time, "sleep") as sleep,
        ):
            cli.wait_for_readiness([probe], timeout=5, interval=0)

        sleep.assert_called_once_with(0)

    def test_wait_for_readiness_failure_explains_next_command(self) -> None:
        probe = cli.ReadinessProbe("Demo API", "http://example.invalid/ready", "mbse-lab services up")
        with (
            mock.patch.object(cli, "fetch_status", return_value=None),
            self.assertRaises(cli.click.ClickException) as raised,
        ):
            cli.wait_for_readiness([probe], timeout=0, interval=0)

        self.assertIn("Service readiness failed after 0s", str(raised.exception))
        self.assertIn("Demo API", str(raised.exception))
        self.assertIn("no HTTP response", str(raised.exception))
        self.assertIn("mbse-lab services up", str(raised.exception))

    def test_services_up_waits_for_selected_service_apis(self) -> None:
        runner = CliRunner()
        with (
            mock.patch.object(cli, "run_command") as run_command,
            mock.patch.object(cli, "wait_for_readiness") as wait_for_readiness,
        ):
            result = runner.invoke(cli.main, ["--repo-root", str(ROOT), "services", "up", "--no-flexo"])

        self.assertEqual(result.exit_code, 0, result.output)
        run_command.assert_called_once_with(
            ["docker", "compose", "-f", "deploy/syson/docker-compose.yml", "up", "-d"],
            ROOT,
            False,
        )
        wait_for_readiness.assert_called_once()
        probes = wait_for_readiness.call_args.args[0]
        self.assertEqual([probe.label for probe in probes], ["SysON Web UI"])

    def test_bootstrap_waits_for_service_readiness_after_start(self) -> None:
        runner = CliRunner()
        with (
            mock.patch.object(cli, "run_command") as run_command,
            mock.patch.object(cli, "ensure_syson_env"),
            mock.patch.object(cli, "wait_for_readiness") as wait_for_readiness,
        ):
            result = runner.invoke(
                cli.main,
                [
                    "--repo-root",
                    str(ROOT),
                    "bootstrap",
                    "--skip-flexo-org",
                    "--skip-status",
                    "--timeout",
                    "45",
                ],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(run_command.call_count, 3)
        self.assertIn("init", run_command.call_args_list[0].args[0])
        self.assertIn("up", run_command.call_args_list[1].args[0])
        self.assertIn("deploy/syson/docker-compose.yml", run_command.call_args_list[2].args[0])
        wait_for_readiness.assert_called_once()
        self.assertEqual(wait_for_readiness.call_args.args[1], 45)

    def test_first_model_preflight_failure_stops_before_creating_projects(self) -> None:
        runner = CliRunner()
        with (
            mock.patch.object(
                cli,
                "wait_for_readiness",
                side_effect=cli.click.ClickException("Service readiness failed after 1s: Flexo unavailable"),
            ),
            mock.patch.object(cli, "create_flexo_project") as create_flexo_project,
        ):
            result = runner.invoke(
                cli.main,
                [
                    "--repo-root",
                    str(ROOT),
                    "first-model",
                    "Demo",
                    "--output-dir",
                    "/tmp/mbse-lab-demo",
                    "--timeout",
                    "1",
                ],
            )

        self.assertNotEqual(result.exit_code, 0, result.output)
        self.assertIn("Service readiness failed", result.output)
        create_flexo_project.assert_not_called()

    def test_smoke_first_use_dry_run_prints_planned_workflow_without_docker(self) -> None:
        runner = CliRunner()
        with mock.patch.object(cli, "run_command") as run_command:
            result = runner.invoke(
                cli.main,
                [
                    "--repo-root",
                    str(ROOT),
                    "smoke",
                    "first-use",
                    "--dry-run",
                    "--output-dir",
                    "/tmp/mbse-lab-smoke",
                    "--report-dir",
                    "/tmp/mbse-lab-report",
                ],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("dry-run: start Flexo services", result.output)
        self.assertIn("dry-run: create Flexo project `First Use Smoke Model`", result.output)
        self.assertIn("dry-run: write lab report to /tmp/mbse-lab-report/index.md", result.output)
        run_command.assert_not_called()

    def test_smoke_first_use_dry_run_json_outputs_plan(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            [
                "--repo-root",
                str(ROOT),
                "smoke",
                "first-use",
                "Demo Smoke",
                "--dry-run",
                "--json-output",
                "--output-dir",
                "/tmp/mbse-lab-smoke",
                "--report-dir",
                "/tmp/mbse-lab-report",
            ],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        summary = json.loads(result.output)
        self.assertEqual(summary["status"], "dry-run")
        self.assertEqual(summary["model"]["model_name"], "Demo Smoke")
        self.assertEqual(summary["report_path"], "/tmp/mbse-lab-report/index.md")
        self.assertIn("planned_steps", summary)

    def test_smoke_first_use_live_outputs_json_summary(self) -> None:
        runner = CliRunner()
        model_summary = {
            "flexo_project_id": "flexo-1",
            "flexo_commit_id": "commit-1",
            "package_id": "package-1",
            "package_name": "Demo Smoke",
            "export_path": "/tmp/mbse-lab-smoke/flexo/flexo-1.json",
            "sysml_path": "/tmp/mbse-lab-smoke/sysml/flexo-1.sysml",
            "syson_project_id": "syson-1",
            "syson_project_name": "Demo Smoke Review",
            "syson_commit_id": "syson-commit-1",
            "namespace_id": "namespace-1",
            "editing_context_id": "editing-context-1",
            "import_result": {"__typename": "SuccessPayload", "id": "import-1"},
            "syson_url": "http://localhost:18090",
        }
        with (
            mock.patch.object(cli, "run_command") as run_command,
            mock.patch.object(cli, "wait_for_readiness") as wait_for_readiness,
            mock.patch.object(cli, "create_first_model_summary", return_value=model_summary) as create_model,
            mock.patch.object(cli, "report_data", return_value={"doctor": {}, "status": {}}),
            mock.patch.object(cli, "write_report") as write_report,
        ):
            result = runner.invoke(
                cli.main,
                [
                    "--repo-root",
                    str(ROOT),
                    "smoke",
                    "first-use",
                    "Demo Smoke",
                    "--json-output",
                    "--output-dir",
                    "/tmp/mbse-lab-smoke",
                    "--report-dir",
                    "/tmp/mbse-lab-report",
                ],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        summary = json.loads(result.output)
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["model"]["flexo_project_id"], "flexo-1")
        self.assertEqual(summary["model"]["syson_project_id"], "syson-1")
        self.assertEqual(summary["report_path"], "/tmp/mbse-lab-report/index.md")
        self.assertEqual(run_command.call_count, 3)
        wait_for_readiness.assert_called_once()
        create_model.assert_called_once()
        write_report.assert_called_once()

    def test_services_down_dry_run_stops_syson_before_flexo(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.main, ["--repo-root", str(ROOT), "services", "down", "--dry-run"])

        self.assertEqual(result.exit_code, 0, result.output)
        syson_index = result.output.index("dry-run: docker compose -f deploy/syson/docker-compose.yml down")
        flexo_index = result.output.index("dry-run: python3 scripts/flexo_mms_env.py down")
        self.assertLess(syson_index, flexo_index)

    def test_services_restart_can_target_syson_only(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.main, ["--repo-root", str(ROOT), "services", "restart", "--no-flexo", "--dry-run"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("dry-run: docker compose -f deploy/syson/docker-compose.yml down", result.output)
        self.assertIn("dry-run: docker compose -f deploy/syson/docker-compose.yml up -d", result.output)
        self.assertNotIn("scripts/flexo_mms_env.py", result.output)

    def test_services_logs_dry_run_supports_tail(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.main, ["--repo-root", str(ROOT), "services", "logs", "--tail", "25", "--dry-run"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("dry-run: python3 scripts/flexo_mms_env.py logs --tail 25", result.output)
        self.assertIn("dry-run: docker compose -f deploy/syson/docker-compose.yml logs --tail 25 app", result.output)

    def test_services_logs_dry_run_supports_follow_and_service_filters(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            [
                "--repo-root",
                str(ROOT),
                "services",
                "logs",
                "--tail",
                "10",
                "--follow",
                "--flexo-service",
                "auth",
                "--syson-service",
                "database",
                "--dry-run",
            ],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("dry-run: python3 scripts/flexo_mms_env.py logs --tail 10 --follow auth", result.output)
        self.assertIn(
            "dry-run: docker compose -f deploy/syson/docker-compose.yml logs --tail 10 --follow database",
            result.output,
        )

    def test_services_down_can_pass_flexo_volumes_flag(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            ["--repo-root", str(ROOT), "services", "down", "--no-syson", "--volumes", "--dry-run"],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("dry-run: python3 scripts/flexo_mms_env.py down --volumes", result.output)

    def test_diagnostics_exposes_script_options(self) -> None:
        runner = CliRunner()
        with mock.patch.object(cli, "run_command") as run_command:
            result = runner.invoke(
                cli.main,
                [
                    "--repo-root",
                    str(ROOT),
                    "diagnostics",
                    "--public-safe",
                    "--output",
                    "diagnostics/demo",
                    "--timeout",
                    "31",
                    "--log-tail",
                    "7",
                ],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        run_command.assert_called_once_with(
            [
                "python3",
                "scripts/collect_diagnostics.py",
                "--public-safe",
                "--output",
                "diagnostics/demo",
                "--timeout",
                "31",
                "--log-tail",
                "7",
            ],
            ROOT,
        )

    def test_flexo_admin_wrappers_build_script_commands(self) -> None:
        runner = CliRunner()
        cases = [
            (
                ["flexo", "init-org", "--org-id", "demo", "--title", "Demo", "--dry-run"],
                "dry-run: python3 scripts/flexo_syson_bridge.py init-flexo-org",
            ),
            (["flexo", "token", "--username", "user02", "--dry-run"], "python3 scripts/flexo_mms_env.py token"),
            (["flexo", "backup", "--no-update-init", "--dry-run"], "python3 scripts/flexo_mms_env.py backup"),
            (["flexo", "restore", "backup.nq", "--dry-run"], "python3 scripts/flexo_mms_env.py restore backup.nq"),
            (["flexo", "rotate-secrets", "--dry-run"], "python3 scripts/flexo_mms_env.py rotate-secrets"),
        ]
        for args, expected in cases:
            with self.subTest(args=args):
                result = runner.invoke(cli.main, ["--repo-root", str(ROOT), *args])

                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn(expected, result.output)

    def test_services_requires_at_least_one_service_family(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            ["--repo-root", str(ROOT), "services", "up", "--no-flexo", "--no-syson", "--dry-run"],
        )

        self.assertNotEqual(result.exit_code, 0, result.output)
        self.assertIn("Select at least one service family.", result.output)

    def test_deployment_verify_can_target_compose_project(self) -> None:
        runner = CliRunner()
        with mock.patch.object(cli, "run_command") as run_command:
            result = runner.invoke(
                cli.main,
                [
                    "--repo-root",
                    str(ROOT),
                    "deployment",
                    "verify",
                    "--project-name",
                    "mbse-lab-test",
                    "--timeout",
                    "12",
                    "--json-output",
                    "--output",
                    "tmp/report.json",
                ],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        run_command.assert_called_once_with(
            [
                "python3",
                "scripts/flexo_syson_bridge.py",
                "deployment-verify",
                "--timeout",
                "12",
                "--project-name",
                "mbse-lab-test",
                "--json",
                "--output",
                "tmp/report.json",
            ],
            ROOT,
        )

    def test_deployment_isolated_smoke_dry_run_builds_command(self) -> None:
        runner = CliRunner()
        with mock.patch.object(cli, "run_command") as run_command:
            result = runner.invoke(
                cli.main,
                [
                    "--repo-root",
                    str(ROOT),
                    "deployment",
                    "isolated-smoke",
                    "--project-name",
                    "mbse-lab-test",
                    "--runtime-dir",
                    "tmp/isolated",
                    "--timeout",
                    "30",
                    "--output",
                    "tmp/report.json",
                    "--keep",
                    "--dry-run",
                ],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        run_command.assert_called_once_with(
            [
                "python3",
                "scripts/flexo_syson_bridge.py",
                "deployment-isolated-smoke",
                "--timeout",
                "30",
                "--project-name",
                "mbse-lab-test",
                "--runtime-dir",
                "tmp/isolated",
                "--output",
                "tmp/report.json",
                "--keep",
                "--dry-run",
            ],
            ROOT,
        )

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
            env.write_text("SYSON_POSTGRES_PASSWORD=pass" "word\n", encoding="utf-8")  # fmt: skip
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

    def test_share_check_flags_ignored_generated_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            repo.mkdir()
            cli.run_capture(["git", "init", "-b", "main"], repo)
            cli.run_capture(["git", "config", "user.email", "test@example.invalid"], repo)
            cli.run_capture(["git", "config", "user.name", "Test User"], repo)
            (repo / ".gitignore").write_text("exports/**\n", encoding="utf-8")
            export = repo / "exports" / "sysml" / "private.sysml"
            export.parent.mkdir(parents=True)
            export.write_text("package PrivateModel;\n", encoding="utf-8")

            issues = cli.scan_share_issues(repo)

            self.assertIn("untracked generated export: exports/sysml/private.sysml", issues)

    def test_share_check_flags_tracked_generated_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            repo.mkdir()
            cli.run_capture(["git", "init", "-b", "main"], repo)
            cli.run_capture(["git", "config", "user.email", "test@example.invalid"], repo)
            cli.run_capture(["git", "config", "user.name", "Test User"], repo)
            export = repo / "exports" / "flexo" / "private.json"
            export.parent.mkdir(parents=True)
            export.write_text("{}", encoding="utf-8")
            cli.run_capture(["git", "add", "-f", "exports/flexo/private.json"], repo)

            issues = cli.scan_share_issues(repo)

            self.assertIn("tracked publish-blocked path: exports/flexo/private.json", issues)

    def test_share_check_flags_tracked_model_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            repo.mkdir()
            cli.run_capture(["git", "init", "-b", "main"], repo)
            cli.run_capture(["git", "config", "user.email", "test@example.invalid"], repo)
            cli.run_capture(["git", "config", "user.name", "Test User"], repo)
            model = repo / "docs" / "private.sysml"
            model.parent.mkdir(parents=True)
            model.write_text("package PrivateModel;\n", encoding="utf-8")
            cli.run_capture(["git", "add", "docs/private.sysml"], repo)

            issues = cli.scan_share_issues(repo)

            self.assertIn("tracked model artifact outside curated allowlist: docs/private.sysml", issues)

    def test_share_check_flags_dirty_flexo_startup_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            repo.mkdir()
            cli.run_capture(["git", "init", "-b", "main"], repo)
            cli.run_capture(["git", "config", "user.email", "test@example.invalid"], repo)
            cli.run_capture(["git", "config", "user.name", "Test User"], repo)
            cluster = repo / "deploy" / "flexo-mms" / "mount" / "cluster.trig"
            cluster.parent.mkdir(parents=True)
            cluster.write_text("# synthetic seed\n", encoding="utf-8")
            cli.run_capture(["git", "add", "deploy/flexo-mms/mount/cluster.trig"], repo)
            cli.run_capture(["git", "commit", "-m", "seed"], repo)
            cluster.write_text("# private live state\n", encoding="utf-8")

            issues = cli.scan_share_issues(repo)

            self.assertIn("dirty Flexo startup dataset: deploy/flexo-mms/mount/cluster.trig", issues)


class SysonPasswordTests(unittest.TestCase):
    """Tests for issue #10: Generate random SysON Postgres password during init/bootstrap."""

    def test_ensure_syson_env_generates_random_password_not_placeholder(self) -> None:
        from mbse_lab.workspace import SYSON_POSTGRES_PASSWORD_PLACEHOLDER, ensure_syson_env

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            example = repo / "deploy/syson/.env.example"
            example.parent.mkdir(parents=True)
            # Write a minimal .env.example using the real placeholder text so ensure_syson_env
            # replaces it with a generated value.
            example.write_text(
                "SYSON_POSTGRES_IMAGE=postgres:15\n"
                "SYSON_POSTGRES_DB=postgres\n"
                "SYSON_POSTGRES_USER=username\n"
                "SYSON_POSTGRES_PASSWORD=change-me\n",
                encoding="utf-8",
            )

            ensure_syson_env(repo)

            env_path = repo / "deploy/syson/.env"
            self.assertTrue(env_path.exists())
            env_content = env_path.read_text(encoding="utf-8")
            self.assertNotIn(SYSON_POSTGRES_PASSWORD_PLACEHOLDER, env_content)
            self.assertIn("SYSON_POSTGRES_PASSWORD=", env_content)

    def test_ensure_syson_env_preserves_existing_env(self) -> None:
        from mbse_lab.workspace import ensure_syson_env

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            env_path = repo / "deploy/syson/.env"
            env_path.parent.mkdir(parents=True)
            env_path.write_text("SYSON_POSTGRES_PASSWORD=my-custom-password\n", encoding="utf-8")

            ensure_syson_env(repo)

            self.assertEqual(env_path.read_text(encoding="utf-8"), "SYSON_POSTGRES_PASSWORD=my-custom-password\n")

    def test_doctor_flags_placeholder_password(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            env_path = repo / "deploy/syson/.env"
            env_path.parent.mkdir(parents=True)
            env_path.write_text("SYSON_POSTGRES_PASSWORD=change-me\n", encoding="utf-8")

            with mock.patch.object(health, "has_persisted_data", return_value=True):
                report = health.syson_database_credential_report(repo)

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "placeholder-password")
        self.assertIn("placeholder", report["detail"])

    def test_doctor_report_includes_syson_password_placeholder_remediation_code(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            env_path = repo / "deploy/syson/.env"
            env_path.parent.mkdir(parents=True)
            env_path.write_text("SYSON_POSTGRES_PASSWORD=change-me\n", encoding="utf-8")

            with (
                mock.patch.object(health, "has_persisted_data", return_value=True),
                mock.patch.object(health, "command_exists", return_value=True),
                mock.patch.object(health, "tcp_connects", return_value=False),
                mock.patch.object(health, "fetch_status", return_value=None),
                mock.patch("subprocess.run", return_value=mock.Mock(returncode=0)),
            ):
                report = health.doctor_report(repo)

        self.assertIn("SYSON_PASSWORD_PLACEHOLDER", report["remediation_codes"])


class WorkspacePreflightTests(unittest.TestCase):
    """Tests for issue #11: Private workspace preflight for generated artifacts."""

    def test_warn_when_workspace_unset_and_no_explicit_output(self) -> None:
        self.assertTrue(cli.should_warn_repo_local_exports(None, allow_repo_exports=False))

    def test_no_warn_when_explicit_output_given(self) -> None:
        self.assertFalse(cli.should_warn_repo_local_exports(Path("/some/output"), allow_repo_exports=False))

    def test_no_warn_when_allow_repo_exports_set(self) -> None:
        self.assertFalse(cli.should_warn_repo_local_exports(None, allow_repo_exports=True))

    def test_no_warn_when_workspace_env_is_set(self) -> None:
        with mock.patch.dict(os.environ, {"MBSE_MODEL_WORKSPACE": "/some/workspace"}):
            self.assertFalse(cli.should_warn_repo_local_exports(None, allow_repo_exports=False))

    def test_first_model_dry_run_no_warning_with_allow_repo_exports(self) -> None:
        runner = CliRunner()
        with mock.patch.dict(os.environ, {"MBSE_MODEL_WORKSPACE": ""}):
            result = runner.invoke(
                cli.main,
                ["--repo-root", str(ROOT), "first-model", "Demo", "--dry-run", "--allow-repo-exports"],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn("warning: MBSE_MODEL_WORKSPACE is unset", result.output)

    def test_flexo_export_warns_when_workspace_unset(self) -> None:
        runner = CliRunner()
        with mock.patch.dict(os.environ, {"MBSE_MODEL_WORKSPACE": ""}):
            result = runner.invoke(
                cli.main,
                ["--repo-root", str(ROOT), "flexo", "export", "proj-1", "--dry-run"],
            )

        self.assertIn("warning: MBSE_MODEL_WORKSPACE is unset", result.output)

    def test_flexo_export_no_warning_with_allow_repo_exports(self) -> None:
        runner = CliRunner()
        with mock.patch.dict(os.environ, {"MBSE_MODEL_WORKSPACE": ""}):
            result = runner.invoke(
                cli.main,
                ["--repo-root", str(ROOT), "flexo", "export", "proj-1", "--dry-run", "--allow-repo-exports"],
            )

        self.assertNotIn("warning: MBSE_MODEL_WORKSPACE is unset", result.output)

    def test_bridge_render_warns_when_workspace_unset(self) -> None:
        runner = CliRunner()
        with mock.patch.dict(os.environ, {"MBSE_MODEL_WORKSPACE": ""}):
            result = runner.invoke(
                cli.main,
                ["--repo-root", str(ROOT), "bridge", "render", "export.json", "--dry-run"],
            )

        self.assertIn("warning: MBSE_MODEL_WORKSPACE is unset", result.output)

    def test_bridge_run_no_warning_with_explicit_output_dir(self) -> None:
        runner = CliRunner()
        with mock.patch.dict(os.environ, {"MBSE_MODEL_WORKSPACE": ""}):
            result = runner.invoke(
                cli.main,
                [
                    "--repo-root",
                    str(ROOT),
                    "bridge",
                    "run",
                    "flexo-proj",
                    "--syson-project-id",
                    "syson-proj",
                    "--namespace-id",
                    "ns-1",
                    "--output-dir",
                    "/tmp/explicit-output",
                    "--dry-run",
                ],
            )

        self.assertNotIn("warning: MBSE_MODEL_WORKSPACE is unset", result.output)


class DoctorRemediationCodesTests(unittest.TestCase):
    """Tests for issue #14: Remediation codes and grouped next steps in doctor."""

    def test_doctor_report_includes_remediation_codes_key(self) -> None:
        with (
            mock.patch.object(health, "command_exists", return_value=True),
            mock.patch.object(health, "tcp_connects", return_value=False),
            mock.patch.object(health, "fetch_status", return_value=None),
            mock.patch("subprocess.run", return_value=mock.Mock(returncode=0)),
        ):
            report = health.doctor_report(None)

        self.assertIn("remediation_codes", report)
        self.assertIsInstance(report["remediation_codes"], list)

    def test_doctor_report_includes_repo_root_missing_code(self) -> None:
        with (
            mock.patch.object(health, "command_exists", return_value=True),
            mock.patch.object(health, "tcp_connects", return_value=False),
            mock.patch.object(health, "fetch_status", return_value=None),
            mock.patch("subprocess.run", return_value=mock.Mock(returncode=0)),
        ):
            report = health.doctor_report(None)

        self.assertIn("REPO_ROOT_MISSING", report["remediation_codes"])

    def test_doctor_report_includes_workspace_unset_code(self) -> None:
        with (
            mock.patch.object(health, "command_exists", return_value=True),
            mock.patch.object(health, "tcp_connects", return_value=False),
            mock.patch.object(health, "fetch_status", return_value=None),
            mock.patch.dict(os.environ, {"MBSE_MODEL_WORKSPACE": ""}),
            mock.patch("subprocess.run", return_value=mock.Mock(returncode=0)),
        ):
            report = health.doctor_report(None)

        self.assertIn("WORKSPACE_UNSET", report["remediation_codes"])

    def test_doctor_json_output_includes_remediation_codes(self) -> None:
        runner = CliRunner()
        mock_report = {
            "status": "passed",
            "checks": {
                "repo_root": {"ok": True, "path": str(ROOT)},
                "markers": [],
            },
            "remediation_codes": ["WORKSPACE_UNSET"],
        }
        with mock.patch.object(cli, "doctor_report", return_value=mock_report):
            result = runner.invoke(cli.main, ["--repo-root", str(ROOT), "doctor", "--json-output"])

        self.assertEqual(result.exit_code, 0, result.output)
        report = json.loads(result.output)
        self.assertIn("remediation_codes", report)
        self.assertIn("WORKSPACE_UNSET", report["remediation_codes"])

    def test_doctor_text_output_has_grouped_sections(self) -> None:
        runner = CliRunner()
        with (
            mock.patch.object(cli, "command_exists", return_value=True),
            mock.patch.object(cli, "tcp_connects", return_value=False),
            mock.patch.object(cli, "fetch_status", return_value=None),
            mock.patch.object(cli.subprocess, "run", return_value=mock.Mock(returncode=0)),
            mock.patch.object(
                cli,
                "doctor_report",
                return_value={
                    "status": "passed",
                    "checks": {"syson_database_credentials": {"ok": True, "detail": "skipped", "status": "skipped"}},
                    "remediation_codes": [],
                },
            ),
        ):
            result = runner.invoke(cli.main, ["--repo-root", str(ROOT), "doctor"])

        self.assertIn("--- Prerequisites ---", result.output)
        self.assertIn("--- Repo Setup ---", result.output)
        self.assertIn("--- Workspace ---", result.output)
        self.assertIn("--- Services ---", result.output)


class DocsCheckMbseLabCommandsTests(unittest.TestCase):
    """Tests for issue #12: docs-check validates mbse-lab command snippets."""

    def test_valid_mbse_lab_commands_in_docs_pass(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("check_docs", ROOT / "scripts" / "check_docs.py")
        check_docs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(check_docs)

        failures: list[str] = []
        check_docs.check_mbse_lab_commands(failures)
        self.assertEqual(failures, [], f"Unexpected failures: {failures}")

    def test_stale_mbse_lab_command_fails_docs_check(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("check_docs", ROOT / "scripts" / "check_docs.py")
        check_docs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(check_docs)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", dir=ROOT / "docs", delete=False, encoding="utf-8"
        ) as tmp_doc:
            tmp_doc.write("# Test\n\n```bash\nmbse-lab nonexistent-command-xyz\n```\n")
            tmp_path = Path(tmp_doc.name)

        try:
            with mock.patch.object(check_docs, "tracked_and_untracked_docs", return_value=[tmp_path]):
                failures: list[str] = []
                check_docs.check_mbse_lab_commands(failures)

            self.assertTrue(
                any("nonexistent-command-xyz" in f for f in failures),
                f"Expected failure for stale command, got: {failures}",
            )
        finally:
            tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
