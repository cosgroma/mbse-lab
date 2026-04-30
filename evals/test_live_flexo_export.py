from __future__ import annotations

import os
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import flexo_syson_bridge  # noqa: E402


class LiveFlexoExportTests(unittest.TestCase):
    def setUp(self) -> None:
        if os.environ.get("MBSE_LIVE_EVAL") != "1":
            self.skipTest("set MBSE_LIVE_EVAL=1 or run `make live-eval` to enable live Flexo evals")
        self.flexo_url = os.environ.get("FLEXO_URL", flexo_syson_bridge.DEFAULT_FLEXO_URL).rstrip("/")
        self.timeout = int(os.environ.get("FLEXO_EVAL_TIMEOUT", "30"))
        self.project_id: str | None = None

    def tearDown(self) -> None:
        if not self.project_id:
            return
        flexo_syson_bridge.request(
            "DELETE",
            f"{self.flexo_url}/projects/{self.project_id}",
            timeout=self.timeout,
        )

    def test_disposable_flexo_project_exports_and_renders(self) -> None:
        package_id = str(uuid.uuid4())
        package_name = "Live Flexo Package"
        project = self.create_project()
        self.project_id = project["@id"]

        commit = self.commit_package(self.project_id, package_id, package_name)
        snapshot = flexo_syson_bridge.export_flexo_project(
            self.flexo_url,
            self.project_id,
            commit["@id"],
            self.timeout,
        )
        rendered = flexo_syson_bridge.render_snapshot(snapshot)

        self.assertEqual(snapshot["project"]["@id"], self.project_id)
        self.assertIn({"@type": "Package", "@id": package_id, "declaredName": package_name}, snapshot["roots"])
        self.assertIn("package Live_Flexo_Package;", rendered)

    def create_project(self) -> dict[str, object]:
        return flexo_syson_bridge.request_json(
            "POST",
            f"{self.flexo_url}/projects",
            {
                "@type": "Project",
                "name": f"Live Flexo Eval {uuid.uuid4()}",
                "description": "Disposable project created by make live-eval",
            },
            timeout=self.timeout,
            expected={200, 201},
        )

    def commit_package(self, project_id: str, package_id: str, package_name: str) -> dict[str, object]:
        return flexo_syson_bridge.request_json(
            "POST",
            f"{self.flexo_url}/projects/{project_id}/commits",
            {
                "@type": "Commit",
                "description": "Create disposable package for live export eval",
                "change": [
                    {
                        "@type": "DataVersion",
                        "identity": None,
                        "payload": {
                            "@id": package_id,
                            "@type": "Package",
                            "declaredName": package_name,
                        },
                    }
                ],
            },
            timeout=self.timeout,
            expected={200, 201},
        )


if __name__ == "__main__":
    unittest.main()
