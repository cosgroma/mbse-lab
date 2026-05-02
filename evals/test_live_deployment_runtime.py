from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys_path = str(ROOT / "src")
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from mbse_lab.bridge import workflow as flexo_syson_bridge  # noqa: E402

FIXTURE = ROOT / "evals" / "fixtures" / "container-deployment-basic.json"


class LiveDeploymentRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        if os.environ.get("MBSE_LIVE_EVAL") != "1":
            self.skipTest("set MBSE_LIVE_EVAL=1 or run `make live-eval` to enable live deployment evals")
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
        contract = flexo_syson_bridge.deployment_contract_from_snapshot(self.snapshot)
        self.assertEqual(
            9, contract["serviceCount"], "deployment fixture should model the expected local lab containers"
        )

        report = flexo_syson_bridge.verify_deployment_contract(
            contract,
            flexo_syson_bridge.load_deployment_env(ROOT),
            ROOT,
        )
        self.assertEqual("passed", report["status"], flexo_syson_bridge.format_deployment_verification_report(report))


if __name__ == "__main__":
    unittest.main()
