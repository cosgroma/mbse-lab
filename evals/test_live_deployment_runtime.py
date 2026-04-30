from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "evals" / "fixtures" / "container-deployment-basic.json"


class LiveDeploymentRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        if os.environ.get("MBSE_LIVE_EVAL") != "1":
            self.skipTest("set MBSE_LIVE_EVAL=1 or run `make live-eval` to enable live deployment evals")
        self.env = self.load_compose_env()
        self.snapshot = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_container_deployment_fixture_names_runtime_stacks(self) -> None:
        names = {
            element.get("declaredName")
            for element in self.snapshot["elements"]
            if isinstance(element.get("declaredName"), str)
        }

        self.assertIn("flexoMmsStack", names)
        self.assertIn("sysonStack", names)

    def test_running_containers_match_compose_runtime_contract(self) -> None:
        expectations = self.container_expectations_from_fixture()
        self.assertEqual(9, len(expectations), "deployment fixture should model the expected local lab containers")

        for expected in expectations:
            with self.subTest(container=expected["containerName"]):
                container = self.inspect_container(expected["containerName"])
                state = container.get("State", {})
                self.assertTrue(
                    state.get("Running"),
                    f"{expected['containerName']} is not running: {state.get('Status')}",
                )
                self.assert_expected_ports(container, expected)
                self.assert_expected_mounts(container, expected)

    def assert_expected_ports(self, container: dict[str, Any], expected: dict[str, Any]) -> None:
        published_ports = container.get("NetworkSettings", {}).get("Ports") or {}
        for port in expected.get("ports", []):
            protocol = port.get("protocol", "tcp")
            container_port = f"{port['containerPort']}/{protocol}"
            bindings = published_ports.get(container_port) or []
            host_ports = {binding.get("HostPort") for binding in bindings}
            expected_host_port = self.env.get(port["hostPortEnv"], str(port["defaultHostPort"]))
            self.assertIn(
                expected_host_port,
                host_ports,
                f"{expected['containerName']} should publish {container_port} on host port {expected_host_port}; "
                f"found {sorted(host_ports)}",
            )

    def assert_expected_mounts(self, container: dict[str, Any], expected: dict[str, Any]) -> None:
        mounts = container.get("Mounts") or []
        by_destination = {mount.get("Destination"): mount for mount in mounts}
        for mount in expected.get("mounts", []):
            actual = by_destination.get(mount["containerPath"])
            self.assertIsNotNone(actual, f"{expected['containerName']} should mount {mount['containerPath']}")
            self.assertEqual(mount.get("type", "bind"), actual.get("Type"))
            self.assertEqual(os.path.abspath(ROOT / mount["hostPath"]), actual.get("Source"))

    def container_expectations_from_fixture(self) -> list[dict[str, Any]]:
        expectations = [
            element
            for element in self.snapshot["elements"]
            if element.get("@type") == "PartUsage" and element.get("containerName")
        ]
        expectations.sort(key=lambda element: element["containerName"])
        for element in expectations:
            self.assertIsInstance(element.get("serviceName"), str)
            self.assertIsInstance(element.get("containerName"), str)
            for port in element.get("ports", []):
                self.assertIsInstance(port.get("containerPort"), int)
                self.assertIsInstance(port.get("defaultHostPort"), int)
                self.assertIsInstance(port.get("hostPortEnv"), str)
                self.assertIsInstance(port.get("protocol", "tcp"), str)
            for mount in element.get("mounts", []):
                self.assertIsInstance(mount.get("containerPath"), str)
                self.assertIsInstance(mount.get("hostPath"), str)
                self.assertIsInstance(mount.get("type", "bind"), str)
        return expectations

    def inspect_container(self, name: str) -> dict[str, Any]:
        try:
            result = subprocess.run(
                ["docker", "inspect", name],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except FileNotFoundError:
            self.fail("docker CLI is required for live deployment evals")
        except subprocess.TimeoutExpired:
            self.fail(f"docker inspect timed out for container {name}")

        if result.returncode != 0:
            self.fail(f"docker inspect failed for {name}: {result.stderr.strip()}")

        inspected = json.loads(result.stdout)
        self.assertEqual(1, len(inspected), f"docker inspect should return exactly one object for {name}")
        return inspected[0]

    def load_compose_env(self) -> dict[str, str]:
        env: dict[str, str] = {}
        for path in (
            ROOT / "deploy" / "flexo-mms" / ".env.example",
            ROOT / "deploy" / "flexo-mms" / ".env",
            ROOT / "deploy" / "syson" / ".env.example",
            ROOT / "deploy" / "syson" / ".env",
        ):
            env.update(self.read_env_file(path))

        for key in (
            "FLEXO_MMS_FUSEKI_HOST_PORT",
            "FLEXO_MMS_MINIO_HOST_PORT",
            "FLEXO_MMS_AUTH_HOST_PORT",
            "FLEXO_MMS_STORE_HOST_PORT",
            "FLEXO_MMS_LAYER1_HOST_PORT",
            "FLEXO_MMS_SYSMLV2_HOST_PORT",
            "SYSON_HOST_PORT",
        ):
            if key in os.environ:
                env[key] = os.environ[key]
        return env

    def read_env_file(self, path: Path) -> dict[str, str]:
        if not path.exists():
            return {}

        values: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
        return values


if __name__ == "__main__":
    unittest.main()
