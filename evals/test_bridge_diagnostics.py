from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import collect_diagnostics  # noqa: E402


class DiagnosticsManifestTests(unittest.TestCase):
    def test_manifest_summarizes_bundle_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.write_json(
                output / "metadata.json",
                {
                    "created_at": "2026-04-30T00:00:00+00:00",
                    "cwd": "/tmp/mbse",
                    "timeout": 10,
                    "log_tail": 120,
                },
            )
            self.write_json(
                output / "commands" / "index.json",
                [
                    {"command": ["ok"], "returncode": 0, "file": "commands/ok.txt"},
                    {"command": ["failed"], "returncode": 1, "file": "commands/failed.txt"},
                    {"command": ["missing"], "returncode": None, "file": "commands/missing.txt"},
                ],
            )
            self.write_json(
                output / "http" / "index.json",
                {
                    "flexo-projects.json": {
                        "url": "http://localhost:18083/projects",
                        "status": 200,
                    }
                },
            )
            self.write_json(
                output / "deployment-verification.json",
                {
                    "status": "failed",
                    "checkedAt": "2026-04-30T00:00:01+00:00",
                    "summary": {
                        "services": 9,
                        "passedServices": 8,
                        "failedServices": 1,
                        "checks": 19,
                        "passedChecks": 18,
                        "failedChecks": 1,
                    },
                },
            )

            manifest = collect_diagnostics.build_manifest(output)

        self.assertEqual("failed", manifest["deploymentVerification"]["status"])
        self.assertEqual(3, manifest["commands"]["total"])
        self.assertEqual(1, len(manifest["commands"]["failed"]))
        self.assertEqual(1, len(manifest["commands"]["timedOutOrMissing"]))
        self.assertEqual(200, manifest["http"]["flexo-projects.json"]["status"])
        self.assertEqual("deployment-verification.json", manifest["artifacts"]["deploymentVerification"])

    def test_manifest_markdown_prioritizes_status_and_entry_points(self) -> None:
        manifest = {
            "metadata": {
                "created_at": "2026-04-30T00:00:00+00:00",
                "cwd": "/tmp/mbse",
            },
            "artifacts": {
                "deploymentVerification": "deployment-verification.json",
                "commandIndex": "commands/index.json",
                "httpIndex": "http/index.json",
                "files": "files/",
            },
            "commands": {
                "total": 3,
                "failed": [{"command": ["failed"]}],
                "timedOutOrMissing": [{"command": ["missing"]}],
            },
            "deploymentVerification": {
                "status": "passed",
                "summary": {
                    "services": 9,
                    "passedServices": 9,
                    "failedServices": 0,
                    "checks": 19,
                    "passedChecks": 19,
                    "failedChecks": 0,
                },
            },
            "http": {
                "syson-root.html.json": {
                    "url": "http://localhost:18090/",
                    "status": 200,
                }
            },
        }

        rendered = collect_diagnostics.render_manifest_markdown(manifest)

        self.assertIn("# Diagnostics Bundle", rendered)
        self.assertIn("- Deployment verification: `passed`", rendered)
        self.assertIn("- Deployment checks: 19 passed, 0 failed, 19 total", rendered)
        self.assertIn("- Commands captured: 3 total, 1 failed, 1 timed out or missing", rendered)
        self.assertIn("- Deployment evidence: `deployment-verification.json`", rendered)
        self.assertIn("`syson-root.html.json`: status `200`", rendered)

    def test_collect_manifest_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.write_json(output / "metadata.json", {"created_at": "now", "cwd": "/tmp/mbse"})
            self.write_json(output / "commands" / "index.json", [])
            self.write_json(output / "http" / "index.json", {})
            self.write_json(output / "deployment-verification.json", {"status": "passed", "summary": {}})

            collect_diagnostics.collect_manifest(output)

            self.assertTrue((output / "manifest.json").exists())
            self.assertTrue((output / "index.md").exists())
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            rendered = (output / "index.md").read_text(encoding="utf-8")

        self.assertEqual("passed", manifest["deploymentVerification"]["status"])
        self.assertIn("# Diagnostics Bundle", rendered)

    def test_public_safe_command_set_omits_project_lists_and_logs(self) -> None:
        commands = collect_diagnostics.diagnostic_commands(log_tail=25, public_safe=True)
        rendered = "\n".join(" ".join(command) for command in commands)

        self.assertNotIn("git status --short", rendered)
        self.assertNotIn("flexo-list-projects", rendered)
        self.assertNotIn("syson-list-projects", rendered)
        self.assertNotIn(" logs ", rendered)
        self.assertIn("scripts/flexo_mms_env.py status --with-sysmlv2", rendered)

    def test_public_safe_http_endpoints_omit_project_lists(self) -> None:
        endpoints = collect_diagnostics.diagnostic_http_endpoints(public_safe=True)

        self.assertNotIn("flexo-projects.json", endpoints)
        self.assertNotIn("syson-rest-projects.json", endpoints)
        self.assertIn("syson-root.html.json", endpoints)

    def test_collect_commands_marks_public_safe_omissions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with mock.patch.object(
                collect_diagnostics,
                "run",
                return_value={"returncode": 0, "stdout": "", "stderr": ""},
            ):
                collect_diagnostics.collect_commands(output, Path(directory), 10, 25, public_safe=True)

            index = json.loads((output / "commands" / "index.json").read_text(encoding="utf-8"))

        self.assertTrue(any(item.get("omitted") for item in index if isinstance(item, dict)))

    def write_json(self, path: Path, data: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
