from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import flexo_syson_bridge  # noqa: E402


class BridgeRenderTests(unittest.TestCase):
    def test_fixture_renders_deterministic_sysml_subset(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "flexo-basic-package.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        rendered = flexo_syson_bridge.render_snapshot(snapshot)

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

        with mock.patch.object(flexo_syson_bridge, "request_json", side_effect=fake_request_json):
            with contextlib.redirect_stdout(io.StringIO()):
                flexo_syson_bridge.cmd_syson_roots(args)

        self.assertEqual(
            calls,
            [
                ("GET", "http://syson.local/api/rest/projects/project%201/commits"),
                ("GET", "http://syson.local/api/rest/projects/project%201/commits/commit%20latest/roots"),
            ],
        )

    def test_unsupported_elements_are_not_rendered(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "flexo-basic-package.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        rendered = flexo_syson_bridge.render_snapshot(snapshot)

        self.assertNotIn("OwningMembership", rendered)
        self.assertNotIn("NotRendered", rendered)

    def test_rf_link_budget_fixture_renders_spec_backbone(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "rf-link-budget-basic.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        rendered = flexo_syson_bridge.render_snapshot(snapshot)

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

    def test_container_deployment_fixture_renders_spec_backbone(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "container-deployment-basic.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        rendered = flexo_syson_bridge.render_snapshot(snapshot)

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

        contract = flexo_syson_bridge.deployment_contract_from_snapshot(snapshot)
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

    def test_deployment_contract_table_is_inspectable(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "container-deployment-basic.json"
        snapshot = json.loads(fixture.read_text(encoding="utf-8"))

        contract = flexo_syson_bridge.deployment_contract_from_snapshot(snapshot)
        rendered = flexo_syson_bridge.format_deployment_contract_table(contract)

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


if __name__ == "__main__":
    unittest.main()
