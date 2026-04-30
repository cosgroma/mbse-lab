from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import flexo_syson_bridge  # noqa: E402


class BridgeRunLogTests(unittest.TestCase):
    def test_run_log_path_is_workflow_scoped(self) -> None:
        path = flexo_syson_bridge.run_log_path(Path("runs"), "flexo-to-syson", "run-123")

        self.assertEqual(path, Path("runs") / "flexo-to-syson" / "run-123.json")

    def test_write_run_log_creates_pretty_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "run.json"
            flexo_syson_bridge.write_run_log(
                path,
                {
                    "run_id": "run-123",
                    "workflow": "flexo-to-syson",
                    "status": "succeeded",
                },
            )

            loaded = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(loaded["run_id"], "run-123")
        self.assertEqual(loaded["workflow"], "flexo-to-syson")
        self.assertEqual(loaded["status"], "succeeded")
