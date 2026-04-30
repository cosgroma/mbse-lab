from __future__ import annotations

import json
import os
import subprocess
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class PortExpectation:
    container_port: str
    env_name: str
    default_host_port: str


@dataclass(frozen=True)
class MountExpectation:
    source: Path
    destination: str


@dataclass(frozen=True)
class ContainerExpectation:
    name: str
    ports: tuple[PortExpectation, ...] = ()
    mounts: tuple[MountExpectation, ...] = ()


EXPECTED_CONTAINERS = (
    ContainerExpectation("openldap-server"),
    ContainerExpectation(
        "quad-server",
        ports=(PortExpectation("3030/tcp", "FLEXO_MMS_FUSEKI_HOST_PORT", "3030"),),
        mounts=(MountExpectation(ROOT / "deploy" / "flexo-mms" / "mount", "/tmp/mount"),),
    ),
    ContainerExpectation(
        "minio-server",
        ports=(PortExpectation("9000/tcp", "FLEXO_MMS_MINIO_HOST_PORT", "9000"),),
        mounts=(MountExpectation(ROOT / "deploy" / "flexo-mms" / "data" / "minio", "/data"),),
    ),
    ContainerExpectation(
        "auth-service",
        ports=(PortExpectation("8080/tcp", "FLEXO_MMS_AUTH_HOST_PORT", "8082"),),
    ),
    ContainerExpectation(
        "store-service",
        ports=(PortExpectation("8080/tcp", "FLEXO_MMS_STORE_HOST_PORT", "8081"),),
    ),
    ContainerExpectation(
        "layer1-service",
        ports=(PortExpectation("8080/tcp", "FLEXO_MMS_LAYER1_HOST_PORT", "18080"),),
    ),
    ContainerExpectation(
        "flexo-sysmlv2",
        ports=(PortExpectation("8080/tcp", "FLEXO_MMS_SYSMLV2_HOST_PORT", "18083"),),
    ),
    ContainerExpectation(
        "syson-database",
        mounts=(MountExpectation(ROOT / "deploy" / "syson" / "data" / "postgres", "/var/lib/postgresql/data"),),
    ),
    ContainerExpectation(
        "syson-app",
        ports=(PortExpectation("8080/tcp", "SYSON_HOST_PORT", "18090"),),
    ),
)


class LiveDeploymentRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        if os.environ.get("MBSE_LIVE_EVAL") != "1":
            self.skipTest("set MBSE_LIVE_EVAL=1 or run `make live-eval` to enable live deployment evals")
        self.env = self.load_compose_env()

    def test_container_deployment_fixture_names_runtime_stacks(self) -> None:
        snapshot = json.loads(
            (ROOT / "evals" / "fixtures" / "container-deployment-basic.json").read_text(encoding="utf-8")
        )
        names = {
            element.get("declaredName")
            for element in snapshot["elements"]
            if isinstance(element.get("declaredName"), str)
        }

        self.assertIn("flexoMmsStack", names)
        self.assertIn("sysonStack", names)

    def test_running_containers_match_compose_runtime_contract(self) -> None:
        for expected in EXPECTED_CONTAINERS:
            with self.subTest(container=expected.name):
                container = self.inspect_container(expected.name)
                state = container.get("State", {})
                self.assertTrue(state.get("Running"), f"{expected.name} is not running: {state.get('Status')}")
                self.assert_expected_ports(container, expected)
                self.assert_expected_mounts(container, expected)

    def assert_expected_ports(self, container: dict[str, Any], expected: ContainerExpectation) -> None:
        published_ports = container.get("NetworkSettings", {}).get("Ports") or {}
        for port in expected.ports:
            bindings = published_ports.get(port.container_port) or []
            host_ports = {binding.get("HostPort") for binding in bindings}
            expected_host_port = self.env.get(port.env_name, port.default_host_port)
            self.assertIn(
                expected_host_port,
                host_ports,
                f"{expected.name} should publish {port.container_port} on host port {expected_host_port}; "
                f"found {sorted(host_ports)}",
            )

    def assert_expected_mounts(self, container: dict[str, Any], expected: ContainerExpectation) -> None:
        mounts = container.get("Mounts") or []
        by_destination = {mount.get("Destination"): mount for mount in mounts}
        for mount in expected.mounts:
            actual = by_destination.get(mount.destination)
            self.assertIsNotNone(actual, f"{expected.name} should mount {mount.destination}")
            self.assertEqual("bind", actual.get("Type"))
            self.assertEqual(os.path.abspath(mount.source), actual.get("Source"))

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
