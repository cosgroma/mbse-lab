from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


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

        services = {
            element["containerName"]: element
            for element in snapshot["elements"]
            if element.get("@type") == "PartUsage" and element.get("containerName")
        }

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


if __name__ == "__main__":
    unittest.main()
