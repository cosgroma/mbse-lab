from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "WORKFLOW.md"
LIVE_SMOKE_WORKFLOW = ROOT / ".github" / "workflows" / "live-smoke.yml"


class WorkflowContractTests(unittest.TestCase):
    def test_workflow_contract_has_front_matter(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        _, front_matter, body = text.split("---", 2)

        self.assertIn("workflow:", front_matter)
        self.assertIn("tracker:", front_matter)
        self.assertIn("workspace:", front_matter)
        self.assertIn("validation:", front_matter)
        self.assertIn("observability:", front_matter)
        self.assertIn("trust:", front_matter)
        self.assertIn("commit_after_chunk: true", front_matter)
        self.assertIn("trusted-local-lab", front_matter)
        self.assertIn("# MBSE Local Lab Workflow", body)

    def test_workflow_contract_names_required_commands(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        for command in (
            "make workflow-check",
            "make check",
            "make docs-check",
            "make docs-build",
            "make docs-serve",
            "make eval",
            "make live-eval",
            "make deployment-contract",
            "make deployment-verify",
            "make diagnostics",
            "make backup",
            "hatch run lint:all",
        ):
            with self.subTest(command=command):
                self.assertIn(command, text)

    def test_workflow_contract_states_handoff_and_safety_policy(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("explicit user intent", text)
        self.assertIn("Unrelated working-tree changes are left untouched", text)
        self.assertIn("committed with a focused message", text)
        self.assertIn("recommended next chunk", text)
        self.assertIn("Runtime secrets and local service data are intentionally ignored", text)
        self.assertIn("docs/plans/active/", text)
        self.assertIn("docs/plans/completed/", text)
        self.assertIn("GitHub CI workflow runs pre-commit", text)
        self.assertIn("documentation is organized for MkDocs", text)

    def test_live_smoke_workflow_is_manual_and_uploads_failure_diagnostics(self) -> None:
        text = LIVE_SMOKE_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", text)
        self.assertIn("mbse-lab services up", text)
        self.assertIn("mbse-lab smoke first-use --json-output", text)
        self.assertIn("make live-eval", text)
        self.assertIn("mbse-lab diagnostics --public-safe", text)
        self.assertIn("actions/upload-artifact", text)


if __name__ == "__main__":
    unittest.main()
