from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mbse_lab.bridge import contracts as bridge_contracts  # noqa: E402
from mbse_lab.bridge import render as bridge_render  # noqa: E402
from mbse_lab.bridge import workflow as flexo_syson_bridge  # noqa: E402
from mbse_lab.deployment import verify as deployment_verify  # noqa: E402


class BridgeRenderTests(unittest.TestCase):
    def test_compatibility_script_remains_callable(self) -> None:
        result = subprocess.run(
            ["python3", "scripts/flexo_syson_bridge.py", "--help"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("flexo-to-syson", result.stdout)

    def test_fixture_renders_deterministic_sysml_subset(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "flexo-basic-package.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        rendered = bridge_render.render_snapshot(snapshot)

        self.assertEqual(
            rendered,
            "\n".join(
                [
                    "// Generated from a Flexo SysML v2 REST export.",
                    "// Project: Fixture Project",
                    "// Commit: commit-1",
                    "",
                    "package Vehicle_Model {",
                    "  part def Transceiver {",
                    "    port rf_in;",
                    "    attribute gain_dB;",
                    "  }",
                    "  requirement def Link_Budget_Requirement;",
                    "}",
                    "",
                ]
            ),
        )

    def test_syson_roots_resolves_latest_commit_before_fetching_roots(self) -> None:
        calls: list[tuple[str, str]] = []

        def fake_request_json(method: str, url: str, **_kwargs: object) -> object:
            calls.append((method, url))
            if url.endswith("/api/rest/projects/project%201/commits"):
                return [{"@id": "commit-old"}, {"@id": "commit latest"}]
            if url.endswith("/api/rest/projects/project%201/commits/commit%20latest/roots"):
                return [{"@id": "root-1", "@type": "Package", "declaredName": "Root"}]
            self.fail(f"unexpected request: {method} {url}")

        args = argparse.Namespace(project_id="project 1", syson_url="http://syson.local/", timeout=10, json=True)

        with (
            mock.patch.object(flexo_syson_bridge, "request_json", side_effect=fake_request_json),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            flexo_syson_bridge.cmd_syson_roots(args)

        self.assertEqual(
            calls,
            [
                ("GET", "http://syson.local/api/rest/projects/project%201/commits"),
                ("GET", "http://syson.local/api/rest/projects/project%201/commits/commit%20latest/roots"),
            ],
        )

    def test_render_warns_when_defaulting_to_repo_local_exports(self) -> None:
        snapshot = {
            "project": {"@id": "project-1", "name": "Demo"},
            "commit": {"@id": "commit-1"},
            "roots": [{"@id": "root-1", "@type": "Package", "declaredName": "Demo"}],
            "elements": [{"@id": "root-1", "@type": "Package", "declaredName": "Demo"}],
        }
        args = argparse.Namespace(input=Path("snapshot.json"), output=None)

        with tempfile.TemporaryDirectory() as directory:
            cwd = Path.cwd()
            os.chdir(directory)
            try:
                args.input.write_text(json.dumps(snapshot), encoding="utf-8")
                with mock.patch.dict(os.environ, {"MBSE_MODEL_WORKSPACE": ""}):
                    stderr = io.StringIO()
                    with contextlib.redirect_stderr(stderr):
                        flexo_syson_bridge.cmd_render_sysml(args)
            finally:
                os.chdir(cwd)

        self.assertIn("warning: MBSE_MODEL_WORKSPACE is unset", stderr.getvalue())
        self.assertIn("repo-local `exports`", stderr.getvalue())

    def test_unsupported_elements_are_not_rendered(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "flexo-basic-package.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        rendered = bridge_render.render_snapshot(snapshot)

        self.assertNotIn("OwningMembership", rendered)
        self.assertNotIn("NotRendered", rendered)

    def test_render_report_counts_rendered_and_unsupported_types(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "flexo-basic-package.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        _rendered, report = bridge_render.render_snapshot_with_report(snapshot)

        self.assertEqual(report["summary"]["total_elements"], 6)
        self.assertEqual(report["summary"]["rendered_elements"], 5)
        self.assertEqual(report["summary"]["skipped_elements"], 0)
        self.assertEqual(report["summary"]["unsupported_elements"], 1)
        self.assertEqual(report["types"]["Package"], {"total": 1, "rendered": 1, "skipped": 0, "unsupported": 0})
        self.assertEqual(
            report["types"]["OwningMembership"], {"total": 1, "rendered": 0, "skipped": 0, "unsupported": 1}
        )
        self.assertIn("unsupported Flexo @type `OwningMembership`: 1 element(s)", report["warnings"])

    def test_all_fixture_render_reports_are_deterministic(self) -> None:
        for fixture in sorted((ROOT / "evals" / "fixtures").glob("*.json")):
            with self.subTest(fixture=fixture.name):
                snapshot = json.loads(fixture.read_text(encoding="utf-8"))

                _first_text, first_report = bridge_render.render_snapshot_with_report(snapshot)
                _second_text, second_report = bridge_render.render_snapshot_with_report(snapshot)

                self.assertEqual(first_report, second_report)
                total = len([element for element in snapshot.get("elements", []) if isinstance(element, dict)])
                summary = first_report["summary"]
                self.assertEqual(summary["total_elements"], total)
                self.assertEqual(
                    summary["total_elements"],
                    summary["rendered_elements"] + summary["skipped_elements"] + summary["unsupported_elements"],
                )

    def test_render_sysml_report_option_writes_json_report(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "flexo-basic-package.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "model.sysml"
            report_output = Path(temp_dir) / "render-report.json"
            args = argparse.Namespace(input=fixture, output=output, report=True, report_output=report_output)

            flexo_syson_bridge.cmd_render_sysml(args)

            report = json.loads(report_output.read_text(encoding="utf-8"))

            self.assertTrue(output.exists())
            self.assertEqual(report["schema"], "mbse-lab.render-report.v1")
            self.assertEqual(report["summary"]["unsupported_elements"], 1)

    def test_bridge_run_writes_render_report_artifact_and_run_log_reference(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "flexo-basic-package.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "exports"
            run_log = Path(temp_dir) / "run.json"
            args = argparse.Namespace(
                flexo_project_id="project-1",
                commit_id=None,
                syson_project_id="syson-project-1",
                namespace_id="namespace-1",
                editing_context_id=None,
                output_dir=output_dir,
                run_log=run_log,
                run_log_dir=Path(temp_dir) / "runs",
                flexo_url="http://flexo.local",
                syson_url="http://syson.local",
                timeout=10,
            )

            with (
                mock.patch.object(flexo_syson_bridge, "export_flexo_project", return_value=snapshot),
                mock.patch.object(
                    flexo_syson_bridge,
                    "import_sysml_text",
                    return_value={"editing_context_id": "ctx-1", "result": {"status": "ok"}},
                ),
            ):
                flexo_syson_bridge.cmd_flexo_to_syson(args)

            record = json.loads(run_log.read_text(encoding="utf-8"))
            render_report = Path(record["artifacts"]["render_report"])

            self.assertTrue(render_report.exists())
            self.assertEqual(record["steps"][2]["details"]["coverage_summary"]["unsupported_elements"], 1)
            self.assertEqual(json.loads(render_report.read_text(encoding="utf-8"))["summary"]["rendered_elements"], 5)

    def test_bridge_run_can_create_syson_project_and_emit_json_summary(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "flexo-basic-package.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "exports"
            run_log = Path(temp_dir) / "run.json"
            args = argparse.Namespace(
                flexo_project_id="project-1",
                commit_id=None,
                syson_project_id=None,
                namespace_id=None,
                create_syson_project="Imported From Flexo",
                editing_context_id=None,
                output_dir=output_dir,
                run_log=run_log,
                run_log_dir=Path(temp_dir) / "runs",
                flexo_url="http://flexo.local",
                syson_url="http://syson.local",
                timeout=10,
                json_output=True,
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with (
                mock.patch.object(flexo_syson_bridge, "export_flexo_project", return_value=snapshot),
                mock.patch.object(
                    flexo_syson_bridge,
                    "create_syson_project",
                    return_value={
                        "id": "syson-project-1",
                        "name": "Imported From Flexo",
                        "currentEditingContext": {"id": "ctx-1"},
                    },
                ),
                mock.patch.object(flexo_syson_bridge, "syson_latest_commit_id", return_value="syson-commit-1"),
                mock.patch.object(flexo_syson_bridge, "syson_root_package_id", return_value="namespace-1"),
                mock.patch.object(
                    flexo_syson_bridge,
                    "import_sysml_text",
                    return_value={"editing_context_id": "ctx-1", "result": {"status": "ok"}},
                ),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                flexo_syson_bridge.cmd_flexo_to_syson(args)

            summary = json.loads(stdout.getvalue())
            record = json.loads(run_log.read_text(encoding="utf-8"))

        self.assertEqual(summary["syson_project_id"], "syson-project-1")
        self.assertEqual(summary["namespace_id"], "namespace-1")
        self.assertEqual(summary["artifacts"]["render_report"], record["artifacts"]["render_report"])
        self.assertIn("Created SysON project: syson-project-1", stderr.getvalue())
        self.assertIn("discover-syson-root", [step["name"] for step in record["steps"]])

    def test_coverage_matrix_matches_renderer_registry(self) -> None:
        doc = (ROOT / "docs" / "lab" / "modeling-conventions.md").read_text(encoding="utf-8")
        matrix_types = set()
        for line in doc.splitlines():
            if not line.startswith("| `"):
                continue
            matrix_types.add(line.split("|", 2)[1].strip().strip("`"))

        self.assertEqual(matrix_types, bridge_render.RENDERABLE_TYPES)

    def test_render_rejects_malformed_snapshot_contract(self) -> None:
        with self.assertRaisesRegex(ValueError, "project"):
            bridge_render.render_snapshot(
                {
                    "commit": {"@id": "commit-1"},
                    "roots": [],
                    "elements": [],
                }
            )

    def test_rf_link_budget_fixture_renders_spec_backbone(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "rf-link-budget-basic.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        rendered = bridge_render.render_snapshot(snapshot)

        self.assertEqual(
            rendered,
            "\n".join(
                [
                    "// Generated from a Flexo SysML v2 REST export.",
                    "// Project: RF Link Budget Fixture",
                    "// Commit: rf-commit-1",
                    "",
                    "package RF_Link_Budget_Model {",
                    "  package Definitions {",
                    "    part def RFLink {",
                    "      attribute frequency_MHz;",
                    "      attribute range_km;",
                    "      attribute linkMargin_dB;",
                    "      part transmitter;",
                    "      part txAntenna;",
                    "      part channel;",
                    "      part rxAntenna;",
                    "      part receiver;",
                    "      part modem;",
                    "    }",
                    "  }",
                    "  package Link_Performance_Requirements {",
                    "    requirement def MinimumLinkMargin;",
                    "  }",
                    "  package RF_Link_Architecture {",
                    "    part uhfDownlink;",
                    "  }",
                    "}",
                    "",
                ]
            ),
        )

    def test_mbse_lab_tool_system_curated_snapshot_matches_fixture_render(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "mbse-lab-tool-system.json"
        snapshot_path = ROOT / "exports" / "examples" / "sysml" / "mbse-lab-tool-system.public.sysml"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        rendered, report = bridge_render.render_snapshot_with_report(snapshot)

        self.assertEqual(rendered, snapshot_path.read_text(encoding="utf-8"))
        self.assertEqual(
            report["summary"],
            {
                "total_elements": 39,
                "rendered_elements": 39,
                "skipped_elements": 0,
                "unsupported_elements": 0,
                "types": 6,
                "unsupported_types": 0,
            },
        )
        self.assertEqual(report["warnings"], [])

    def test_container_deployment_fixture_renders_spec_backbone(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "container-deployment-basic.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        rendered = bridge_render.render_snapshot(snapshot)

        self.assertEqual(
            rendered,
            "\n".join(
                [
                    "// Generated from a Flexo SysML v2 REST export.",
                    "// Project: Container Deployment Fixture",
                    "// Commit: deployment-commit-1",
                    "",
                    "package Container_Deployment_Model {",
                    "  package Definitions {",
                    "    part def DeploymentEnvironment;",
                    "    part def DockerComposeStack;",
                    "    part def ContainerService;",
                    "    part def VolumeMount;",
                    "    part def ApiProbe;",
                    "  }",
                    "  package Deployment_Requirements {",
                    "    requirement def ApiReachabilityRequired;",
                    "    requirement def VolumePersistenceRequired;",
                    "    requirement def BackupReadinessRequired;",
                    "  }",
                    "  package Deployment_Architecture {",
                    "    part def MBSELocalLabDeployment {",
                    "      part flexoMmsStack;",
                    "      part sysonStack;",
                    "    }",
                    "  }",
                    "}",
                    "",
                ]
            ),
        )

    def test_container_deployment_fixture_models_runtime_contract(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "container-deployment-basic.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        contract = bridge_contracts.deployment_contract_from_snapshot(snapshot)
        services = {service["containerName"]: service for service in contract["services"]}

        self.assertEqual(9, contract["serviceCount"])
        self.assertEqual(
            {
                "auth-service",
                "flexo-sysmlv2",
                "layer1-service",
                "minio-server",
                "openldap-server",
                "quad-server",
                "store-service",
                "syson-app",
                "syson-database",
            },
            set(services),
        )
        self.assertEqual("FLEXO_MMS_SYSMLV2_HOST_PORT", services["flexo-sysmlv2"]["ports"][0]["hostPortEnv"])
        self.assertEqual(18083, services["flexo-sysmlv2"]["ports"][0]["defaultHostPort"])
        self.assertEqual("/data", services["minio-server"]["mounts"][0]["containerPath"])
        self.assertEqual("deploy/syson/data/postgres", services["syson-database"]["mounts"][0]["hostPath"])
        self.assertEqual("syson", services["syson-app"]["stackName"])

    def test_deployment_contract_rejects_malformed_required_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "serviceCount"):
            bridge_contracts.DeploymentContract.from_mapping(
                {
                    "project": {"name": "Fixture"},
                    "commit": {"@id": "commit-1"},
                    "serviceCount": 2,
                    "services": [{"containerName": "demo-container"}],
                }
            )

    def test_deployment_contract_table_is_inspectable(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "container-deployment-basic.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        contract = bridge_contracts.deployment_contract_from_snapshot(snapshot)
        rendered = bridge_contracts.format_deployment_contract_table(contract)

        self.assertIn("CONTAINER", rendered)
        self.assertIn("flexo-sysmlv2", rendered)
        self.assertIn("${FLEXO_MMS_SYSMLV2_HOST_PORT:-18083}->8080/tcp", rendered)
        self.assertIn("deploy/syson/data/postgres->/var/lib/postgresql/data", rendered)

    def test_deployment_verification_report_uses_contract_data(self) -> None:
        contract = {
            "project": {"name": "Fixture"},
            "commit": {"@id": "commit-1"},
            "services": [
                {
                    "id": "service-1",
                    "declaredName": "demo",
                    "stackName": "demo-stack",
                    "serviceName": "demo-service",
                    "containerName": "demo-container",
                    "ports": [
                        {
                            "containerPort": 8080,
                            "defaultHostPort": 18080,
                            "hostPortEnv": "DEMO_HOST_PORT",
                            "protocol": "tcp",
                        }
                    ],
                    "mounts": [
                        {
                            "containerPath": "/data",
                            "hostPath": "deploy/demo/data",
                            "type": "bind",
                        }
                    ],
                }
            ],
        }
        container = {
            "State": {"Running": True, "Status": "running"},
            "NetworkSettings": {"Ports": {"8080/tcp": [{"HostPort": "18080"}]}},
            "Mounts": [
                {
                    "Destination": "/data",
                    "Source": str(ROOT / "deploy" / "demo" / "data"),
                    "Type": "bind",
                }
            ],
        }

        with mock.patch.object(flexo_syson_bridge, "inspect_docker_container", return_value=(container, None)):
            report = flexo_syson_bridge.verify_deployment_contract(contract, {}, ROOT)

        self.assertEqual("passed", report["status"])
        self.assertEqual(3, report["summary"]["passedChecks"])
        self.assertIn("PASSED demo-container", flexo_syson_bridge.format_deployment_verification_report(report))

    def test_deployment_verification_report_rejects_malformed_checks(self) -> None:
        with self.assertRaisesRegex(ValueError, "checks"):
            deployment_verify.DeploymentVerificationReport.from_mapping(
                {
                    "status": "passed",
                    "checkedAt": "2026-05-01T00:00:00Z",
                    "project": {},
                    "commit": {},
                    "composeProject": None,
                    "summary": {},
                    "services": [
                        {
                            "containerName": "demo-container",
                            "status": "passed",
                        }
                    ],
                }
            )

    def test_deployment_verification_can_inspect_compose_project_services(self) -> None:
        contract = {
            "project": {"name": "Fixture"},
            "commit": {"@id": "commit-1"},
            "services": [
                {
                    "id": "service-1",
                    "declaredName": "demo",
                    "stackName": "demo-stack",
                    "serviceName": "demo-service",
                    "containerName": "demo-container",
                    "ports": [],
                    "mounts": [],
                }
            ],
        }
        container = {
            "Name": "/mbse-lab-demo-service-1",
            "State": {"Running": True, "Status": "running"},
            "NetworkSettings": {"Ports": {}},
            "Mounts": [],
        }

        with mock.patch.object(
            flexo_syson_bridge, "inspect_compose_service", return_value=(container, None)
        ) as inspect:
            report = flexo_syson_bridge.verify_deployment_contract(
                contract,
                {},
                ROOT,
                project_name="mbse-lab-test",
            )

        inspect.assert_called_once_with("mbse-lab-test", "demo-service", 20)
        self.assertEqual("passed", report["status"])
        self.assertEqual("mbse-lab-test", report["composeProject"])
        running_check = report["services"][0]["checks"][0]
        self.assertEqual("mbse-lab-demo-service-1", running_check["details"]["actualContainerName"])

    def test_deployment_mount_verification_supports_isolated_data_dirs(self) -> None:
        container = {
            "Mounts": [
                {
                    "Destination": "/data",
                    "Source": "/tmp/isolated/flexo/minio",
                    "Type": "bind",
                }
            ]
        }
        expected = {
            "containerName": "minio-server",
            "mounts": [
                {
                    "containerPath": "/data",
                    "hostPath": "deploy/flexo-mms/data/minio",
                    "type": "bind",
                }
            ],
        }

        checks = deployment_verify.verify_deployment_mounts(
            container,
            expected,
            ROOT,
            {"FLEXO_MMS_DATA_DIR": "/tmp/isolated/flexo"},
        )

        self.assertEqual("passed", checks[0]["status"])
        self.assertEqual("/tmp/isolated/flexo/minio", checks[0]["details"]["expectedHostPath"])


if __name__ == "__main__":
    unittest.main()
