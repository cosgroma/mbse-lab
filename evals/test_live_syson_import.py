from __future__ import annotations

import json
import os
import sys
import time
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mbse_lab.bridge import workflow as flexo_syson_bridge  # noqa: E402


class LiveSysonImportTests(unittest.TestCase):
    def setUp(self) -> None:
        if os.environ.get("MBSE_LIVE_EVAL") != "1":
            self.skipTest("set MBSE_LIVE_EVAL=1 or run `make live-eval` to enable live SysON evals")
        self.syson_url = os.environ.get("SYSON_URL", flexo_syson_bridge.DEFAULT_SYSON_URL)
        self.timeout = int(os.environ.get("SYSON_EVAL_TIMEOUT", "30"))
        self.project_id: str | None = None

    def tearDown(self) -> None:
        if not self.project_id:
            return
        flexo_syson_bridge.request(
            "DELETE",
            f"{self.syson_url.rstrip('/')}/api/rest/projects/{self.project_id}",
            timeout=self.timeout,
        )

    def test_rendered_fixture_imports_into_disposable_syson_project(self) -> None:
        snapshot = json.loads((ROOT / "evals" / "fixtures" / "flexo-basic-package.json").read_text(encoding="utf-8"))
        textual_sysml = flexo_syson_bridge.render_snapshot(snapshot)

        project = self.create_project()
        self.project_id = project["id"]
        editing_context_id = project["currentEditingContext"]["id"]
        commit_id = self.latest_commit_id(self.project_id)
        namespace_id = self.root_package_id(self.project_id, commit_id)

        self.import_text(editing_context_id, namespace_id, textual_sysml)

        imported = self.wait_for_element(self.project_id, commit_id, "Vehicle_Model")
        self.assertEqual(imported["@type"], "Package")

    def create_project(self) -> dict[str, object]:
        mutation = """
        mutation CreateProject($input: CreateProjectInput!) {
          createProject(input: $input) {
            __typename
            ... on CreateProjectSuccessPayload {
              project { id name currentEditingContext { id } }
            }
            ... on ErrorPayload { message }
          }
        }
        """
        response = flexo_syson_bridge.graphql(
            self.syson_url,
            mutation,
            {
                "input": {
                    "id": str(uuid.uuid4()),
                    "name": f"Live Bridge Eval {uuid.uuid4()}",
                    "templateId": "sysmlv2-template",
                    "libraryIds": [],
                }
            },
            timeout=self.timeout,
        )
        result = response["data"]["createProject"]
        if result["__typename"] == "ErrorPayload":
            self.fail(result["message"])
        return result["project"]

    def latest_commit_id(self, project_id: str) -> str:
        commits = flexo_syson_bridge.request_json(
            "GET",
            f"{self.syson_url.rstrip('/')}/api/rest/projects/{project_id}/commits",
            timeout=self.timeout,
        )
        self.assertTrue(commits, "SysON project should expose at least one REST commit")
        return commits[-1]["@id"]

    def root_package_id(self, project_id: str, commit_id: str) -> str:
        roots = flexo_syson_bridge.request_json(
            "GET",
            f"{self.syson_url.rstrip('/')}/api/rest/projects/{project_id}/commits/{commit_id}/roots",
            timeout=self.timeout,
        )
        for root in roots:
            if root.get("@type") == "Package":
                return root["@id"]
        self.fail(f"no root Package found in SysON project {project_id}")

    def import_text(self, editing_context_id: str, namespace_id: str, textual_sysml: str) -> None:
        mutation = """
        mutation InsertTextualSysMLv2($input: InsertTextualSysMLv2Input!) {
          insertTextualSysMLv2(input: $input) {
            __typename
            ... on SuccessPayload { id }
            ... on ErrorPayload { message }
          }
        }
        """
        response = flexo_syson_bridge.graphql(
            self.syson_url,
            mutation,
            {
                "input": {
                    "id": str(uuid.uuid4()),
                    "editingContextId": editing_context_id,
                    "objectId": namespace_id,
                    "textualContent": textual_sysml,
                }
            },
            timeout=self.timeout,
        )
        result = response["data"]["insertTextualSysMLv2"]
        if result["__typename"] == "ErrorPayload":
            self.fail(result["message"])

    def wait_for_element(self, project_id: str, commit_id: str, name: str) -> dict[str, object]:
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            elements = flexo_syson_bridge.request_json(
                "GET",
                f"{self.syson_url.rstrip('/')}/api/rest/projects/{project_id}/commits/{commit_id}/elements",
                timeout=self.timeout,
            )
            for element in elements:
                if (element.get("declaredName") or element.get("name")) == name:
                    return element
            time.sleep(0.5)
        self.fail(f"did not find imported element `{name}` in SysON project {project_id}")


if __name__ == "__main__":
    unittest.main()
